#!/usr/bin/env bash
# cron_health_check.sh - cron silent fail 検知 (cmd_1443_p09 / H12)
# 毎時 30 分に実行され、shared_context/cron_inventory.md 記載の全 cron ログを
# tail→grep で検査し、ERROR/FAIL/Traceback を検知したら ntfy で 1 通集約通知する。
#
# 設計原則:
#   - 自身のログ (logs/cron_health_check.log) は scan 対象から除外 (再帰 ntfy 防止)
#   - 1 回の実行で複数 cron のエラーを 1 通の ntfy に集約 (rate limit)
#   - 欠損ログファイルはスキップ (新規 cron で未出力の場合あり)
#   - 直近 1 時間分の末尾のみ検査 (tail -n 200) で過去エラーの再通知を防ぐ

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/cron_health_check.log"
NTFY_SCRIPT="$SCRIPT_DIR/scripts/ntfy.sh"
TAIL_LINES=200

mkdir -p "$(dirname "$LOG_FILE")"

# 検査対象ログファイル一覧
# cron_inventory.md の「ログ」フィールドと同期すること
# C11 (自身) は意図的に除外 → 再帰通知を防ぐ
TARGETS=(
  "C01:$SCRIPT_DIR/logs/genai_daily.log"
  "C02:$SCRIPT_DIR/logs/semantic_update.log"
  "C03:$SCRIPT_DIR/logs/dedup.log"
  "C04:$SCRIPT_DIR/projects/dozle_kirinuki/analytics/cron.log"
  "C05:$SCRIPT_DIR/logs/nightly_audit.log"
  "C06:$SCRIPT_DIR/logs/orphan_chrome_cleanup.log"
  "C07:$SCRIPT_DIR/logs/cta_comment.log"
  "C08:$SCRIPT_DIR/logs/mcp_experiment_cron.log"
  "C09:$SCRIPT_DIR/logs/slim_yaml_cron.log"
  "C10:$SCRIPT_DIR/logs/backup_full.log"
  "C14:$SCRIPT_DIR/logs/skill_inventory.log"
)

# パターン: 単語境界付き・大文字小文字無視。
# - 単語境界 (\b) で "0FAIL" / "9PASS" のような数字連結を除外
# - 大文字小文字無視 (-i) で rsync 等の小文字 "error" も検出
# - 例: "0FAIL" → \b 前後なしで不一致、"rsync error:" → \b ある両端で一致
PATTERN='\bERROR\b|\bFAIL(ED)?\b|\bFATAL\b|\bException\b|\bTraceback\b|\bCRITICAL\b'

# 結果集約バッファ
SUMMARY=""
HIT_COUNT=0

for entry in "${TARGETS[@]}"; do
  id="${entry%%:*}"
  path="${entry#*:}"

  if [ ! -f "$path" ]; then
    # ログ不在はスキップ (新規 cron で未出力の場合あり)
    continue
  fi

  # 直近 TAIL_LINES 行を検査 (単語境界 + 大文字小文字無視)
  matches=$(tail -n "$TAIL_LINES" "$path" 2>/dev/null | grep -iE "$PATTERN" | tail -n 3 || true)

  if [ -n "$matches" ]; then
    HIT_COUNT=$((HIT_COUNT + 1))
    # 各 hit は 1 cron 最大 3 行まで要約
    first_line=$(echo "$matches" | head -n 1)
    SUMMARY+="[$id] ${first_line:0:120}"$'\n'
  fi
done

# 自身のログに常に記録 (成功/失敗問わず)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] checked=${#TARGETS[@]} hit=$HIT_COUNT" >> "$LOG_FILE"

if [ "$HIT_COUNT" -gt 0 ]; then
  # 1 通集約通知
  MSG="⚠️ cron異常検知 (${HIT_COUNT}件): "$'\n'"$SUMMARY"
  if [ -x "$NTFY_SCRIPT" ]; then
    bash "$NTFY_SCRIPT" "$MSG" || echo "[$TIMESTAMP] ntfy send failed" >> "$LOG_FILE"
  else
    echo "[$TIMESTAMP] NTFY_SCRIPT missing: $NTFY_SCRIPT" >> "$LOG_FILE"
  fi
  # ログにも詳細記録
  echo "[$TIMESTAMP] HIT DETAIL:" >> "$LOG_FILE"
  echo "$SUMMARY" >> "$LOG_FILE"
fi

# ログローテ (1000 行超で末尾 500 行を残す)
if [ -f "$LOG_FILE" ]; then
  lines=$(wc -l < "$LOG_FILE")
  if [ "$lines" -gt 1000 ]; then
    tail -n 500 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
  fi
fi

exit 0
