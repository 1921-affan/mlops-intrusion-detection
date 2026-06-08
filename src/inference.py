from __future__ import annotations

# CI test change for manual approval gate validation
import logging
import time
from pathlib import Path
from typing import Dict, Any, Tuple

import mlflow
import pandas as pd
import yaml
from sklearn.metrics import accuracy_score, classification_report

from src.data.loader import preprocess_data, load_processed_data
from src.cache.redis_cache import (
    get_cached_prediction,
    set_cached_prediction,
)

from src.metrics.prometheus_metrics import (
    INFERENCE_REQUESTS,
    CACHE_HITS,
    INFERENCE_LATENCY,
    PREDICTION_NORMAL,
    PREDICTION_FRAUD,
)

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
logger = logging.getLogger("src.inference")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------
CONFIG_PATH = Path("configs/config.yaml")
MODEL_NAME = "model_top20"
MODEL_ALIAS = "production"

# ⚠️ MUST MATCH TRAINING ORDER EXACTLY
FEATURE_COLUMNS = [
    "sttl",
    "ct_dst_sport_ltm",
    "ct_state_ttl",
    "sbytes",
    "proto_enc",
    "smean",
    "ct_srv_dst",
    "ct_srv_src",
    "sbytes_log",
    "synack",
    "service_enc",
    "dbytes",
    "ct_dst_src_ltm",
    "dload",
    "ct_dst_ltm",
    "dmean",
    "rate",
    "ct_src_ltm",
    "sinpkt",
    "sload",
    "dur",
    "dttl",
    "spkts",
    "sjit",
    "tcprtt",
]

_model = None
_config = None

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def load_config() -> dict:
    global _config
    if _config is None:
        with open(CONFIG_PATH, "r") as f:
            _config = yaml.safe_load(f)
    return _config


def load_model():
    global _model
    if _model is None:
        model_uri = f"models:/{MODEL_NAME}@{MODEL_ALIAS}"
        logger.info("Loading model from MLflow: %s", model_uri)
        _model = mlflow.sklearn.load_model(model_uri)
    return _model


def preprocess_raw_batch(
    raw_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.Series | None]:
    cfg = load_config()
    train_path = cfg["paths"]["train_csv"]

    train_df, _ = load_processed_data(train_path, train_path)

    _, _, X_raw, y_raw, _ = preprocess_data(
        train_df.copy(),
        raw_df.copy(),
    )

    return X_raw, y_raw


# -------------------------------------------------------------------
# Inference (STREAMING + REDIS CACHE + PROMETHEUS)
# -------------------------------------------------------------------
def predict_on_raw_df(raw_df: pd.DataFrame) -> Dict[str, Any]:
    model = load_model()
    logger.info("Starting inference on batch size %d", len(raw_df))

    X_proc, y_true = preprocess_raw_batch(raw_df)

    # Strict column order
    X_top = X_proc[FEATURE_COLUMNS]

    # Convert to NumPy float (prevents dtype bugs)
    X_np = X_top.to_numpy(dtype=float)

    predictions = []

    for row in X_np:
        INFERENCE_REQUESTS.inc()
        start_time = time.time()

        feature_list = row.tolist()
        # DEMO FIX: Round to 4 decimals to ensure cache hits despite float precision
        feature_list = [round(x, 4) for x in feature_list]

        # ✅ CHECK CACHE FIRST
        cached_pred = get_cached_prediction(feature_list)
        if cached_pred is not None:
            CACHE_HITS.inc()
            predictions.append(cached_pred)
            INFERENCE_LATENCY.observe(time.time() - start_time)
            continue

        # ❌ Cache miss → run model
        pred = int(model.predict([row], validate_features=False)[0])
        predictions.append(pred)

        # 🔥 CLASS METRICS
        if pred == 0:
            PREDICTION_NORMAL.inc()
        else:
            PREDICTION_FRAUD.inc()

        # ✅ STORE RESULT IN CACHE
        set_cached_prediction(feature_list, pred)

        INFERENCE_LATENCY.observe(time.time() - start_time)

    pred_series = pd.Series(predictions)

    stats: Dict[str, Any] = {
        "pred_counts": pred_series.value_counts().to_dict()
    }

    if y_true is not None:
        stats["accuracy"] = float(accuracy_score(y_true, predictions))
        stats["classification_report"] = classification_report(
            y_true,
            predictions,
            output_dict=True,
            zero_division=0,
        )

    logger.info("Inference completed successfully")

    return {
        "pred_labels": pred_series,
        "stats": stats,
    }
