# src/serve.py

from __future__ import annotations
from typing import Any, Dict, Optional
import io
import json
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

# =========================
# CORS Middleware
# =========================
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    try:
        from mlflow.tracking import MlflowClient
        from src.inference import MODEL_NAME, MODEL_ALIAS
        
        client = MlflowClient()
        mv = client.get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
        run = client.get_run(mv.run_id)
        
        # List artifacts (plots, etc.)
        artifacts = client.list_artifacts(mv.run_id)
        artifact_list = [f.path for f in artifacts] if artifacts else []

        return {
            "model_uri": f"models:/{MODEL_NAME}@{MODEL_ALIAS}",
            "run_id": mv.run_id,
            "version": mv.version,
            "alias": MODEL_ALIAS,
            "status": mv.status,
            "params": run.data.params,
            "metrics": run.data.metrics,
            "artifacts": artifact_list
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "model_uri": "unknown",
            "run_id": "unknown"
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

@app.get("/model-artifact/{filename}")
def get_artifact(filename: str):
    """
    Proxy MLflow artifacts (like PNG plots) to the frontend.
    """
    try:
        from mlflow.tracking import MlflowClient
        import mlflow
        from src.inference import MODEL_NAME, MODEL_ALIAS
        from fastapi.responses import Response

        client = MlflowClient()
        mv = client.get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
        
        # Download artifact to local tmp
        local_path = mlflow.artifacts.download_artifacts(
            run_id=mv.run_id, 
            artifact_path=filename
        )
        
        with open(local_path, "rb") as f:
            content = f.read()
            
        media_type = "image/png" if filename.endswith(".png") else "application/octet-stream"
        return Response(content=content, media_type=media_type)
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/logs")
def get_logs():
    cfg = load_cfg()
    r = get_redis_client(cfg)
    
    # Fetch recent logs (already JSON strings)
    # LIFO: Index 0 is newest
    raw_logs = r.lrange("intrusion:logs", 0, -1)
    
    parsed_logs = []
    for log_str in raw_logs:
        try:
            parsed_logs.append(json.loads(log_str))
        except:
            continue
            
    return {"logs": parsed_logs}
