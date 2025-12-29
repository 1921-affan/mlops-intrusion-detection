# src/serve.py

from __future__ import annotations
from typing import Any, Dict, Optional
import io
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException

import redis
import yaml
from pathlib import Path

from src.inference import predict_on_raw_df, load_model
from src.streaming.state import start, stop, is_running

# =========================
# App & Config
# =========================
app = FastAPI(
    title="UNSW Intrusion Detection – MLOps API",
    description="Batch intrusion detection using MLflow Production model",
    version="1.0.0",
)

CFG_PATH = Path("configs/streaming.yaml")

def load_cfg():
    with open(CFG_PATH) as f:
        return yaml.safe_load(f)

def get_redis_client(cfg):
    return redis.Redis(
        host=cfg["redis"]["host"],
        port=cfg["redis"]["port"],
        decode_responses=True
    )

# =========================
# Control Plane
# =========================
@app.post("/start-detection")
def start_detection():
    if is_running():
        return {"status": "already running"}
    start()
    return {"status": "detection started"}

@app.post("/stop-detection")
def stop_detection():
    stop()
    return {"status": "detection stopped"}

@app.get("/status")
def status():
    return {"running": is_running()}

# =========================
# Health
# =========================
@app.get("/health")
def health_check():
    return {"status": "ok"}

# =========================
# Prediction
# =========================
@app.post("/predict-file")
async def predict_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    try:
        df_raw = pd.read_csv(io.BytesIO(await file.read()))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV read failed: {e}")

    if df_raw.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV is empty")

    result = predict_on_raw_df(df_raw)

    preview = {
        "labels": result["pred_labels"].head(20).tolist()
    }

    if result.get("pred_proba") is not None:
        preview["proba"] = result["pred_proba"].head(20).to_dict(orient="list")

    return {
        "n_rows": len(df_raw),
        "stats": result["stats"],
        "preview": preview,
    }

# =========================
# Model Info
# =========================
@app.get("/model-info")
def model_info():
    model = load_model()
    return {
        "model_uri": model.metadata.model_uri,
        "run_id": model.metadata.run_id,
        "alias": "production",
    }

# =========================
# Reset Stream (Demo Utility)
# =========================
@app.post("/reset-stream")
def reset_stream():
    cfg = load_cfg()
    r = get_redis_client(cfg)

    stream = cfg["redis"]["stream_name"]
    group = cfg["redis"]["consumer_group"]

    stop()  # stop processing first

    r.delete(stream)

    try:
        r.xgroup_create(stream, group, id="0", mkstream=True)
    except redis.exceptions.ResponseError:
        pass  # group already exists (safe)

    return {"status": "stream reset successfully"}
