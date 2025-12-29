from pathlib import Path
from typing import Tuple, List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder


def load_processed_data(
    train_path: str,
    test_path: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    train_file = Path(train_path)
    test_file = Path(test_path)

    if not train_file.exists():
        raise FileNotFoundError(f"Train file not found: {train_file}")
    if not test_file.exists():
        raise FileNotFoundError(f"Test file not found: {test_file}")

    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)

    return train_df, test_df


def _apply_log_transforms(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    log_features = [
        "trans_depth",
        "response_body_len",
        "sbytes",
        "sloss",
        "dloss",
        "spkts",
        "dbytes",
        "dpkts",
        "dinpkt",
        "djit",
        "sload",
        "sinpkt",
        "dur",
    ]

    for col in log_features:
        if col in train_df.columns:
            train_df[col + "_log"] = np.log1p(train_df[col])
        if col in test_df.columns:
            test_df[col + "_log"] = np.log1p(test_df[col])


def _encode_categoricals(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    cat_cols = ["proto", "service", "state"]

    for col in cat_cols:
        if col not in train_df.columns:
            continue

        le = LabelEncoder()
        combined = pd.concat([train_df[col], test_df[col]], axis=0).astype(str)
        le.fit(combined)

        train_df[col + "_enc"] = le.transform(train_df[col].astype(str))
        test_df[col + "_enc"] = le.transform(test_df[col].astype(str))


def preprocess_data(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, Optional[pd.Series], List[str]]:

    cols_to_drop = []
    for col in ["attack_cat", "id"]:
        if col in train_df.columns:
            cols_to_drop.append(col)

    train_df = train_df.drop(columns=cols_to_drop, errors="ignore")
    test_df = test_df.drop(columns=cols_to_drop, errors="ignore")

    _apply_log_transforms(train_df, test_df)
    _encode_categoricals(train_df, test_df)

    if "ct_ftp_cmd" in train_df.columns:
        train_df = train_df.drop(columns=["ct_ftp_cmd"])
    if "ct_ftp_cmd" in test_df.columns:
        test_df = test_df.drop(columns=["ct_ftp_cmd"])

    enc_cols = ["proto_enc", "service_enc", "state_enc"]
    log_cols = [c for c in train_df.columns if c.endswith("_log")]

    numeric_cols = train_df.select_dtypes(include=["number"]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in enc_cols + ["label"]]

    feature_cols = list(dict.fromkeys(numeric_cols + enc_cols + log_cols))

    X_train = train_df[feature_cols]
    y_train = train_df["label"]

    X_test = test_df[feature_cols]
    y_test = test_df["label"] if "label" in test_df.columns else None

    return X_train, y_train, X_test, y_test, feature_cols
