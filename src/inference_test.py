import json
from pathlib import Path

import yaml
import mlflow
from mlflow import xgboost as mlflow_xgb

from src.data.loader import load_processed_data, preprocess_data

CONFIG_PATH = Path("configs/config.yaml")


def main():
    # 1. Load config
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    train_path = config["paths"]["train_csv"]
    test_path = config["paths"]["test_csv"]
    artifacts_dir = Path(config["paths"]["artifacts_dir"])

    # 2. Connect to the MLflow server
    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])

    # 3. Load the registered model from MLflow Model Registry
    #    (You saw Version 1 in the UI)
    
    model_uri = "models:/model_top20@production"
    model = mlflow_xgb.load_model(model_uri)

    # 4. Load data and preprocess (same as training)
    train_df, test_df = load_processed_data(train_path, test_path)
    X_full, y_full, X_test_full, y_test, feature_cols = preprocess_data(
        train_df, test_df
    )

    # 5. Load top-20 features list
    with open(artifacts_dir / "top_features.json", "r") as f:
        top_features = json.load(f)

    # 6. Take a small sample from test data
    X_sample = X_test_full[top_features].head(5)
    y_sample = y_test.head(5)

    # 7. Predict
    preds = model.predict(X_sample)

    print("Top-20 features used:", top_features)
    print("\nSample input shape:", X_sample.shape)
    print("Predictions:", preds)
    print("True labels:", y_sample.values)

        # ---- NEW: Evaluate on full test set ----
    from sklearn.metrics import accuracy_score, classification_report

    X_test_top = X_test_full[top_features]
    y_test_pred = model.predict(X_test_top)

    test_acc = accuracy_score(y_test, y_test_pred)
    print("\n=== Full Test Set Evaluation ===")
    print(f"Test accuracy: {test_acc:.4f}")
    print(classification_report(y_test, y_test_pred))

if __name__ == "__main__":
    main()
