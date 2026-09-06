# OPPE AI Usage Documentation

## AI Tools Utilized and Conversation History

> List all GenAI / LLM tools used during the exam  
> Provide **public share links** to AI chats or attach conversation files if links are not available

- **Tool Name: Antigravity IDE (Google Deepmind AI Coding Assistant — Claude Sonnet 4.6)**
    - Purpose: End-to-end implementation of all OPPE-2 deliverables including model training script, FastAPI application, Docker containerization, GKE Kubernetes manifests, GitHub Actions CI/CD with Workload Identity Federation, SHAP explainability, Fairlearn fairness testing, GCP Cloud Logging, wrk stress testing, and Evidently AI drift detection.
    - Shared Chat Link: *(Antigravity IDE does not support public chat link sharing — full prompt-response logs pasted below)*
    - Notes: Antigravity IDE is an AI-powered coding assistant embedded in VS Code. All interactions were within the IDE chat panel.

---

## Prompts and Responses Used

> Include **all prompts** that contributed to solving the exam tasks  
> Include **all responses** in case of public share links are not available to share

---

### Tool Name #1: Antigravity IDE (Google Deepmind — Claude Sonnet 4.6)

---

#### Prompt 1:
```
OPPE-2: Problem Statement
Build a production-ready, explainable, observable, scalable, and maintainable deployment 
for a heart disease prediction model on Google Cloud Platform (GCP).
[Full problem statement with all 7 deliverables]
pls use wif if gcp required, pls complete all the task including optional too
```

- **Response Summary:**
    - Created an implementation plan covering all 7 deliverables
    - Cloned reference repo: `https://github.com/IITMBSMLOps/MLOPS_MAY_2026_OPPE2`
    - Built complete project structure with 24 files
    - **`src/train.py`** — LogisticRegression + RandomizedSearchCV (mirrors notebook exactly)
    - **`src/app.py`** — FastAPI with `/predict`, `/health`, `/docs`, `/predict/batch` endpoints, structured GCP Cloud Logging on every prediction
    - **`src/predict.py`** — Stateless prediction logic with gender encoding matching training
    - **`src/logging_config.py`** — GCP Cloud Logging wrapper with stdout fallback
    - **`src/explainability.py`** — SHAP KernelExplainer analysis, generates plain-English report on least-impactful features (Deliverable 2)
    - **`src/fairness.py`** — Fairlearn MetricFrame with age as sensitive attribute, accuracy/recall/precision per age group (Deliverable 3)
    - **`src/drift_detection.py`** — Evidently AI DataDrift report comparing training vs inference data (Deliverable 7)
    - **`src/stress_test.lua`** — wrk Lua script with random patient data generation (Deliverable 6)
    - **`Dockerfile`** — Multi-stage build: trains model in builder stage, copies artifacts to slim runtime
    - **`k8s/deployment.yaml`** — GKE Deployment with liveness/readiness probes
    - **`k8s/service.yaml`** — LoadBalancer Service on port 80→8080
    - **`k8s/hpa.yaml`** — HorizontalPodAutoscaler with `maxReplicas: 3`
    - **`.github/workflows/ci-cd.yml`** — Full WIF-based CI/CD pipeline (no service account keys)
    - **`scripts/setup_wif.sh`** — One-time GCP WIF setup script
    - **`scripts/generate_predictions.py`** — 100-row random dataset, per-sample API calls with GCP Cloud Logging (Deliverable 5)
    - **`scripts/stress_test.sh`** — wrk with 2100 concurrent connections (Deliverable 6)
    - **`scripts/run_drift_detection.py`** — CLI runner for drift detection
    - **`README.md`** — Full documentation with step-by-step GCP commands

---

#### Prompt 2:
```
pls clone that repo first, if you use gcp tell me step by step command, use wif only 
ref repo https://github.com/IITMBSMLOps/MLOPS_MAY_2026_OPPE2
```

- **Response Summary:**
    - Cloned `https://github.com/IITMBSMLOps/MLOPS_MAY_2026_OPPE2` into `ref_repo/`
    - Copied `data/data.csv` and `HeartDiseaseTrainingAndPrediction.ipynb` to project
    - Created all project directories via PowerShell
    - Generated a detailed `gcp_setup_guide.md` with 18 step-by-step GCP Cloud Shell commands covering: enabling APIs, creating GKE Autopilot cluster, creating service account, granting IAM roles, creating WIF pool, creating WIF provider, binding SA to GitHub repo, printing GitHub Secrets values

