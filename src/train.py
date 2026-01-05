import json
from pathlib import Path
import yaml

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    confusion_matrix,
    ConfusionMatrixDisplay,
    roc_curve,
    auc,
    precision_score,
    recall_score,
    f1_score,
)

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


def enforce_stable_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce inference-safe dtypes:
    - ints   -> int32
    - floats -> float32
    """
    df = df.copy()
    for col in df.columns:
        if df[col].dtype in ["int64", "int32"]:
            df[col] = df[col].astype("int32")
        else:
            df[col] = df[col].astype("float32")
    return df


def main():
    # ================= CONFIG =================
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    train_path = config["paths"]["train_csv"]
    test_path = config["paths"]["test_csv"]

    artifacts_dir = Path(config["paths"]["artifacts_dir"])
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # ================= MLFLOW =================
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment(config["mlflow"]["experiment_name"])

    # ================= DATA =================
    train_df, test_df = load_processed_data(train_path, test_path)

    X_full, y_full, X_test_full, y_test, feature_cols = preprocess_data(
        train_df, test_df
    )

    X_full = enforce_stable_dtypes(X_full)

    X_tr, X_val, y_tr, y_val = train_test_split(
        X_full,
        y_full,
        test_size=0.2,
        random_state=42,
        stratify=y_full,
    )

    # ================= RUN =================
    with mlflow.start_run(run_name=config["mlflow"]["run_name"]) as run:

        # =========================================================
        # 1️⃣ LOG PARAMETERS (VISIBLE IN UI)
        # =========================================================
        mlflow.log_params({
            "model_type": "XGBoost",
            "top_k_features": int(config["model"]["top_k_features"]),
            "train_rows": int(X_tr.shape[0]),
            "val_rows": int(X_val.shape[0]),
            "num_features_full": int(X_tr.shape[1]),
        })

        # =========================================================
        # 2️⃣ BASE MODEL (FULL FEATURES)
        # =========================================================
        base_model = create_xgb_model()
        base_model.fit(X_tr, y_tr)

        train_acc = float(evaluate_model(base_model, X_tr, y_tr, "train_full"))
        val_acc = float(evaluate_model(base_model, X_val, y_val, "val_full"))

        mlflow.log_metric("train_full_accuracy", train_acc)
        mlflow.log_metric("val_full_accuracy", val_acc)

        # =========================================================
        # 3️⃣ SHAP → TOP FEATURES
        # =========================================================
        if USE_SHAP:
            shap_importance = compute_shap_importance(
                base_model,
                X_val.sample(n=800, random_state=42),
            )

            top_features = select_top_k_features(
                shap_importance,
                k=config["model"]["top_k_features"],
            )

            top_features_path = artifacts_dir / "top_features.json"
            with open(top_features_path, "w") as f:
                json.dump(top_features, f, indent=2)

            mlflow.log_artifact(str(top_features_path))
        else:
            with open(artifacts_dir / "top_features.json", "r") as f:
                top_features = json.load(f)

        # =========================================================
        # 4️⃣ DATASET INFO (ARTIFACT – SAFE)
        # =========================================================
        dataset_info = {
            "train_shape": X_tr.shape,
            "val_shape": X_val.shape,
            "num_features": int(X_tr.shape[1]),
            "feature_names": list(X_tr.columns),
        }

        dataset_info_path = artifacts_dir / "dataset_info.json"
        with open(dataset_info_path, "w") as f:
            json.dump(dataset_info, f, indent=2)

        mlflow.log_artifact(str(dataset_info_path))

        # =========================================================
        # 5️⃣ TOP-K DATA
        # =========================================================
        X_tr_top = enforce_stable_dtypes(X_tr[top_features])
        X_val_top = enforce_stable_dtypes(X_val[top_features])

        # =========================================================
        # 6️⃣ TOP-K MODEL
        # =========================================================
        model_top = create_xgb_model()
        model_top.fit(X_tr_top, y_tr)

        y_val_pred = model_top.predict(X_val_top)
        y_val_proba = model_top.predict_proba(X_val_top)[:, 1].astype("float32")

        # =========================================================
        # 7️⃣ METRICS
        # =========================================================
        mlflow.log_metric("val_top_accuracy", float((y_val_pred == y_val).mean()))
        mlflow.log_metric("precision", float(precision_score(y_val, y_val_pred)))
        mlflow.log_metric("recall", float(recall_score(y_val, y_val_pred)))
        mlflow.log_metric("f1_score", float(f1_score(y_val, y_val_pred)))

        # =========================================================
        # 8️⃣ CONFUSION MATRIX
        # =========================================================
        cm = confusion_matrix(y_val, y_val_pred)
        ConfusionMatrixDisplay(cm).plot(cmap="Blues")

        cm_path = artifacts_dir / "confusion_matrix.png"
        plt.savefig(cm_path, bbox_inches="tight")
        plt.close()
        mlflow.log_artifact(str(cm_path))

        # =========================================================
        # 9️⃣ ROC CURVE
        # =========================================================
        fpr, tpr, _ = roc_curve(y_val, y_val_proba)
        roc_auc = auc(fpr, tpr)
        mlflow.log_metric("roc_auc", float(roc_auc))

        plt.figure()
        plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.4f}")
        plt.plot([0, 1], [0, 1], linestyle="--")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.legend()

        roc_path = artifacts_dir / "roc_curve.png"
        plt.savefig(roc_path, bbox_inches="tight")
        plt.close()
        mlflow.log_artifact(str(roc_path))

        # =========================================================
        # 🔟 FEATURE IMPORTANCE (NON-SHAP)
        # =========================================================
        importances = model_top.feature_importances_
        indices = np.argsort(importances)[::-1]

        plt.figure(figsize=(8, 5))
        plt.bar(range(len(importances)), importances[indices])
        plt.xticks(
            range(len(importances)),
            np.array(top_features)[indices],
            rotation=90,
        )
        plt.title("Feature Importance")

        fi_path = artifacts_dir / "feature_importance.png"
        plt.savefig(fi_path, bbox_inches="tight")
        plt.close()
        mlflow.log_artifact(str(fi_path))

        # =========================================================
        # 11️⃣ MODEL LOGGING (INFERENCE-SAFE)
        # =========================================================
        signature = infer_signature(
            X_tr_top,
            model_top.predict(X_tr_top),
        )

        mlflow.sklearn.log_model(
            sk_model=model_top,
            artifact_path="model",
            signature=signature,
            input_example=X_tr_top.head(5),
        )

        # =========================================================
        # 12️⃣ REGISTER MODEL
        # =========================================================
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
