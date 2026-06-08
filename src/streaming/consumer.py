import json
import os
from datetime import datetime, timezone
import time
import yaml
import redis
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import pandas as pd
from pathlib import Path

from prometheus_client import start_http_server

from src.streaming.state import is_running
from src.inference import predict_on_raw_df
from src.metrics.prometheus_metrics import REDIS_STREAM_LAG

CFG_PATH = Path("configs/streaming.yaml")

# ── S3 configuration (read from environment, same vars as docker-compose) ──
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "mlops-ids-artifacts")
S3_PREFIX = "inference-logs"   # folder inside the bucket


def load_cfg():
    with open(CFG_PATH) as f:
        return yaml.safe_load(f)


def get_redis(cfg):
    return redis.Redis(
        host=cfg["redis"]["host"],
        port=cfg["redis"]["port"],
        decode_responses=True,
    )


def get_s3_client():
    """Return a boto3 S3 client using env credentials (already in container)."""
    return boto3.client(
        "s3",
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )


def upload_batch_to_s3(logs: list) -> None:
    """
    Upload a batch of inference log dicts to S3 as a JSON file.
    S3 path: inference-logs/YYYY-MM-DD/HH-MM-SS-ffffff.json
    Non-fatal — if S3 is unreachable the consumer keeps running.
    """
    if not logs:
        return
    try:
        now      = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S-%f")
        s3_key   = f"{S3_PREFIX}/{date_str}/{time_str}.json"

        payload = json.dumps({
            "batch_timestamp": now.isoformat(),
            "record_count":    len(logs),
            "records":         logs,
        }, indent=2)

        s3 = get_s3_client()
        s3.put_object(
            Bucket      = S3_BUCKET,
            Key         = s3_key,
            Body        = payload.encode("utf-8"),
            ContentType = "application/json",
        )
        print(f"☁️  Saved {len(logs)} records → s3://{S3_BUCKET}/{s3_key}")

    except (BotoCoreError, ClientError, Exception) as exc:
        print(f"⚠️  S3 upload skipped: {exc}")


def init_consumer_group(r, cfg):
    try:
        r.xgroup_create(
            cfg["redis"]["stream_name"],
            cfg["redis"]["consumer_group"],
            id="0",
            mkstream=True,
        )
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise


def run_consumer():
    # Prometheus metrics endpoint
    start_http_server(8001)

    cfg      = load_cfg()
    r        = get_redis(cfg)
    stream   = cfg["redis"]["stream_name"]
    group    = cfg["redis"]["consumer_group"]
    consumer = cfg["redis"]["consumer_name"]

    init_consumer_group(r, cfg)

    print(f"🟢 Consumer ready — logs → Redis + s3://{S3_BUCKET}/{S3_PREFIX}/")

    while True:
        if not is_running():
            time.sleep(1)
            continue

        messages = r.xreadgroup(
            groupname=group,
            consumername=consumer,
            streams={stream: ">"},
            count=cfg["consumer"]["read_count"],
            block=cfg["consumer"]["block_ms"],
        )

        # Redis stream lag metric
        try:
            groups = r.xinfo_groups(stream)
            for g in groups:
                if g["name"] == group:
                    REDIS_STREAM_LAG.set(g.get("lag", 0))
                    break
        except Exception:
            pass

        for _, msgs in messages:
            rows = []
            ids  = []

            for msg_id, payload in msgs:
                rows.append(json.loads(payload["row"]))
                ids.append(msg_id)

            if not rows:
                continue

            df     = pd.DataFrame(rows)
            result = predict_on_raw_df(df)

            # Build log entries (shared by Redis live view + S3 audit trail)
            predictions  = result["pred_labels"].tolist()
            logs_to_push = []

            for idx, pred in enumerate(predictions):
                if idx >= len(rows):
                    break
                row_data  = rows[idx]
                log_entry = {
                    "timestamp":   datetime.now(timezone.utc).isoformat(),
                    "src_ip":      row_data.get("src_ip",     "N/A"),
                    "dst_ip":      row_data.get("dst_ip",     "N/A"),
                    "attack_type": row_data.get("attack_cat", "Unknown"),
                    "prediction":  int(pred),
                    "label":       int(row_data.get("label", -1)),
                }
                logs_to_push.append(log_entry)

            # Push to Redis (live frontend view — last 50 entries)
            if logs_to_push:
                r.lpush("intrusion:logs", *[json.dumps(e) for e in logs_to_push])
                r.ltrim("intrusion:logs", 0, 49)

            # Upload batch to S3 (persistent audit trail)
            upload_batch_to_s3(logs_to_push)

            for msg_id in ids:
                r.xack(stream, group, msg_id)

            print(f"🔍 Processed {len(df)} rows")


if __name__ == "__main__":
    run_consumer()
