#!/usr/bin/env bash
# cron_health_check.sh - cron silent fail 検知 (cmd_1443_p09 / H12)
# 毎時 30 分に実行され、shared_context/cron_inventory.md 記載の全 cron ログを
# offset-based scan で検査し、ERROR/FAIL/Traceback を検知したら ntfy で 1 通集約通知する。
#
# 設計原則:
#   - 自身のログ (logs/cron_health_check.log) は scan 対象から除外 (再帰 ntfy 防止)
#   - 1 回の実行で複数 cron のエラーを 1 通の ntfy に集約 (rate limit)
#   - 欠損ログファイルはスキップ (新規 cron で未出力の場合あり)
#   - バイトオフセット追跡で前回 scan 以降の新規追記分のみ検査 (cmd_1468 改修)
#     初回実行時(オフセットなし)は従来通り tail -n 200 でスキャン

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/cron_health_check.log"
NTFY_SCRIPT="$SCRIPT_DIR/scripts/ntfy.sh"
OFFSET_DIR="$SCRIPT_DIR/queue/.flags/cron_health_offsets"
TAIL_LINES_FALLBACK=200

mkdir -p "$(dirname "$LOG_FILE")" "$OFFSET_DIR"

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

# offset_key: ログパスから一意なファイル名を生成
offset_key() {
  echo -n "$1" | md5sum | cut -d' ' -f1
}

# 結果集約バッファ
SUMMARY=""
HIT_COUNT=0

for entry in "${TARGETS[@]}"; do
  id="${entry%%:*}"
  path="${entry#*:}"

  if [ ! -f "$path" ]; then
    continue
  fi

  key=$(offset_key "$path")
  offset_file="$OFFSET_DIR/$key"
  current_size=$(stat -c '%s' "$path" 2>/dev/null || echo 0)

  if [ -f "$offset_file" ]; then
    prev_offset=$(cat "$offset_file" 2>/dev/null || echo 0)
  else
    prev_offset=""
  fi

  # 新規追記分のみを抽出
  if [ -n "$prev_offset" ] && [ "$prev_offset" -gt 0 ] 2>/dev/null; then
    if [ "$current_size" -gt "$prev_offset" ]; then
      new_bytes=$((current_size - prev_offset))
      content=$(dd if="$path" bs=1 skip="$prev_offset" count="$new_bytes" 2>/dev/null)
    elif [ "$current_size" -lt "$prev_offset" ]; then
      # ログがローテされた(小さくなった) → 全件スキャン
      content=$(cat "$path")
    else
      # 変化なし → skip
      echo "$current_size" > "$offset_file"
      continue
    fi
  else
    # 初回: 従来通り tail -n 200
    content=$(tail -n "$TAIL_LINES_FALLBACK" "$path" 2>/dev/null)
  fi

  # pattern 検査
  matches=$(echo "$content" | grep -iE "$PATTERN" | tail -n 3 || true)

  if [ -n "$matches" ]; then
    HIT_COUNT=$((HIT_COUNT + 1))
    first_line=$(echo "$matches" | head -n 1)
    SUMMARY+="[$id] ${first_line:0:120}"$'\n'
  fi

  # offset 更新
  echo "$current_size" > "$offset_file"
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
