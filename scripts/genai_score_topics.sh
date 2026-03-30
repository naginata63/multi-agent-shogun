#!/usr/bin/env bash
# genai_score_topics.sh — レポートMDの各見出しにスコアを追記
# 使用方法: bash scripts/genai_score_topics.sh [YYYY-MM-DD]
#
# 出力形式: ## 🤖 [95] Gemini 3.1 Flash Live発表
# スコア基準: config/genai_user_profile.yaml の scoring_weights に基づく

set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DATE_ARG="${1:-}"
DATE_STR="${DATE_ARG:-$(date +%Y-%m-%d)}"

REPORT_FILE="$PROJECT_ROOT/reports/genai_daily/${DATE_STR}.md"
LOG_FILE="$PROJECT_ROOT/logs/genai_daily.log"
PROFILE_FILE="$PROJECT_ROOT/config/genai_user_profile.yaml"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [score_topics] $*" | tee -a "$LOG_FILE"
}

log "=== スコアリング開始 date=$DATE_STR ==="

if [[ ! -f "$REPORT_FILE" ]] || [[ ! -s "$REPORT_FILE" ]]; then
    log "WARN: レポートファイルが存在しない or 空: $REPORT_FILE — スキップ"
    exit 0
fi

if ! command -v claude &>/dev/null; then
    log "ERROR: claude コマンドが見つかりません。スコアリングスキップ"
    exit 1
fi

# スコア付き見出しが既にあれば（[数字] パターン）スキップ
if grep -qP '^## .+\[\d+\]' "$REPORT_FILE" 2>/dev/null || grep -qE '^## .+\[[0-9]+\]' "$REPORT_FILE" 2>/dev/null; then
    log "INFO: スコア付き見出しが既に存在します。スキップ"
    exit 0
fi

PROFILE_CONTENT="$(cat "$PROFILE_FILE")"

# 見出し一覧を抽出（## 以降の文字列）
HEADINGS="$(grep '^## ' "$REPORT_FILE" | sed 's/^## //')"
HEADING_COUNT="$(echo "$HEADINGS" | grep -c . || true)"

if [[ "$HEADING_COUNT" -eq 0 ]]; then
    log "WARN: 見出しが0件。スキップ"
    exit 0
fi

log "スコアリング対象: ${HEADING_COUNT}件"

PROMPT="以下のユーザープロフィールに基づき、各トピックに0〜100の整数スコアを付けよ。

## ユーザープロフィール
${PROFILE_CONTENT}

## スコア基準（各軸のweightはプロフィールのscoring_weightsを参照）
- practical_relevance: Gemini API/Claude API/Claude Code/ffmpeg/動画AI/マルチエージェント等の実務直結度
- technical_novelty: 新しいブレークスルーか既存の改善か
- industry_impact: AI業界全体への影響の大きさ
- cost_impact: API料金変更・無料ツール公開等のコスト影響

興味lowの「政策・資金調達・買収」は低スコアにすること。

## 出力フォーマット（このJSON配列のみを出力せよ。前後に説明文を入れるな）
[
  {\"heading\": \"（元の見出し文字列をそのまま）\", \"score\": 数値},
  ...
]

## スコアリング対象トピック（## 見出し行）
${HEADINGS}"

log "Claude CLIでスコアリング中..."
SCORE_OUTPUT="$(env -u CLAUDECODE claude -p "$PROMPT" --tools "" --dangerously-skip-permissions 2>>"$LOG_FILE" || true)"

if [[ -z "$SCORE_OUTPUT" ]]; then
    log "ERROR: Claude CLI出力が空。スコアリングスキップ"
    exit 1
fi

# JSON配列を抽出してMDを書き換え（Python）
python3 - "$REPORT_FILE" "$SCORE_OUTPUT" <<'PYEOF'
import json
import re
import sys
from pathlib import Path

report_file = Path(sys.argv[1])
raw_output = sys.argv[2]

# コードブロックを除去してJSON配列を探す
text = re.sub(r'```(?:json)?\n?', '', raw_output)
m = re.search(r'\[.*\]', text, re.DOTALL)
if not m:
    print("ERROR: JSON配列が見つかりません", file=sys.stderr)
    sys.exit(1)

try:
    scores = json.loads(m.group())
except json.JSONDecodeError as e:
    print(f"ERROR: JSON parse失敗: {e}", file=sys.stderr)
    sys.exit(1)

# heading → score マップ（正規化して照合）
score_map = {}
for item in scores:
    heading = item.get("heading", "").strip()
    score = int(item.get("score", 0))
    score_map[heading] = score

md = report_file.read_text(encoding="utf-8")
lines = md.splitlines()
new_lines = []
updated = 0

for line in lines:
    if not line.startswith("## "):
        new_lines.append(line)
        continue

    heading = line[3:].strip()

    # スコアが既にある場合はスキップ
    if re.search(r'\[\d+\]', heading):
        new_lines.append(line)
        continue

    # スコアを探す（完全一致 → 部分一致）
    score = score_map.get(heading)
    if score is None:
        for h, s in score_map.items():
            if heading in h or h in heading:
                score = s
                break

    if score is None:
        new_lines.append(line)
        continue

    # 絵文字プレフィックスと本文を分離して [score] を挿入
    # 例: "🤖 Gemini 3.1..." → "🤖 [95] Gemini 3.1..."
    m = re.match(r'^((?:[^\w\d\u3040-\u9FFF]+))(.*)', heading)
    if m:
        emoji_part = m.group(1)
        title_part = m.group(2).strip()
        new_heading = f"{emoji_part}[{score}] {title_part}"
    else:
        new_heading = f"[{score}] {heading}"

    new_lines.append(f"## {new_heading}")
    updated += 1

report_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print(f"Done: {updated}/{len([l for l in lines if l.startswith('## ')])} 件にスコアを付与")
PYEOF

STATUS=$?
if [[ $STATUS -eq 0 ]]; then
    log "=== スコアリング完了 ==="
else
    log "ERROR: MD書き換え失敗 (exit=$STATUS)"
    exit 1
fi