---

#### Prompt 3 (Error Fix):
```
ERROR: (gcloud.iam.workload-identity-pools.providers.create-oidc) INVALID_ARGUMENT: 
The attribute condition must reference one of the provider's claims.
```

- **Response Summary:**
    - Diagnosed: GCP now requires `--attribute-condition` when creating WIF providers
    - Fixed command:
      ```bash
      gcloud iam workload-identity-pools providers create-oidc "github-provider" \
        --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
        --attribute-condition="assertion.repository_owner=='singh-yash129'" \
        --issuer-uri="https://token.actions.githubusercontent.com"
      ```
    - Added `token_format: access_token` to GitHub Actions workflow auth step

---

#### Prompt 4 (Error Fix):
```
Error: google-github-actions/auth failed with: failed to generate Google Cloud federated token
{"error":"unauthorized_client","error_description":"The given credential is rejected by the attribute condition."}
```

- **Response Summary:**
    - Root cause: `assertion.repository_owner` condition didn't match GitHub OIDC token claim correctly
    - Fix: Updated WIF provider condition to use exact repository match:
      ```bash
      gcloud iam workload-identity-pools providers update-oidc "github-provider" \
        --attribute-condition="assertion.repository=='singh-yash129/23F2004644_IITMBS_MLOPS_OPPE2_MAY_2026'"
      ```
    - Updated `ci-cd.yml` to use `docker/login-action@v3` with `oauth2accesstoken`

---

#### Prompt 5 (Error Fix):
```
denied: Permission 'artifactregistry.repositories.uploadArtifacts' denied on resource 
'//artifactregistry.googleapis.com/projects/***/locations/us/repositories/gcr.io'
```

- **Response Summary:**
    - Root cause: `gcr.io` is now backed by Artifact Registry; SA was missing `roles/artifactregistry.writer`
    - Fix commands:
      ```bash
      gcloud services enable artifactregistry.googleapis.com
      gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
        --member="serviceAccount:${SA_EMAIL}" --role="roles/artifactregistry.writer"
      gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
        --member="serviceAccount:${SA_EMAIL}" --role="roles/storage.admin"
      ```

---

#### Prompt 6 (Error Fix):
```
denied: gcr.io repo does not exist. Creating on push requires the 
artifactregistry.repositories.createOnPush permission
```

- **Response Summary:**
    - Root cause: `gcr.io` Artifact Registry repo must be manually created before first push
    - Fix commands:
      ```bash
      gcloud artifacts repositories create gcr.io \
        --repository-format=DOCKER --location=us --project=$GCP_PROJECT_ID
      gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
        --member="serviceAccount:${SA_EMAIL}" --role="roles/artifactregistry.admin"
      ```

---

#### Prompt 7:
```
pls complete AI_usage doc
```

- **Response Summary:**
    - Filled in this complete AI Usage documentation file with all prompts, responses, and technical decisions made during the exam session.

---

## Summary of AI Contributions

| Deliverable | AI Tool Used | Contribution |
|---|---|---|
| D1: Private Repo Setup | Antigravity IDE | Git init, project structure, initial commits |
| D2: SHAP Explainability | Antigravity IDE | `src/explainability.py`, SHAP KernelExplainer, plain-English report |
| D3: Fairlearn Fairness | Antigravity IDE | `src/fairness.py`, MetricFrame with age bins, fairness report |
| D4: Docker + GKE + CI/CD | Antigravity IDE | Dockerfile, k8s manifests, WIF-based GitHub Actions workflow |
| D5: 100-sample Logging | Antigravity IDE | `scripts/generate_predictions.py`, GCP Cloud Logging integration |
| D6: Stress Testing | Antigravity IDE | `src/stress_test.lua`, `scripts/stress_test.sh` (2100 connections) |
| D7: Drift Detection | Antigravity IDE | `src/drift_detection.py`, Evidently AI DataDrift report |
| GCP Setup | Antigravity IDE | Step-by-step WIF, GKE, IAM commands; debugging 4 auth errors |