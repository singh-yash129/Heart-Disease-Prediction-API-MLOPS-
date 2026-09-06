"""
logging_config.py — GCP Cloud Logging with guaranteed non-fatal fallback.
The app MUST NOT crash if Cloud Logging is unavailable.
"""
import json
import logging
import os
import sys


def get_logger(name: str = "heart-disease-api"):
    """
    Returns a logger. Always falls back to stdout — never crashes the app.
    GCP Cloud Logging is used when GCP_PROJECT_ID env var is set AND permissions exist.
    """
    project_id = os.getenv("GCP_PROJECT_ID", "")

    if project_id:
        try:
            from google.cloud import logging as gcp_logging
            client = gcp_logging.Client(project=project_id)
            # Test the connection with a simple write — if it fails, fall back
            cloud_logger = client.logger(name)
            cloud_logger.log_text("Heart Disease API logger initialized", severity="INFO")
            print(f"[INFO] GCP Cloud Logging enabled (project={project_id})", file=sys.stderr)
            return _GCPLoggerWrapper(cloud_logger, name)
        except Exception as e:
            print(f"[WARNING] GCP Logging unavailable: {e}", file=sys.stderr)
            print("[WARNING] Falling back to stdout logging.", file=sys.stderr)

    # Fallback: structured JSON to stdout (always works)
    _logger = logging.getLogger(name)
    if not _logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JSONFormatter())
        _logger.addHandler(handler)
        _logger.setLevel(logging.INFO)
    return _StdoutLoggerWrapper(_logger)


class _JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "severity": record.levelname,
            "message":  record.getMessage(),
            "logger":   record.name,
        }
        return json.dumps(payload)


class _GCPLoggerWrapper:
    """Thin wrapper around google.cloud.logging — never raises exceptions."""
    def __init__(self, cloud_logger, name):
        self._logger = cloud_logger
        self._name = name
        # Stdout fallback for when GCP calls fail
        self._fallback = logging.getLogger(name + ".fallback")
        if not self._fallback.handlers:
            h = logging.StreamHandler(sys.stdout)
            h.setFormatter(_JSONFormatter())
            self._fallback.addHandler(h)
            self._fallback.setLevel(logging.INFO)

    def log_struct(self, payload: dict, severity: str = "INFO"):
        try:
            self._logger.log_struct(payload, severity=severity)
        except Exception:
            # Always fall back to stdout — never crash
            self._fallback.info(json.dumps(payload))

    def info(self, msg: str, **kwargs):
        payload = {"message": msg, **kwargs}
        self.log_struct(payload, severity="INFO")

    def error(self, msg: str, **kwargs):
        payload = {"message": msg, **kwargs}
        self.log_struct(payload, severity="ERROR")


class _StdoutLoggerWrapper:
    """Stdout-only logger — always works."""
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
