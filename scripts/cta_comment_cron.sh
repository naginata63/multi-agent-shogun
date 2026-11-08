#!/bin/bash
# cta_comment_cron.sh — CTA自動コメント投稿 cron スクリプト
# cron: 5 12 * * * bash /home/murakami/multi-agent-shogun/scripts/cta_comment_cron.sh >> /home/murakami/multi-agent-shogun/logs/cta_comment.log 2>&1
#
# 処理: YouTube Data APIでチャンネルの公開済み動画を検索 → 自コメント未投稿の動画にCTA投稿

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$REPO_DIR/scripts/cta_comment.py"
LOG_DIR="$REPO_DIR/logs"

# ログディレクトリ作成（存在しない場合）
mkdir -p "$LOG_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] cta_comment_cron.sh 開始"

python3 "$SCRIPT"

# 元動画コメント(殿 2026-11-08): CTA のあとに、新しい動画から1日30本まで「📌 元動画：題+URL」を付ける
python3 "$REPO_DIR/scripts/source_comment.py" --max 30 || echo "[$(date '+%Y-%m-%d %H:%M:%S')] source_comment.py 失敗"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] cta_comment_cron.sh 完了"
