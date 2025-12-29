import numpy as np
import pandas as pd
import xgboost as xgb
import shap
from sklearn.metrics import accuracy_score, classification_report


def create_xgb_model():
    return xgb.XGBClassifier(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=7,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42
    )


def evaluate_model(model, X, y, name: str = "dataset"):
    y_pred = model.predict(X)
    acc = accuracy_score(y, y_pred)
    print(f"[{name}] Accuracy: {acc:.4f}")
    print(classification_report(y, y_pred))
    return acc


def select_top_k_features(feature_importance: pd.DataFrame, k: int = 20):
    return feature_importance.head(k)["feature"].tolist()


def compute_shap_importance(model, X_val_sample: pd.DataFrame) -> pd.DataFrame:
    """
    Fast SHAP importance using TreeExplainer (no infinite permutation loops).
    """

    # you can control sample size here
    if len(X_val_sample) > 5000:
        X_val_sample = X_val_sample.sample(n=5000, random_state=42)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_val_sample)

    if isinstance(shap_values, list):
        per_class = [np.abs(v).mean(axis=0) for v in shap_values]
        shap_importance = np.mean(np.stack(per_class, axis=0), axis=0)
    else:
        vals = np.array(shap_values)
        if vals.ndim == 3:
            shap_importance = np.abs(vals).mean(axis=(0, 1))
        else:
            shap_importance = np.abs(vals).mean(axis=0)

    feature_importance = pd.DataFrame({
        "feature": X_val_sample.columns.tolist(),
        "mean_abs_shap": shap_importance
    }).sort_values(by="mean_abs_shap", ascending=False).reset_index(drop=True)

    return feature_importance
