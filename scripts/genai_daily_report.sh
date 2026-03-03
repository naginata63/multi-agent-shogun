#!/usr/bin/env bash
# 生成AI 技術トレンド日報 — 自動生成スクリプト
# 使用方法: bash scripts/genai_daily_report.sh [YYYY-MM-DD]
#
# モード切り替え (環境変数):
#   GENAI_MODE=claude (デフォルト): claude CLIを使ってWeb検索+日本語レポート生成
#   GENAI_MODE=rss   (フォールバック): Python RSSフェッチを使用
#
# cron設定例（claudeモード、推奨）:
#   0 7 * * * cd /home/murakami/multi-agent-shogun && bash scripts/genai_daily_report.sh >> logs/genai_daily.log 2>&1
#
# cron設定例（RSSフォールバックモード）:
#   0 7 * * * cd /home/murakami/multi-agent-shogun && GENAI_MODE=rss bash scripts/genai_daily_report.sh >> logs/genai_daily.log 2>&1

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 日付引数（省略時は今日）
DATE_ARG="${1:-}"
if [[ -z "$DATE_ARG" ]]; then
    DATE_STR="$(date +%Y-%m-%d)"
else
    DATE_STR="$DATE_ARG"
fi

# モード設定（デフォルト: claude）
GENAI_MODE="${GENAI_MODE:-claude}"

OUTPUT_DIR="$PROJECT_ROOT/reports/genai_daily"
OUTPUT_FILE="$OUTPUT_DIR/${DATE_STR}.md"
LOG_FILE="$PROJECT_ROOT/logs/genai_daily.log"
FETCH_SCRIPT="$SCRIPT_DIR/genai_daily_fetch.py"

# ディレクトリ作成
mkdir -p "$OUTPUT_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=== 生成AI日報生成開始 date=$DATE_STR mode=$GENAI_MODE ==="

# ---- モード1: claude -p 方式 ----------------------------------------
if [[ "$GENAI_MODE" == "claude" ]]; then
    if ! command -v claude &>/dev/null; then
        log "WARN: claude コマンドが見つかりません。RSSモードにフォールバック"
        GENAI_MODE="rss"
    else
        TIME_STR="$(date '+%H:%M JST')"
        PROMPT="今日(${DATE_STR})の生成AI技術トレンドを調査し、日本語で詳細レポートを作成してください。

■ 収集対象:
- 新モデル発表（Claude, GPT, Gemini, Llama, Mistral, DeepSeek, Grok等）
- 主要論文・ベンチマーク（arXiv cs.AI/cs.CL等）
- API変更・価格改定（Anthropic, OpenAI, Google, Azure等）
- 注目OSSツール（HuggingFace, GitHub等）
- 主要プレイヤー動向（買収・提携・資金調達等）
- 日本語サイト優先（ITmedia AI+、GIGAZINE、Publickey、ASCII.jp等の記事があれば必ず含める）
- 日本市場動向（NTT、ソフトバンク、サイバーエージェント、富士通、NEC、LINE等の国内企業の生成AI取り組み）
- 国内規制・政策動向（内閣府AI戦略、総務省・経産省のガイドライン等）

■ 選定基準（重要 — 必ず守ること）:
0. 除外基準（最優先）: 以下は除外すること:
   - AirPods、iPad、iPhone、Apple Watch等のApple消費者製品ニュース（AI機能なしの場合）
   - 一般的なスマートフォン・タブレット・家電の発売情報（AI技術の採用がメインでない場合）
   - ゲーム・エンタメニュース（AIが核心でないもの）
   - 株価・決算情報（AI技術の具体的な進展がないもの）
1. 速報性: 24時間以内の新規情報を最優先。古い情報は含めない。
2. 影響範囲: 業界全体に影響するものを上位に。一社内の軽微な更新は下位または除外。
3. 技術的新規性: 既知技術の改善よりブレークスルーを優先。
4. 信頼性: 公式ブログ・論文・実績あるメディアを一次ソースとして優先。
   未確認の噂・憶測は「⚠️未確認」として明記するか除外。
