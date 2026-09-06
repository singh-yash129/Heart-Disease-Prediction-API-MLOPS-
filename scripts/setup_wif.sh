#!/usr/bin/env bash
# =============================================================================
# setup_wif.sh — One-time WIF (Workload Identity Federation) setup for GKE CI/CD
# =============================================================================
# Usage:
#   export GCP_PROJECT_ID="your-project-id"
#   export GITHUB_REPO="singh-yash129/23F2004644_IITMBS_MLOPS_OPPE2_MAY_2026"
#   bash scripts/setup_wif.sh
#
# After running, copy the printed values as GitHub repository secrets.
# =============================================================================
set -euo pipefail

# ── Configuration — EDIT THESE ────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID env var}"
GITHUB_REPO="${GITHUB_REPO:?Set GITHUB_REPO env var (owner/repo)}"
GCP_REGION="${GCP_REGION:-us-central1}"
CLUSTER_NAME="${GKE_CLUSTER:-heart-disease-cluster}"

# Derived
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
SA_NAME="github-actions-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
WIF_POOL="github-pool"
WIF_PROVIDER="github-provider"

echo "=================================================================="
echo "  MLOPS OPPE-2 — GCP Workload Identity Federation Setup"
echo "=================================================================="
echo "  Project ID     : ${PROJECT_ID}"
echo "  Project Number : ${PROJECT_NUMBER}"
echo "  GitHub Repo    : ${GITHUB_REPO}"
echo "  GCP Region     : ${GCP_REGION}"
echo "  GKE Cluster    : ${CLUSTER_NAME}"
echo "=================================================================="
echo ""

# ── Step 1: Enable required GCP APIs ─────────────────────────────────────────
echo "🔧 [1/8] Enabling required APIs..."
gcloud services enable \
  container.googleapis.com \
  containerregistry.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  --project="${PROJECT_ID}"
echo "   ✅ APIs enabled"

# ── Step 2: Create GKE Cluster ────────────────────────────────────────────────
echo ""
echo "🔧 [2/8] Creating GKE Autopilot cluster: ${CLUSTER_NAME}..."
if gcloud container clusters describe "${CLUSTER_NAME}" \
     --region="${GCP_REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "   ℹ️  Cluster already exists — skipping creation"
else
  gcloud container clusters create-auto "${CLUSTER_NAME}" \
    --region="${GCP_REGION}" \
    --project="${PROJECT_ID}"
  echo "   ✅ Cluster created"
fi

# ── Step 3: Create Service Account ───────────────────────────────────────────
echo ""
echo "🔧 [3/8] Creating service account: ${SA_NAME}..."
if gcloud iam service-accounts describe "${SA_EMAIL}" \
     --project="${PROJECT_ID}" &>/dev/null; then
  echo "   ℹ️  Service account already exists"
else
  gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="GitHub Actions CI/CD Service Account" \
    --project="${PROJECT_ID}"
  echo "   ✅ Service account created"
fi

# ── Step 4: Grant IAM roles ───────────────────────────────────────────────────
echo ""
echo "🔧 [4/8] Granting IAM roles to service account..."
for ROLE in \
  "roles/container.developer" \
  "roles/storage.admin" \
  "roles/logging.logWriter" \
  "roles/monitoring.metricWriter" \
  "roles/artifactregistry.writer"; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --quiet
  echo "   ✅ Granted: ${ROLE}"
done

# ── Step 5: Create Workload Identity Pool ─────────────────────────────────────
echo ""
echo "🔧 [5/8] Creating Workload Identity Pool: ${WIF_POOL}..."
if gcloud iam workload-identity-pools describe "${WIF_POOL}" \
     --location="global" --project="${PROJECT_ID}" &>/dev/null; then
  echo "   ℹ️  Pool already exists"
else
  gcloud iam workload-identity-pools create "${WIF_POOL}" \
    --location="global" \
    --display-name="GitHub Actions Pool" \
    --project="${PROJECT_ID}"
  echo "   ✅ Pool created"
fi

# ── Step 6: Create Workload Identity Provider ─────────────────────────────────
echo ""
echo "🔧 [6/8] Creating Workload Identity Provider: ${WIF_PROVIDER}..."
POOL_NAME="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${WIF_POOL}"

if gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER}" \
     --workload-identity-pool="${WIF_POOL}" \
     --location="global" --project="${PROJECT_ID}" &>/dev/null; then
  echo "   ℹ️  Provider already exists"
else
  gcloud iam workload-identity-pools providers create-oidc "${WIF_PROVIDER}" \
    --location="global" \
    --workload-identity-pool="${WIF_POOL}" \
    --display-name="GitHub Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.actor=assertion.actor" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --project="${PROJECT_ID}"
  echo "   ✅ Provider created"
fi

# ── Step 7: Bind Service Account to GitHub Repo ───────────────────────────────
echo ""
echo "🔧 [7/8] Binding SA to GitHub repo principal..."
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.repository/${GITHUB_REPO}"
echo "   ✅ Binding created"

# ── Step 8: Output GitHub Secrets ─────────────────────────────────────────────
PROVIDER_FULL="${POOL_NAME}/providers/${WIF_PROVIDER}"

echo ""
echo "=================================================================="
echo "  ✅ SETUP COMPLETE — Add these as GitHub Repository Secrets"
echo "=================================================================="
echo ""
echo "  Secret Name            Value"
echo "  ─────────────────────────────────────────────────────────────"
echo "  GCP_PROJECT_ID       → ${PROJECT_ID}"
echo ""
echo "  WIF_PROVIDER         → ${PROVIDER_FULL}"
echo ""
echo "  WIF_SERVICE_ACCOUNT  → ${SA_EMAIL}"
echo ""
echo "=================================================================="
echo ""
echo "📌 Add secrets at:"
echo "   https://github.com/${GITHUB_REPO}/settings/secrets/actions"
echo ""
echo "📌 Get GKE credentials locally:"
echo "   gcloud container clusters get-credentials ${CLUSTER_NAME} \\"
echo "     --region ${GCP_REGION} --project ${PROJECT_ID}"
