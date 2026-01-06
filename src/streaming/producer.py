import time
import random
import json
import yaml
import pandas as pd
import redis
from pathlib import Path

from src.streaming.state import is_running

CFG_PATH = Path("configs/streaming.yaml")

def load_cfg():
    with open(CFG_PATH) as f:
        return yaml.safe_load(f)

def get_redis(cfg):
    return redis.Redis(
        host=cfg["redis"]["host"],
        port=cfg["redis"]["port"],
        decode_responses=True
    )

def run_producer():
    cfg = load_cfg()
    r = get_redis(cfg)

    stream = cfg["redis"]["stream_name"]
    csv_path = Path(cfg["producer"]["csv_path"])
    batch_size = cfg["producer"]["batch_size"]
    sleep_s = cfg["producer"]["sleep_seconds"]

    print("🟢 Producer ready — waiting for START")

    while True:
        if not is_running():
            time.sleep(1)
            continue

        print("🚀 Producer started")

        df = pd.read_csv(csv_path)

        for i in range(0, len(df), batch_size):
            if not is_running():
                print("⛔ Producer stopped")
                break

            batch = df.iloc[i:i + batch_size]

            for _, row in batch.iterrows():
                row_dict = row.to_dict()
                
                # MOCK DATA: Generate wider range of random IPs
                # Source: Random 192.168.X.Y
                row_dict['src_ip'] = f"192.168.{random.randint(0, 255)}.{random.randint(2, 254)}"
                
                # Dest: Random 10.X.Y.Z
                row_dict['dst_ip'] = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(2, 254)}"

                r.xadd(
                    stream,
                    {"row": json.dumps(row_dict)}
                )

            time.sleep(sleep_s)

        print("✅ Producer finished CSV")
        time.sleep(2)


if __name__ == "__main__":
    run_producer()
