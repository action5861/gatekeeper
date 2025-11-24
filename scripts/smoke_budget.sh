#!/usr/bin/env bash

set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8007}"
AUCTION_BASE="${AUCTION_BASE:-http://localhost:8002}"
ADVERTISER_ID="${ADVERTISER_ID:-9}"
TOKEN="${TOKEN:-}"

if [[ -z "${TOKEN}" ]]; then
  echo "[ERROR] TOKEN environment variable is required for authenticated requests." >&2
  exit 1
fi

AUTH_HEADER_VALUE="Bearer ${TOKEN}"

if command -v jq >/dev/null 2>&1; then
  JQ="jq ."
else
  echo "[WARN] jq not found; responses will be shown raw." >&2
  JQ="cat"
fi

DAILY_BUDGET_VALUE="${DAILY_BUDGET:-12345}"
MAX_BID_VALUE="${MAX_BID_PER_KEYWORD:-2500}"
MIN_QUALITY_VALUE="${MIN_QUALITY_SCORE:-55}"

PUT_PAYLOAD=$(cat <<JSON
{
  "dailyBudget": ${DAILY_BUDGET_VALUE},
  "maxBidPerKeyword": ${MAX_BID_VALUE},
  "minQualityScore": ${MIN_QUALITY_VALUE},
  "isEnabled": true
}
JSON
)

echo ">>> [1/3] Updating auto bid settings for advertiser ${ADVERTISER_ID}"
curl -sf -X PUT "${API_BASE}/auto-bid-settings/${ADVERTISER_ID}" \
  -H "Authorization: ${AUTH_HEADER_VALUE}" \
  -H "Content-Type: application/json" \
  -d "${PUT_PAYLOAD}" \
  | ${JQ}

echo ">>> [2/3] Fetching updated auto bid settings"
curl -sf "${API_BASE}/auto-bid-settings/${ADVERTISER_ID}" \
  -H "Authorization: ${AUTH_HEADER_VALUE}" \
  | ${JQ}

echo ">>> [3/3] Triggering auction-service reverse auction (verify _reserve_budget_tx in logs)"
curl -sf -X POST "${AUCTION_BASE}/start" \
  -H "Content-Type: application/json" \
  -d '{"query": "budget smoke test", "quality_score": 60}' \
  | ${JQ}

echo "Smoke test completed. Inspect auction-service logs to confirm budget reservation."

