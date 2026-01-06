import json
from datetime import datetime
import time
import yaml
import redis
import pandas as pd
from pathlib import Path

from prometheus_client import start_http_server

from src.streaming.state import is_running
from src.inference import predict_on_raw_df
from src.metrics.prometheus_metrics import REDIS_STREAM_LAG

CFG_PATH = Path("configs/streaming.yaml")


def load_cfg():
    with open(CFG_PATH) as f:
        return yaml.safe_load(f)


def get_redis(cfg):
    return redis.Redis(
        host=cfg["redis"]["host"],
        port=cfg["redis"]["port"],
        decode_responses=True,
    )


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
    # 🔥 Prometheus metrics endpoint
    start_http_server(8001)

    cfg = load_cfg()
    r = get_redis(cfg)

    stream = cfg["redis"]["stream_name"]
    group = cfg["redis"]["consumer_group"]
    consumer = cfg["redis"]["consumer_name"]

    init_consumer_group(r, cfg)

    print("🟢 Consumer ready — waiting for START")

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

        # 🔥 Redis stream lag (Backlog)
        try:
            groups = r.xinfo_groups(stream)
            for g in groups:
                if g["name"] == group:
                    # 'lag' is available in Redis 6.2+
                    current_lag = g.get("lag", 0)
                    REDIS_STREAM_LAG.set(current_lag)
                    break
        except Exception:
            pass # resilient to redis errors

        for _, msgs in messages:
            rows = []
            ids = []

            for msg_id, payload in msgs:
                rows.append(json.loads(payload["row"]))
                ids.append(msg_id)

            if not rows:
                continue

            df = pd.DataFrame(rows)
            result = predict_on_raw_df(df)
            
            # 📝 LOGGING TO REDIS FOR FRONTEND
            predictions = result["pred_labels"].tolist()
            logs_to_push = []
            
            for idx, pred in enumerate(predictions):
                # Ensure we don't go out of bounds if something dropped rows (unlikely but safe)
                if idx >= len(rows):
                    break
                    
                row_data = rows[idx]
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "src_ip": row_data.get("src_ip", "N/A"),
                    "dst_ip": row_data.get("dst_ip", "N/A"),
                    "attack_type": row_data.get("attack_cat", "Unknown"),
                    "prediction": int(pred),
                    "label": int(row_data.get("label", -1))
                }
                logs_to_push.append(json.dumps(log_entry))

            if logs_to_push:
                # Push all logs (LIFO for "recent" view)
                r.lpush("intrusion:logs", *logs_to_push)
                # Keep only last 50 logs to save memory
                r.ltrim("intrusion:logs", 0, 49)

            for msg_id in ids:
                r.xack(stream, group, msg_id)

            print(f"🔍 Processed {len(df)} rows")


if __name__ == "__main__":
    run_consumer()
