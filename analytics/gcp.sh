#!/usr/bin/env bash
# One-time setup, run in Google Cloud Shell: a read-only GA4 reader that GitHub Actions
# can use WITHOUT any key file (Workload Identity Federation, limited to this repo).
set -e
REPO="justinbclose/portfolio"
P=jbc-portfolio-stats
gcloud projects describe "$P" >/dev/null 2>&1 || gcloud projects create "$P" --name="Portfolio stats" || { P="jbc-portfolio-stats-$RANDOM"; gcloud projects create "$P" --name="Portfolio stats"; }
gcloud config set project "$P" >/dev/null
gcloud services enable analyticsdata.googleapis.com iamcredentials.googleapis.com sts.googleapis.com iam.googleapis.com
SA="ga4-reader@$P.iam.gserviceaccount.com"
gcloud iam service-accounts describe "$SA" >/dev/null 2>&1 || gcloud iam service-accounts create ga4-reader --display-name="GA4 reader (portfolio stats)"
gcloud iam workload-identity-pools describe github --location=global >/dev/null 2>&1 || gcloud iam workload-identity-pools create github --location=global --display-name="GitHub Actions"
gcloud iam workload-identity-pools providers describe portfolio --location=global --workload-identity-pool=github >/dev/null 2>&1 || \
gcloud iam workload-identity-pools providers create-oidc portfolio --location=global --workload-identity-pool=github \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='$REPO'"
PN=$(gcloud projects describe "$P" --format='value(projectNumber)')
gcloud iam service-accounts add-iam-policy-binding "$SA" --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PN/locations/global/workloadIdentityPools/github/attribute.repository/$REPO" >/dev/null
echo
echo "=== DONE ==="
echo "SA=$SA"
echo "PROVIDER=projects/$PN/locations/global/workloadIdentityPools/github/providers/portfolio"
