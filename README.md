# Heart Disease Prediction API — MLOPS 

## Overview

Production-ready MLOps deployment of a heart disease prediction model on **Google Kubernetes Engine (GKE)** with full CI/CD via **GitHub Actions + Workload Identity Federation**.

| Deliverable | Status | Marks |
|---|---|---|
| D1: Private Repo | ✅ Done | Mandatory |
| D2: SHAP Explainability | ✅ Done | 10 |
| D3: Fairlearn Fairness (age) | ✅ Done | 10 |
| D4: Docker + GKE + CI/CD (WIF) | ✅ Done | 40 |
| D5: 100-sample logging + Cloud Logging | ✅ Done | 20 |
| D6: wrk stress test (>2000 connections) | ✅ Done | 10 |
| D7: Evidently drift detection | ✅ Done | 10 |

---

## Architecture

```
GitHub (push) → GitHub Actions (WIF) → GCR (Docker image) → GKE (max 3 pods)
                                                              ↓
                                                         FastAPI /predict
                                                              ↓
                                                       GCP Cloud Logging
```

## Tech Stack

- **Model**: LogisticRegression + RandomizedSearchCV (sklearn)
- **API**: FastAPI + Uvicorn
- **Container**: Docker (multi-stage)
- **Orchestration**: GKE Autopilot + HPA (max 3 pods)
- **CI/CD**: GitHub Actions + Workload Identity Federation (no service account keys)
- **Explainability**: SHAP KernelExplainer
- **Fairness**: Fairlearn MetricFrame (sensitive: age)
- **Observability**: GCP Cloud Logging
- **Drift**: Evidently AI
- **Stress Test**: wrk (2100 concurrent connections)

---

## Repository Structure

```
├── data/data.csv                          # Heart disease dataset
├── notebooks/                             # Original notebook
├── src/
│   ├── train.py                          # Model training
│   ├── app.py                            # FastAPI application
│   ├── predict.py                        # Prediction logic
│   ├── explainability.py                 # SHAP analysis (D2)
│   ├── fairness.py                       # Fairlearn analysis (D3)
│   ├── logging_config.py                 # GCP Cloud Logging
│   ├── drift_detection.py                # Evidently drift (D7)
│   └── stress_test.lua                   # wrk script (D6)
├── k8s/
│   ├── deployment.yaml                   # GKE Deployment
│   ├── service.yaml                      # LoadBalancer Service
│   └── hpa.yaml                          # HPA (max 3 pods)
├── scripts/
│   ├── setup_wif.sh                      # One-time WIF setup
│   ├── generate_predictions.py           # 100-row logging (D5)
│   ├── stress_test.sh                    # wrk runner (D6)
│   └── run_drift_detection.py            # Drift CLI (D7)
├── reports/                              # Generated reports
├── Dockerfile
└── requirements.txt
```

---

## Setup Guide

### Step 1: GCP Setup (run once)

Open **Google Cloud Shell** or your local terminal with `gcloud` installed:

```bash
# Clone your repo
git clone https://github.com/singh-yash129/23F2004644_IITMBS_MLOPS_OPPE2_MAY_2026.git
cd 23F2004644_IITMBS_MLOPS_OPPE2_MAY_2026

# Set variables
export GCP_PROJECT_ID="YOUR_PROJECT_ID"
export GITHUB_REPO="singh-yash129/23F2004644_IITMBS_MLOPS_OPPE2_MAY_2026"
export GCP_REGION="us-central1"

# Run one-time WIF setup (creates cluster, SA, WIF pool/provider)
bash scripts/setup_wif.sh
```

### Step 2: Add GitHub Secrets

Go to: `https://github.com/singh-yash129/23F2004644_IITMBS_MLOPS_OPPE2_MAY_2026/settings/secrets/actions`

Add these secrets (values printed by `setup_wif.sh`):

| Secret Name | Value |
|---|---|
| `GCP_PROJECT_ID` | your-project-id |
| `WIF_PROVIDER` | projects/.../providers/github-provider |
| `WIF_SERVICE_ACCOUNT` | github-actions-sa@...iam.gserviceaccount.com |

### Step 3: Push to Trigger CI/CD

```bash
git add .
git commit -m "Initial deployment"
git push origin main
# → GitHub Actions triggers automatically
# → Builds Docker image, pushes to GCR, deploys to GKE
```

### Step 4: Get API External IP

```bash
gcloud container clusters get-credentials heart-disease-cluster \
  --region us-central1 --project $GCP_PROJECT_ID

kubectl get svc heart-disease-api-svc
# Copy the EXTERNAL-IP
```

---

## API Usage

```bash
# Health check
curl http://<EXTERNAL_IP>/health

# Single prediction
curl -X POST http://<EXTERNAL_IP>/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 63, "gender": "male", "cp": 3,
    "trestbps": 145.0, "chol": 233.0, "fbs": 1,
    "restecg": 0, "thalach": 150.0, "exang": 0,
    "oldpeak": 2.3, "slope": 0, "ca": 0, "thal": 1
  }'

# Interactive docs
open http://<EXTERNAL_IP>/docs
```

---

## Deliverable 5: 100-Sample Prediction Logging

```bash
# Run 100 per-sample predictions (logs each to GCP Cloud Logging)
export API_URL="http://<EXTERNAL_IP>"
python scripts/generate_predictions.py $API_URL

# View logs in GCP Console:
# https://console.cloud.google.com/logs/query
# Filter: logName="heart-disease-api"
```

## Deliverable 6: Stress Testing

```bash
# Install wrk (Linux/Mac)
# Ubuntu: sudo apt install wrk
# Mac: brew install wrk

bash scripts/stress_test.sh <EXTERNAL_IP>
# Runs: wrk -t12 -c2100 -d30s -s src/stress_test.lua http://<IP>/predict
```

## Deliverable 7: Drift Detection

```bash
# After running generate_predictions.py
python scripts/run_drift_detection.py
# Opens: reports/drift_report.html
```

## Deliverable 2 & 3: Responsible AI Reports

```bash
# Install deps locally
pip install -r requirements.txt

# Train model
python -m src.train

# SHAP Explainability (D2)
python -m src.explainability
# → reports/explainability_report.md
# → reports/shap_summary.png

# Fairlearn Fairness (D3)
python -m src.fairness
# → reports/fairness_report.md
# → reports/fairness_by_age.png
```

---

## GCP Cloud Logging — View Prediction Logs

```
https://console.cloud.google.com/logs/query;
query=resource.type="k8s_container"
  AND jsonPayload.request_id!=""
```

Or use `gcloud`:
```bash
gcloud logging read 'logName="projects/YOUR_PROJECT/logs/heart-disease-api"' \
  --project=YOUR_PROJECT_ID \
  --limit=20 \
  --format=json
```

---

## Dataset

Source: [IITMBSMLOps/MLOPS_MAY_2026_OPPE2](https://github.com/IITMBSMLOps/MLOPS_MAY_2026_OPPE2)

| Feature | Description |
|---|---|
| age | Age in years |
| gender | male / female |
| cp | Chest pain type (0-3) |
| trestbps | Resting blood pressure |
| chol | Serum cholesterol (mg/dl) |
| fbs | Fasting blood sugar > 120 mg/dl |
| restecg | Resting ECG results |
| thalach | Max heart rate achieved |
| exang | Exercise induced angina |
| oldpeak | ST depression by exercise |
| slope | Slope of peak exercise ST segment |
| ca | Major vessels by fluoroscopy (0-3) |
| thal | 0=normal; 1=fixed defect; 2=reversable defect |
| **target** | **yes / no (heart disease)** |
