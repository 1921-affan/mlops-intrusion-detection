# src/streaming/state.py

import redis
import yaml
from pathlib import Path

CFG_PATH = Path("configs/streaming.yaml")
STATE_KEY = "intrusion:streaming_state"


def _get_redis():
    with open(CFG_PATH) as f:
        cfg = yaml.safe_load(f)

    return redis.Redis(
        host=cfg["redis"]["host"],
        port=cfg["redis"]["port"],
        decode_responses=True
    )


def start():
    """
    Signal ALL services (producer + consumer)
    that streaming should start.
    """
    r = _get_redis()
    r.set(STATE_KEY, "running")


def stop():
    """
    Signal ALL services to stop streaming.
    """
    r = _get_redis()
    r.set(STATE_KEY, "stopped")


def is_running() -> bool:
    """
    Global streaming state check.
    Works across containers.
    """
    r = _get_redis()
    return r.get(STATE_KEY) == "running"
