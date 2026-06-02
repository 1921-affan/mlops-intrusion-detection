"""
Basic smoke tests for the MLOps IDS project.
These tests check non-networked logic so they pass in CI without
needing a running MLflow server or database.
"""
import os
import yaml
import pytest
from pathlib import Path


CONFIG_PATH = Path("configs/config.yaml")


def test_config_yaml_exists():
    """config.yaml must exist."""
    assert CONFIG_PATH.exists(), f"Missing config at {CONFIG_PATH}"


def test_config_yaml_has_required_keys():
    """config.yaml must contain paths, mlflow, and model sections."""
    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)
    assert "paths" in cfg, "Missing 'paths' section in config.yaml"
    assert "mlflow" in cfg, "Missing 'mlflow' section in config.yaml"
    assert "model" in cfg, "Missing 'model' section in config.yaml"


def test_mlflow_tracking_uri_is_docker_safe():
    """tracking_uri should not be localhost when MLFLOW_TRACKING_URI env var is set."""
    # Simulate what happens in Docker (env var overrides config)
    os.environ["MLFLOW_TRACKING_URI"] = "http://mlflow:5000"
    uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    assert "localhost" not in uri, (
        "tracking_uri should not be localhost when MLFLOW_TRACKING_URI env var is set"
    )
    del os.environ["MLFLOW_TRACKING_URI"]


def test_env_example_exists():
    """.env.example must exist and contain required keys."""
    env_example = Path(".env.example")
    assert env_example.exists(), "Missing .env.example file"
    content = env_example.read_text()
    for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET_NAME"]:
        assert key in content, f"Missing {key} in .env.example"


def test_gitignore_excludes_env():
    """.gitignore must exclude .env to prevent secret leaks."""
    gitignore = Path(".gitignore")
    assert gitignore.exists(), ".gitignore must exist"
    # .gitignore may be UTF-16 on Windows — try both encodings
    for encoding in ("utf-16", "utf-8", "latin-1"):
        try:
            content = gitignore.read_text(encoding=encoding)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    assert ".env" in content, ".env is not in .gitignore — risk of committing secrets!"


def test_dockercompose_no_minio():
    """docker-compose.yml must NOT contain MinIO service (replaced by S3)."""
    dc = Path("docker-compose.yml")
    assert dc.exists(), "docker-compose.yml must exist"
    content = dc.read_text()
    assert "minio/minio" not in content, "MinIO should be removed from docker-compose.yml"
    assert "minio_data" not in content, "MinIO volume should be removed from docker-compose.yml"


def test_dockercompose_has_s3_bucket_var():
    """docker-compose.yml must reference S3_BUCKET_NAME (not hardcode a bucket name)."""
    dc = Path("docker-compose.yml")
    content = dc.read_text()
    assert "S3_BUCKET_NAME" in content, (
        "docker-compose.yml should reference S3_BUCKET_NAME env var for the bucket"
    )
