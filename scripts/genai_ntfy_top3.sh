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

以下のカテゴリはTop3に選ばないこと（他に有力候補がない限り）:
- 政策・資金調達・買収
- GPU/ハードウェアのベンチマーク比較
- 学術論文の数学的解説

## 出力フォーマット（このフォーマット以外の文字を一切出力するな）
📰 今朝のAI Top3 (${MONTH_DAY})

1⃣ [タイトル（20字以内）] — [なぜ殿に重要か（30字以内）]

2⃣ [タイトル（20字以内）] — [なぜ殿に重要か（30字以内）]

3⃣ [タイトル（20字以内）] — [なぜ殿に重要か（30字以内）]

全文: https://genai-daily.pages.dev/
#SCORES:★N,★N,★N  ← 各記事の★スコア（1〜5）をレポートから読み取り、1⃣2⃣3⃣の順で記入

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

# 2段階通知閾値: #SCORES行を解析してスコア判断
SCORES_LINE="$(echo "$TOP3_MSG" | grep '^#SCORES:' || true)"
TOP3_MSG_CLEAN="$(echo "$TOP3_MSG" | grep -v '^#SCORES:')"

MAX_STARS=0
if [[ -n "$SCORES_LINE" ]]; then
    while IFS= read -r star_num; do
        [[ "$star_num" =~ ^[0-9]+$ ]] && [[ "$star_num" -gt "$MAX_STARS" ]] && MAX_STARS="$star_num"
    done < <(echo "$SCORES_LINE" | grep -oP '★\K[0-9]+')
else
    # #SCORES行なし → フォールバック: ntfy送信（旧来の動作）
    log "WARN: #SCORES行が見つからない。フォールバック: ntfy送信"
    MAX_STARS=4
fi

if [[ "$MAX_STARS" -ge 4 ]]; then
    log "ntfy配信 (★${MAX_STARS} >= ★4): $(echo "$TOP3_MSG_CLEAN" | head -1)"
    bash "$NTFY_SCRIPT" "$TOP3_MSG_CLEAN"
    NOTIFY_DISCORD=true
elif [[ "$MAX_STARS" -eq 3 ]]; then
    log "ntfyスキップ (★3: Discordのみ)"
    NOTIFY_DISCORD=true
else
    log "ntfyスキップ (★${MAX_STARS} <= ★2: Webビューアのみ)"
    NOTIFY_DISCORD=false
fi

# Discord Bot連携: queue/discord_pending.json に書き出す（topics全件含む）
DISCORD_PENDING="$PROJECT_ROOT/queue/discord_pending.json"
QUEUE_DIR="$PROJECT_ROOT/queue"
mkdir -p "$QUEUE_DIR"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"
TOPICS_JSON="$("$VENV_PYTHON" "$SCRIPT_DIR/genai_parse_report.py" "$DATE_STR" 2>>"$LOG_FILE" || echo "[]")"
TOP3_JSON="$(echo "$TOP3_MSG_CLEAN" | "$VENV_PYTHON" -c "import json,sys; print(json.dumps(sys.stdin.read()))")"
"$VENV_PYTHON" - <<PYEOF
import json
topics = $TOPICS_JSON
pending = {
    "date": "$DATE_STR",
    "text": $TOP3_JSON,
    "topics": topics,
    "posted": False,
    "notify_discord": $([[ "$NOTIFY_DISCORD" == "true" ]] && echo "True" || echo "False"),
}
import tempfile, os
tmpfd, tmppath = tempfile.mkstemp(suffix=".tmp", dir=os.path.dirname("$DISCORD_PENDING"))
try:
    with os.fdopen(tmpfd, "w", encoding="utf-8") as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)
    os.rename(tmppath, "$DISCORD_PENDING")
except:
    os.unlink(tmppath) if os.path.exists(tmppath) else None
    raise
PYEOF
log "Discord pending書き出し: $DISCORD_PENDING (topics=$(echo "$TOPICS_JSON" | "$VENV_PYTHON" -c 'import json,sys; print(len(json.load(sys.stdin)))' 2>/dev/null || echo '?')件)"

log "=== Top3配信完了 ==="
