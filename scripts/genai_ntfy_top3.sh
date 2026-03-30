#!/usr/bin/env bash
# genai_ntfy_top3.sh — 生成AI日報からTop3をntfyでスマホ配信
# 使用方法: bash scripts/genai_ntfy_top3.sh [YYYY-MM-DD]
#
# P1: ntfy Top3サマリー配信 (gunshi_report_genai_viewer_improvement.yaml P1)
# P2: パーソナライズスコアリング (config/genai_user_profile.yaml を参照)

set -uo pipefail

export PATH="$HOME/.local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DATE_ARG="${1:-}"
if [[ -z "$DATE_ARG" ]]; then
    DATE_STR="$(date +%Y-%m-%d)"
else
    DATE_STR="$DATE_ARG"
fi

REPORT_FILE="$PROJECT_ROOT/reports/genai_daily/${DATE_STR}.md"
LOG_FILE="$PROJECT_ROOT/logs/genai_daily.log"
PROFILE_FILE="$PROJECT_ROOT/config/genai_user_profile.yaml"
NTFY_SCRIPT="$SCRIPT_DIR/ntfy.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ntfy_top3] $*" | tee -a "$LOG_FILE"
}

log "=== Top3配信開始 date=$DATE_STR ==="

# レポートファイル存在確認
if [[ ! -f "$REPORT_FILE" ]] || [[ ! -s "$REPORT_FILE" ]]; then
    log "WARN: レポートファイルが存在しない or 空: $REPORT_FILE — Top3配信スキップ"
    exit 0
fi

# claude CLI確認
if ! command -v claude &>/dev/null; then
    log "ERROR: claude コマンドが見つかりません。Top3配信スキップ"
    exit 1
fi

# プロフィール読み込み（ファイルがない場合はデフォルト）
if [[ -f "$PROFILE_FILE" ]]; then
    PROFILE_CONTENT="$(cat "$PROFILE_FILE")"
else
    PROFILE_CONTENT="role: YouTubeチャンネル運営 + AI開発者, interests.high: [Gemini API, Claude API, ffmpeg, 動画AI, マルチエージェント]"
fi

REPORT_CONTENT="$(cat "$REPORT_FILE")"
MONTH_DAY="$(date -d "$DATE_STR" '+%-m/%-d' 2>/dev/null || date '+%-m/%-d')"

PROMPT="以下のレポートから、このユーザーに最も価値のある3件を選び、指定フォーマットで出力せよ。

## ユーザープロフィール (config/genai_user_profile.yaml)
${PROFILE_CONTENT}

## 選定基準（優先順）
1. 実務直結度 (40%): Gemini API/Claude API変更、ffmpeg新機能、動画AI、Claude Code更新
2. 技術的新規性 (25%): ブレークスルー > 既存改善
3. 業界影響度 (20%): 大きいほど優先
4. コスト影響 (15%): API料金変更・無料ツール公開

興味lowの「政策・資金調達・買収」は他に有力候補がない限り選ばないこと。

## 出力フォーマット（このフォーマット以外の文字を一切出力するな）
📰 今朝のAI Top3 (${MONTH_DAY})

1⃣ [タイトル（20字以内）] — [なぜ殿に重要か（30字以内）]

2⃣ [タイトル（20字以内）] — [なぜ殿に重要か（30字以内）]

3⃣ [タイトル（20字以内）] — [なぜ殿に重要か（30字以内）]

全文: http://localhost:8580/

## レポート
${REPORT_CONTENT}"

log "Claude CLIでTop3選定中..."
TOP3_MSG="$(env -u CLAUDECODE claude -p "$PROMPT" --tools "" --dangerously-skip-permissions 2>>"$LOG_FILE" || true)"

if [[ -z "$TOP3_MSG" ]]; then
    log "ERROR: Claude CLI出力が空。Top3配信スキップ"
    exit 1
fi

# 先頭の思考テキスト除去（📰 より前の行を削除）
TOP3_MSG="$(echo "$TOP3_MSG" | sed -n '/^📰/,$p')"

if [[ -z "$TOP3_MSG" ]]; then
    log "ERROR: フォーマット解析失敗（📰 が見つからない）。Top3配信スキップ"
    exit 1
fi

log "ntfy配信: $(echo "$TOP3_MSG" | head -1)"
bash "$NTFY_SCRIPT" "$TOP3_MSG"

# Discord Bot連携: queue/discord_pending.json に書き出す
DISCORD_PENDING="$PROJECT_ROOT/queue/discord_pending.json"
QUEUE_DIR="$PROJECT_ROOT/queue"
mkdir -p "$QUEUE_DIR"
cat > "$DISCORD_PENDING" <<DISCORD_EOF
{
  "date": "${DATE_STR}",
  "text": $(echo "$TOP3_MSG" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))"),
  "posted": false
}
DISCORD_EOF
log "Discord pending書き出し: $DISCORD_PENDING"

log "=== Top3配信完了 ==="
