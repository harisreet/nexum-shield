#!/usr/bin/env bash
# NEXUM SHIELD — GCP Infrastructure Setup
# Usage: PROJECT_ID=your-project-id ./infra/setup.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?ERROR: PROJECT_ID env var is required}"
REGION="us-central1"
BUCKET="nexum-assets"
TOPIC="media-events"
SUBSCRIPTION="media-worker-sub"
SERVICE_ACCOUNT="nexum-worker"

echo "▶ Setting up NEXUM SHIELD on project: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# ─── Enable APIs ──────────────────────────────────────────────────
echo "▶ Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  firestore.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# ─── Cloud Storage ────────────────────────────────────────────────
echo "▶ Creating GCS bucket: gs://$BUCKET"
gcloud storage buckets create "gs://$BUCKET" \
  --location="$REGION" \
  --uniform-bucket-level-access 2>/dev/null || echo "  Bucket already exists, skipping."

# ─── Firestore ────────────────────────────────────────────────────
echo "▶ Creating Firestore database..."
gcloud firestore databases create \
  --location="$REGION" 2>/dev/null || echo "  Firestore already exists, skipping."

# ─── Pub/Sub ──────────────────────────────────────────────────────
echo "▶ Creating Pub/Sub topic: $TOPIC"
gcloud pubsub topics create "$TOPIC" 2>/dev/null || echo "  Topic already exists, skipping."

# ─── Service Account ──────────────────────────────────────────────
echo "▶ Creating service account: $SERVICE_ACCOUNT"
gcloud iam service-accounts create "$SERVICE_ACCOUNT" \
  --display-name="NEXUM Worker Service Account" 2>/dev/null || echo "  SA already exists, skipping."

SA_EMAIL="$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com"

# Grant roles
echo "▶ Granting IAM roles..."
for ROLE in \
  "roles/storage.objectAdmin" \
  "roles/pubsub.subscriber" \
  "roles/pubsub.publisher" \
  "roles/datastore.user" \
  "roles/run.invoker"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE" --quiet
done

# ─── Artifact Registry ────────────────────────────────────────────
echo "▶ Creating Artifact Registry repository..."
gcloud artifacts repositories create nexum \
  --repository-format=docker \
  --location="$REGION" \
  --description="NEXUM SHIELD Docker images" 2>/dev/null || echo "  Registry already exists."

echo ""
echo "✅ Infrastructure setup complete!"
echo ""
echo "Next Steps:"
echo "  1. Build & push Docker images:"
echo "     gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/nexum/ingestion:latest nexum-backend/ingestion"
echo "     gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/nexum/worker:latest nexum-backend/worker"
echo ""
echo "  2. Deploy Worker first (to get URL):"
echo "     gcloud run deploy nexum-worker \\"
echo "       --image $REGION-docker.pkg.dev/$PROJECT_ID/nexum/worker:latest \\"
echo "       --service-account $SA_EMAIL \\"
echo "       --memory 2Gi --cpu 2 --min-instances 0 --max-instances 5 \\"
echo "       --region $REGION --allow-unauthenticated"
echo ""
echo "  3. Create Pub/Sub push subscription (replace WORKER_URL):"
echo "     WORKER_URL=\$(gcloud run services describe nexum-worker --region $REGION --format 'value(status.url)')"
echo "     gcloud pubsub subscriptions create $SUBSCRIPTION \\"
echo "       --topic $TOPIC \\"
echo "       --push-endpoint \$WORKER_URL/process \\"
echo "       --push-auth-service-account $SA_EMAIL"
echo ""
echo "  4. Deploy Ingestion API:"
echo "     gcloud run deploy nexum-ingestion \\"
echo "       --image $REGION-docker.pkg.dev/$PROJECT_ID/nexum/ingestion:latest \\"
echo "       --service-account $SA_EMAIL \\"
echo "       --memory 512Mi --region $REGION --allow-unauthenticated"
