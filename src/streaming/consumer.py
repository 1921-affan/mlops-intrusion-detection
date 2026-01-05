import json
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

        # 🔥 Redis stream lag (authoritative)
        pending_info = r.xpending(stream, group)
        REDIS_STREAM_LAG.set(pending_info["pending"])

        for _, msgs in messages:
            rows = []
            ids = []

            for msg_id, payload in msgs:
                rows.append(json.loads(payload["row"]))
                ids.append(msg_id)

            if not rows:
                continue

            df = pd.DataFrame(rows)
            predict_on_raw_df(df)

            for msg_id in ids:
                r.xack(stream, group, msg_id)

            print(f"🔍 Processed {len(df)} rows")


if __name__ == "__main__":
    run_consumer()
