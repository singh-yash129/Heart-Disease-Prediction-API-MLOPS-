# ── Stage 1: Builder — install deps & train model ─────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source & data
COPY data/ data/
COPY src/   src/

# Ensure src is importable as a package
RUN touch src/__init__.py

# Train model at build time → produces model/heart_disease_model.pkl
RUN python -m src.train

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime deps only
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source + trained model artifacts from builder
COPY src/  src/
COPY data/ data/
COPY --from=builder /app/model/ model/

# Ensure src is importable as a package
RUN touch src/__init__.py

EXPOSE 8080

# Healthcheck — give app 30s to start (model load takes a moment)
HEALTHCHECK --interval=30s --timeout=15s --start-period=45s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run as root is acceptable for GKE Autopilot (avoids permission issues)
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--log-level", "info"]
