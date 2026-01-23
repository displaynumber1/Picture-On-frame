#!/usr/bin/env bash
set -euo pipefail

# Required:
#   API_URL=https://api.yourdomain.com
#   ACCESS_TOKEN=eyJhbGci...
#
# Optional:
#   MIDTRANS_SERVER_KEY=...
#   TEST_USER_ID=...
#   TEST_IMAGE_URL=https://...
#
# Usage:
#   API_URL=... ACCESS_TOKEN=... bash deploy/smoke-test.sh

API_URL="${API_URL:-}"
ACCESS_TOKEN="${ACCESS_TOKEN:-}"
MIDTRANS_SERVER_KEY="${MIDTRANS_SERVER_KEY:-}"
TEST_USER_ID="${TEST_USER_ID:-}"
TEST_IMAGE_URL="${TEST_IMAGE_URL:-}"

if [[ -z "$API_URL" || -z "$ACCESS_TOKEN" ]]; then
  echo "Missing API_URL or ACCESS_TOKEN"
  exit 1
fi

echo "== Auth check =="
curl -s -X POST "$API_URL/api/auth/ensure-access" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | cat
echo ""

echo "== Billing status =="
curl -s "$API_URL/api/billing/status" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | cat
echo ""

echo "== Billing history (latest 5) =="
curl -s "$API_URL/api/billing/history?limit=5" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | cat
echo ""

if [[ -n "$MIDTRANS_SERVER_KEY" && -n "$TEST_USER_ID" ]]; then
  echo "== Webhook simulation (subscription) =="
  ORDER_ID="sub-${TEST_USER_ID}-smoketest"
  GROSS_AMOUNT="49000"
  STATUS_CODE="200"
  SIGNATURE=$(printf "%s" "${ORDER_ID}${STATUS_CODE}${GROSS_AMOUNT}${MIDTRANS_SERVER_KEY}" | openssl dgst -sha512 -hex | awk '{print $2}')

  curl -s -X POST "$API_URL/api/billing/webhook" \
    -H "Content-Type: application/json" \
    -d "{
      \"transaction_status\": \"settlement\",
      \"order_id\": \"${ORDER_ID}\",
      \"gross_amount\": \"${GROSS_AMOUNT}\",
      \"status_code\": \"${STATUS_CODE}\",
      \"signature_key\": \"${SIGNATURE}\",
      \"fraud_status\": \"accept\",
      \"custom_field1\": \"${TEST_USER_ID}\",
      \"custom_field2\": \"pro_monthly\",
      \"custom_field3\": \"subscription\"
    }" | cat
  echo ""
fi

if [[ -n "$TEST_IMAGE_URL" ]]; then
  echo "== FFmpeg job (generate video from image) =="
  curl -s -X POST "$API_URL/api/generate-video" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"test video generation\",
      \"image_url\": \"${TEST_IMAGE_URL}\"
    }" | cat
  echo ""
fi

echo "Done."
