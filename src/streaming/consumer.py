import json
import time
import yaml
import redis
import pandas as pd
from pathlib import Path
import mlflow
from src.streaming.state import is_running
from src.inference import predict_on_raw_df
from prometheus_client import start_http_server

CFG_PATH = Path("configs/streaming.yaml")


def load_cfg():
    with open(CFG_PATH) as f:
        return yaml.safe_load(f)


def get_redis(cfg):
    return redis.Redis(
        host=cfg["redis"]["host"],   # ✅ must be "redis" in Docker
        port=cfg["redis"]["port"],
        decode_responses=True
    )


def init_consumer_group(r, cfg):
    try:
        r.xgroup_create(
            cfg["redis"]["stream_name"],
            cfg["redis"]["consumer_group"],
            id="0",
            mkstream=True
        )
    except redis.exceptions.ResponseError as e:
        # BUSYGROUP = already exists (normal on restart)
        if "BUSYGROUP" not in str(e):
            raise


def update_stats(r, key, value=1):
    r.hincrby(key, value, 1)


def run_consumer():
    # Start Prometheus metrics server
    start_http_server(8001)

    cfg = load_cfg()
    r = get_redis(cfg)

    stream = cfg["redis"]["stream_name"]
    group = cfg["redis"]["consumer_group"]
    consumer = cfg["redis"]["consumer_name"]
    stats_key = cfg["stats"]["redis_prefix"]

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
            block=cfg["consumer"]["block_ms"]
        )

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

            preds = result["pred_labels"]
            counts = preds.value_counts().to_dict()

            for label, count in counts.items():
                r.hincrby(stats_key, label, count)

            r.hincrby(stats_key, "total_processed", len(df))

            for msg_id in ids:
                r.xack(stream, group, msg_id)

            print(f"🔍 Processed {len(df)} rows")


if __name__ == "__main__":
    run_consumer()
