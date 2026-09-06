"""
logging_config.py — GCP Cloud Logging setup with local fallback.
Uses the GCP_PROJECT_ID env-var injected by Kubernetes (via GitHub Secrets).
"""
import json
import logging
import os
import sys


def get_logger(name: str = "heart-disease-api"):
    """
    Returns a logger that writes structured JSON to GCP Cloud Logging
    when running on GKE, or to stdout when running locally.
    """
    project_id = os.getenv("GCP_PROJECT_ID", "")

    if project_id:
        try:
            from google.cloud import logging as gcp_logging
            client = gcp_logging.Client(project=project_id)
            # Attach GCP handler — this sends logs to Cloud Logging
            cloud_logger = client.logger(name)
            return _GCPLoggerWrapper(cloud_logger, name)
        except Exception as e:
            print(f"[WARNING] GCP Logging unavailable ({e}), falling back to stdout", file=sys.stderr)

    # Fallback: structured JSON to stdout (still ingestible by GCP if log-based sink configured)
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return _StdoutLoggerWrapper(logger)


class _JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "severity": record.levelname,
            "message":  record.getMessage(),
            "logger":   record.name,
        }
        return json.dumps(payload)


class _GCPLoggerWrapper:
    """Thin wrapper around google.cloud.logging Cloud Logger."""
    def __init__(self, cloud_logger, name):
        self._logger = cloud_logger
        self._name = name

    def log_struct(self, payload: dict, severity: str = "INFO"):
        self._logger.log_struct(payload, severity=severity)

    def info(self, msg: str, **kwargs):
        payload = {"message": msg, **kwargs}
        self._logger.log_struct(payload, severity="INFO")

    def error(self, msg: str, **kwargs):
        payload = {"message": msg, **kwargs}
        self._logger.log_struct(payload, severity="ERROR")


class _StdoutLoggerWrapper:
    """Thin wrapper that mimics GCPLoggerWrapper interface over stdlib logging."""
    def __init__(self, logger):
        self._logger = logger

    def log_struct(self, payload: dict, severity: str = "INFO"):
        self._logger.info(json.dumps(payload))

    def info(self, msg: str, **kwargs):
        payload = {"message": msg, **kwargs}
        self._logger.info(json.dumps(payload))

    def error(self, msg: str, **kwargs):
        payload = {"message": msg, **kwargs}
        self._logger.error(json.dumps(payload))
