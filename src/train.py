import json
import os
from pathlib import Path
import yaml

import pandas as pd
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient
from sklearn.model_selection import train_test_split

# ================= PROJECT IMPORTS =================
from src.data.loader import load_processed_data, preprocess_data
from src.model.utils import (
    create_xgb_model,
    evaluate_model,
    compute_shap_importance,
    select_top_k_features,
)

# ================= CONSTANTS =================
CONFIG_PATH = Path("configs/config.yaml")
MODEL_NAME = "model_top20"
MODEL_ALIAS = "production"
USE_SHAP = True


def main():
    # ---------- CONFIG ----------
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    train_path = config["paths"]["train_csv"]
    test_path = config["paths"]["test_csv"]
    artifacts_dir = Path(config["paths"]["artifacts_dir"])
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # ---------- MLFLOW ----------
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment(config["mlflow"]["experiment_name"])

    # ---------- DATA ----------
    train_df, test_df = load_processed_data(train_path, test_path)

    X_full, y_full, X_test_full, y_test, feature_cols = preprocess_data(
        train_df, test_df
    )

    # 🔒 FORCE STABLE DTYPES (THIS FIXES proto_enc)
    for col in X_full.columns:
        if X_full[col].dtype == "int64":
            X_full[col] = X_full[col].astype("int32")

    X_tr, X_val, y_tr, y_val = train_test_split(
        X_full,
        y_full,
        test_size=0.2,
        random_state=42,
        stratify=y_full,
    )

    # ---------- RUN ----------
    with mlflow.start_run(run_name=config["mlflow"]["run_name"]) as run:

        # ===== BASE MODEL =====
        base_model = create_xgb_model()
        base_model.fit(X_tr, y_tr)

        mlflow.log_metric(
            "train_full_accuracy",
            float(evaluate_model(base_model, X_tr, y_tr, "train_full")),
        )
        mlflow.log_metric(
            "val_full_accuracy",
            float(evaluate_model(base_model, X_val, y_val, "val_full")),
        )

        # ===== SHAP =====
        if USE_SHAP:
            shap_importance = compute_shap_importance(
                base_model,
                X_val.sample(n=5000, random_state=42),
            )

            top_features = select_top_k_features(
                shap_importance,
                k=config["model"]["top_k_features"],
            )

            with open(artifacts_dir / "top_features.json", "w") as f:
                json.dump(top_features, f, indent=2)

            mlflow.log_artifact(str(artifacts_dir / "top_features.json"))
        else:
            with open(artifacts_dir / "top_features.json", "r") as f:
                top_features = json.load(f)

        # ===== TOP-K DATA =====
        X_tr_top = X_tr[top_features].copy()
        X_val_top = X_val[top_features].copy()

        # 🔒 FORCE AGAIN FOR SAFETY
        for col in X_tr_top.columns:
            if X_tr_top[col].dtype == "int64":
                X_tr_top[col] = X_tr_top[col].astype("int32")

        # ===== TOP-K MODEL =====
        model_top = create_xgb_model()
        model_top.fit(X_tr_top, y_tr)

        mlflow.log_metric(
            "train_top_accuracy",
            float(evaluate_model(model_top, X_tr_top, y_tr, "train_top")),
        )
        mlflow.log_metric(
            "val_top_accuracy",
            float(evaluate_model(model_top, X_val_top, y_val, "val_top")),
        )

        # ===== GUARANTEED SCHEMA =====
        signature = infer_signature(
            X_tr_top,
            model_top.predict(X_tr_top),
        )

        input_example = X_tr_top.head(5)

        mlflow.sklearn.log_model(
            sk_model=model_top,
            artifact_path="model",
            signature=signature,
            input_example=input_example,
        )

        # ===== REGISTER =====
        client = MlflowClient()
        run_id = run.info.run_id

        try:
            client.get_registered_model(MODEL_NAME)
        except Exception:
            client.create_registered_model(MODEL_NAME)

        mv = client.create_model_version(
            name=MODEL_NAME,
            source=f"runs:/{run_id}/model",
            run_id=run_id,
        )

        client.set_registered_model_alias(
            name=MODEL_NAME,
            alias=MODEL_ALIAS,
            version=mv.version,
        )

        print(f"✅ {MODEL_NAME} v{mv.version} registered as @{MODEL_ALIAS}")


if __name__ == "__main__":
    main()