5. 日本語ソース最優先（必須）:
   - 日本語の記事・情報源が存在する場合は、英語記事より必ず優先して取り上げること。
   - ITmedia AI+、GIGAZINE、Publickey、ASCII.jp、日経XTECH、ZDNet Japan等から
     最低3件の記事を含めること。
   - 日本市場・日本企業（NTT、ソフトバンク、サイバーエージェント、富士通、NEC、LINE等）
     の生成AI取り組みを少なくとも1トピック含めること。
   - 日本語ソースが見つからない場合のみ、英語ソースを使用すること。

■ 出力形式（厳守）:
# 生成AI 技術トレンド日報
**日付**: ${DATE_STR}
**生成日時**: ${TIME_STR}
**トピック数**: N件

---

## [カテゴリアイコン] トピックタイトル（日本語）

要約（日本語、2-3行。具体的な数値・モデル名を含めること）

**ソース**: [メディア名 / ブログ名](URL)

---

カテゴリアイコン: 🤖新モデル 📄論文 💰API価格 🛠️OSS 📢動向
最低5件（できれば8件以上）。重要度・速報性の高い順。
出力順序: ①日本語ソースの記事（重要度順）を先に、②英語ソースの記事（重要度順）を後に配置すること。
日本語記事と英語記事を混在させてはならない。
各トピックに必ず実在するソースURLを付けること。URLは推測しない。"

        log "claudeモード: Web検索+日本語レポート生成を開始..."
        if env -u CLAUDECODE claude -p "$PROMPT" > "$OUTPUT_FILE" 2>> "$LOG_FILE"; then
            log "claude コマンド完了"
        else
            log "WARN: claude コマンドが失敗しました（終了コード $?）。RSSモードにフォールバック"
            GENAI_MODE="rss"
        fi

        # 出力が空の場合もフォールバック
        if [[ ! -s "$OUTPUT_FILE" ]]; then
            log "WARN: claude出力が空です。RSSモードにフォールバック"
            GENAI_MODE="rss"
        fi
    fi
fi

# ---- モード2: Python RSS フォールバック ----------------------------
if [[ "$GENAI_MODE" == "rss" ]]; then
    if ! command -v python3 &>/dev/null; then
        log "ERROR: python3 が見つかりません"
        exit 1
    fi

    log "RSSモード: Pythonスクリプト呼び出し中..."
    python3 "$FETCH_SCRIPT" "$DATE_STR" "$OUTPUT_FILE" 2>> "$LOG_FILE"

    # 英語見出し和訳ステップ（claude CLI が利用可能な場合のみ）
    if command -v claude &>/dev/null && [[ -s "$OUTPUT_FILE" ]]; then
        log "RSSレポートの英語見出しを和訳中..."
        TRANSLATE_PROMPT="以下のmarkdownレポートの## 見出し行のうち、英語タイトルのみを日本語に翻訳してください。日本語のタイトルはそのままにしてください。見出し以外の行（要約・ソース行・空行・---）は一切変更しないでください。レポート全文をそのまま出力してください。

---

$(cat "$OUTPUT_FILE")"
        TRANSLATED="$(env -u CLAUDECODE claude -p "$TRANSLATE_PROMPT" 2>/dev/null)"
        if [[ -n "$TRANSLATED" ]]; then
            echo "$TRANSLATED" > "$OUTPUT_FILE"
            log "英語見出し和訳完了"
        else
            log "WARN: 和訳失敗。英語見出しのまま継続"
        fi
    fi
fi

# ---- 完了確認 -------------------------------------------------------
if [[ -f "$OUTPUT_FILE" ]] && [[ -s "$OUTPUT_FILE" ]]; then
    LINES="$(wc -l < "$OUTPUT_FILE")"
    # URL死活確認（オプション、失敗しても続行）
    if [[ -f "$OUTPUT_FILE" ]]; then
        log "URL死活確認を開始..."
        python3 "$SCRIPT_DIR/genai_check_urls.py" "$OUTPUT_FILE" 2>> "$LOG_FILE" || true
        log "URL死活確認完了"
    fi
    log "SUCCESS: レポート生成完了 — $OUTPUT_FILE ($LINES 行)"
else
    log "ERROR: 出力ファイルが生成されませんでした: $OUTPUT_FILE"
    exit 1
fi

log "=== 完了 ==="
