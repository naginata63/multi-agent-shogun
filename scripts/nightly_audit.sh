#!/usr/bin/env bash
# 夜間矛盾検出 — 毎晩2:00にcrontabから実行
# カテゴリをローテーションして軍師に矛盾検出タスクを振る

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# === cron_inventory ↔ crontab drift 検知 (cmd_1443_p09 / H12) ===
# shared_context/crontab.snapshot.txt と現状の crontab -l を diff し、
# 差分があれば ntfy で警告。cron 追加/削除時の inventory 更新漏れを検知する。
_check_cron_drift() {
  local snapshot="$SCRIPT_DIR/shared_context/crontab.snapshot.txt"
  local current
  current=$(mktemp)
  crontab -l > "$current" 2>/dev/null || { rm -f "$current"; return 0; }

  if [ -f "$snapshot" ]; then
    # コメント行・空行を無視した実効 diff
    if ! diff <(grep -vE '^\s*#|^\s*$' "$snapshot") <(grep -vE '^\s*#|^\s*$' "$current") > /dev/null 2>&1; then
      local msg="⚠️ cron drift 検知: crontab.snapshot.txt と実 crontab -l が乖離。shared_context/cron_inventory.md も併せて更新要。"
      if [ -x "$SCRIPT_DIR/scripts/ntfy.sh" ]; then
        bash "$SCRIPT_DIR/scripts/ntfy.sh" "$msg" || true
      fi
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" >> "$SCRIPT_DIR/logs/nightly_audit.log"
    fi
  fi
  rm -f "$current"
}
_check_cron_drift

DOW=$(date +%u)  # 1=月, 2=火, ..., 7=日

case $DOW in
  1|4) CATEGORY="STTパイプライン（vocal_stt_pipeline.py, stt_merge.py, speaker_id系, 成果物）" ;;
  2|5) CATEGORY="動画制作（main.py, make_expression_shorts.py, Remotion, vertical_convert.py, make_shorts系）" ;;
  3|6) CATEGORY="インフラ（inbox_write/watcher, ntfy, cron, agent管理系, context_monitor等）" ;;
  7)   CATEGORY="YouTube/外部連携（youtube_uploader.py, downloader.py, note系, API連携）" ;;
esac

bash "$SCRIPT_DIR/scripts/inbox_write.sh" karo \
  "【夜間矛盾検出・自動発令】本日のカテゴリ: ${CATEGORY}。軍師に矛盾検出タスクを振れ。cmd_828と同じ形式で。テストを書くな。コードを修正するな。読んで報告するだけ。朝までにダッシュボードに結果を掲載せよ。" \
  nightly_audit shogun

# === dashboard_lifecycle (cmd_1443_p02 / H2 拡張) ===
# dashboard.md 🚨解決済み残骸の自動クリーン + MCPダッシュボード残骸検出→家老通知
bash "$SCRIPT_DIR/scripts/dashboard_lifecycle.sh" >> "$SCRIPT_DIR/logs/dashboard_lifecycle.log" 2>&1 || \
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] dashboard_lifecycle failed (continuing)" >> "$SCRIPT_DIR/logs/nightly_audit.log"
