#!/bin/bash
# GCP課金確認スクリプト
# 使い方: bash scripts/gcp_billing_check.sh [YYYYMM]
# 例: bash scripts/gcp_billing_check.sh 202603

export PATH="$HOME/google-cloud-sdk/bin:$PATH"

PROJECT="dozlesha-mainichi-kirinuki"
DATASET="billing_export"
MONTH="${1:-$(date +%Y%m)}"

echo "=== GCP課金確認 (${MONTH}) ==="
echo "プロジェクト: $PROJECT"
echo ""

# データセット存在確認
if ! bq ls "$DATASET" &>/dev/null; then
  echo "❌ データセット '$DATASET' が見つかりません"
  echo "まずbigquery billing exportを設定してください"
  exit 1
fi

# テーブル存在確認
TABLE_COUNT=$(bq ls "${PROJECT}:${DATASET}" 2>/dev/null | grep -c "gcp_billing")
if [ -z "$TABLE_COUNT" ] || [ "$TABLE_COUNT" -eq 0 ]; then
  echo "⏳ Billing Exportのテーブルがまだありません"
  echo ""
  echo "BigQuery Export設定が必要です:"
  echo "1. https://console.cloud.google.com/billing"
  echo "2. 請求先アカウント(01DE83-CDB694-CFA149)を選択"
  echo "3. エクスポート → BigQueryへのエクスポート → 編集"
  echo "4. プロジェクト: $PROJECT, データセット: $DATASET"
  echo "5. 標準使用量のコストにチェック → 保存"
  echo ""
  echo "設定後、データ反映まで最大24時間かかります"
  exit 0
fi

# サービス別課金クエリ
echo "--- サービス別課金額 ---"
bq query --use_legacy_sql=false \
  --project_id="$PROJECT" \
  "SELECT
    service.description AS service,
    ROUND(SUM(cost), 2) AS total_cost_jpy,
    COUNT(*) AS record_count
  FROM \`${PROJECT}.${DATASET}.gcp_billing_export_v1*\`
  WHERE invoice.month = '${MONTH}'
  GROUP BY service.description
  ORDER BY total_cost_jpy DESC
  LIMIT 20" 2>&1

echo ""
echo "--- 月合計 ---"
bq query --use_legacy_sql=false \
  --project_id="$PROJECT" \
  "SELECT
    ROUND(SUM(cost), 2) AS total_cost,
    currency
  FROM \`${PROJECT}.${DATASET}.gcp_billing_export_v1*\`
  WHERE invoice.month = '${MONTH}'
  GROUP BY currency" 2>&1

echo ""
echo "--- Gemini API課金 ---"
bq query --use_legacy_sql=false \
  --project_id="$PROJECT" \
  "SELECT
    service.description AS service,
    sku.description AS sku,
    ROUND(SUM(cost), 2) AS cost,
    currency
  FROM \`${PROJECT}.${DATASET}.gcp_billing_export_v1*\`
  WHERE invoice.month = '${MONTH}'
    AND (LOWER(service.description) LIKE '%gemini%'
      OR LOWER(service.description) LIKE '%vertex%'
      OR LOWER(sku.description) LIKE '%gemini%')
  GROUP BY service.description, sku.description, currency
  ORDER BY cost DESC" 2>&1
