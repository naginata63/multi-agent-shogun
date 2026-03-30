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

# cron環境でもclaudeが見つかるようにPATHを補完
export PATH="$HOME/.local/bin:$PATH"
# cron環境でもGEMINI_API_KEYを取得
GEMINI_API_KEY="${GEMINI_API_KEY:-$(grep -E '^export GEMINI_API_KEY=' ~/.bashrc 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' || true)}"
export GEMINI_API_KEY

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
CACHE_FILE="$OUTPUT_DIR/.title_cache.json"
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

        # 昨日のトピック一覧をキャッシュから取得（P3: 日跨ぎ重複排除）
        YESTERDAY_STR="$(date -d 'yesterday' +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d 2>/dev/null || true)"
        YESTERDAY_TOPICS=""
        if [[ -f "$CACHE_FILE" ]] && [[ -n "$YESTERDAY_STR" ]]; then
            YESTERDAY_TOPICS="$(python3 -c "
import json, sys
try:
    with open('$CACHE_FILE') as f:
        cache = json.load(f)
    titles = cache.get('$YESTERDAY_STR', [])
    if titles:
        print('■ 重複排除（昨日のトピック — 以下と同一・類似のニュースは除外すること）:')
        for t in titles[:20]:
            print(f'  - {t}')
except:
    pass
" 2>/dev/null || true)"
        fi
        [[ -n "$YESTERDAY_TOPICS" ]] && log "昨日のトピック${YESTERDAY_STR}を重複排除用にロード済み"

        PROMPT="今日(${DATE_STR})の生成AI技術トレンドを調査し、日本語で詳細レポートを作成してください。

■ 収集対象:
- 新モデル発表（Claude, GPT, Gemini, Llama, Mistral, DeepSeek, Grok等）
- 主要論文・ベンチマーク（arXiv cs.AI/cs.CL等）
- API変更・価格改定（Anthropic, OpenAI, Google, Azure等）
- 注目OSSツール（HuggingFace, GitHub等）
- 主要プレイヤー動向（買収・提携・資金調達等）
- 日本語サイト優先（ITmedia AI+、GIGAZINE、Publickey、ASCII.jp等の記事があれば必ず含める）
- 日本語個人ブログ・技術記事（note, Zenn, Qiita等）— 実践的な体験談・独自の知見がある記事を優先。ニュースの転載・まとめだけの記事は除外
- 日本市場動向（NTT、ソフトバンク、サイバーエージェント、富士通、NEC、LINE等の国内企業の生成AI取り組み）
- 国内規制・政策動向（内閣府AI戦略、総務省・経産省のガイドライン等）

${YESTERDAY_TOPICS}

■ 選定基準（重要 — 必ず守ること）:
0. 除外基準（最優先）: 以下は除外すること:
   - AirPods、iPad、iPhone、Apple Watch等のApple消費者製品ニュース（AI機能なしの場合）
   - 一般的なスマートフォン・タブレット・家電の発売情報（AI技術の採用がメインでない場合）
   - ゲーム・エンタメニュース（AIが核心でないもの）
   - 株価・決算情報（AI技術の具体的な進展がないもの）
1. 速報性（最重要）: 直近3日以内に公開された記事のみ。4日以上前の記事は絶対に含めるな。「3月5日」の記事を「3月30日」のレポートに入れるのは禁止。記事の公開日を必ず確認すること。
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
6. 英語ソースの扱い（必須）:
   - 重要な英語ソースの記事も必ず含めること。英語記事を除外してはならない。
   - 英語ソースの記事は見出し・要約を全て日本語に翻訳して掲載すること。
   - ソースURL・メディア名は原文のまま維持。翻訳するのは見出しと要約のみ。

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
出力順序: 日本語ソースの記事を先に、英語ソースの記事（日本語翻訳済み）を後に配置すること。
セクション見出し（【日本語ソース】【英語ソース】等）は付けないこと。区切りなく連続で並べよ。
各トピックに必ず実在するソースURLを付けること。URLは推測しない。
ソースURLは必ず個別記事の直接URLを使え。一覧ページ・トップページのURLは禁止。
例: itmedia.co.jp/aiplus/subtop/news/index.htmlはNG、itmedia.co.jp/aiplus/articles/XXXX/story.htmlはOK"

        log "claudeモード: Web検索+日本語レポート生成を開始..."
        if env -u CLAUDECODE claude -p "$PROMPT" --tools "WebSearch,WebFetch" --dangerously-skip-permissions > "$OUTPUT_FILE" 2>> "$LOG_FILE"; then
            log "claude コマンド完了"
        else
            log "WARN: claude コマンドが失敗しました（終了コード $?）。RSSモードにフォールバック"
            GENAI_MODE="rss"
        fi

        # claudeの思考テキスト除去（"# 生成AI" の前の行を削除）
        if [[ -s "$OUTPUT_FILE" ]]; then
            sed -i '1,/^# 生成AI/{/^# 生成AI/!d}' "$OUTPUT_FILE" 2>/dev/null || true
        fi

        # 出力が空の場合もフォールバック
        if [[ ! -s "$OUTPUT_FILE" ]]; then
            log "WARN: claude出力が空です。RSSモードにフォールバック"
            GENAI_MODE="rss"
        fi

        # トピック数チェック（3件未満→RSSフォールバック）（P4）
        if [[ "$GENAI_MODE" == "claude" ]] && [[ -s "$OUTPUT_FILE" ]]; then
            TOPIC_COUNT="$(grep -c '^## ' "$OUTPUT_FILE" 2>/dev/null || echo 0)"
            if [[ "$TOPIC_COUNT" -lt 3 ]]; then
                log "WARN: claudeレポートのトピック数が少なすぎます（${TOPIC_COUNT}件 < 3件）。RSSモードにフォールバック"
                GENAI_MODE="rss"
            else
                log "トピック数確認: ${TOPIC_COUNT}件（OK）"
            fi
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

    # 英語見出し和訳ステップ（claude CLI または Gemini API を使用）
    if [[ -s "$OUTPUT_FILE" ]]; then
        TRANSLATE_PROMPT="以下のmarkdownレポートについて:
1. ## 見出し行に英語タイトルがあれば日本語に翻訳
2. 英語で書かれた要約・説明文（箇条書きや段落）も日本語に翻訳
形式は変えず、原文の数値・固有名詞は保持すること。日本語化のみで追記・削除はしないこと。

---

$(cat "$OUTPUT_FILE")"
        TRANSLATED=""

        # まずclaudeを試す
        if command -v claude &>/dev/null; then
            log "RSSレポートの英語見出しを和訳中（claude）..."
            TRANSLATED="$(env -u CLAUDECODE claude -p "$TRANSLATE_PROMPT" --tools "" --dangerously-skip-permissions 2>/dev/null || true)"
        fi

        # claudeが失敗した場合はGemini APIにフォールバック
        if [[ -z "$TRANSLATED" ]] && [[ -n "${GEMINI_API_KEY:-}" ]]; then
            log "RSSレポートの英語見出しを和訳中（Gemini APIフォールバック）..."
            GEMINI_PROMPT="以下のmarkdownレポートについて:\n1. ## 見出し行に英語タイトルがあれば日本語に翻訳\n2. 英語で書かれた要約・説明文（箇条書きや段落）も日本語に翻訳\n形式は変えず、原文の数値・固有名詞は保持すること。日本語化のみで追記・削除はしないこと。\n\n---\n\n$(cat "$OUTPUT_FILE" | head -200)"
            GEMINI_RESPONSE="$(curl -s -X POST \
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key=${GEMINI_API_KEY}" \
                -H "Content-Type: application/json" \
                -d "{\"contents\":[{\"parts\":[{\"text\":$(echo "$GEMINI_PROMPT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}]}]}" \
                2>/dev/null || true)"
            TRANSLATED="$(echo "$GEMINI_RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d['candidates'][0]['content']['parts'][0]['text'])
except:
    sys.exit(1)
" 2>/dev/null || true)"
        fi

        if [[ -n "$TRANSLATED" ]]; then
            echo "$TRANSLATED" > "$OUTPUT_FILE"
            log "英語見出し・サマリー和訳完了"
        else
            log "WARN: 和訳失敗（claude・Gemini両方不可）。英語のまま継続"
        fi
    fi
fi

# ---- 完了確認 -------------------------------------------------------
if [[ -f "$OUTPUT_FILE" ]] && [[ -s "$OUTPUT_FILE" ]]; then
    LINES="$(wc -l < "$OUTPUT_FILE")"
    FINAL_TOPIC_COUNT="$(grep -c '^## ' "$OUTPUT_FILE" 2>/dev/null || echo 0)"
    # URL死活確認（オプション、失敗しても続行）
    if [[ -f "$OUTPUT_FILE" ]]; then
        log "URL死活確認を開始..."
        python3 "$SCRIPT_DIR/genai_check_urls.py" "$OUTPUT_FILE" 2>> "$LOG_FILE" || true
        log "URL死活確認完了"
    fi
    # 最終的にトピックが空の場合はntfy通知（P4）
    if [[ "$FINAL_TOPIC_COUNT" -eq 0 ]]; then
        log "WARN: 最終レポートのトピック数が0件です"
        bash "$SCRIPT_DIR/ntfy.sh" "⚠️ genai日報生成失敗: レポートが空です (${DATE_STR})" 2>/dev/null || true
    fi
    log "SUCCESS: レポート生成完了 — $OUTPUT_FILE ($LINES 行, トピック${FINAL_TOPIC_COUNT}件)"

    # タイトルキャッシュ保存（P3: 日跨ぎ重複排除用）
    log "タイトルキャッシュを保存中..."
    python3 -c "
import json, re, sys
from pathlib import Path

cache_file = Path('$CACHE_FILE')
output_file = Path('$OUTPUT_FILE')
date_str = '$DATE_STR'

titles = []
try:
    content = output_file.read_text(encoding='utf-8')
    for line in content.splitlines():
        if line.startswith('## '):
            heading = line[3:].strip()
            heading = re.sub(r'[★☆]{5}\s*', '', heading)
            title = re.sub(r'^[^\w\d\u3000-\u9FFF\uF900-\uFAFF]+', '', heading).strip()
            if title:
                titles.append(title)
except Exception as e:
    print(f'WARN: タイトル抽出失敗: {e}', file=sys.stderr)
    sys.exit(0)

cache = {}
if cache_file.exists():
    try:
        cache = json.loads(cache_file.read_text(encoding='utf-8'))
    except Exception:
        cache = {}

cache[date_str] = titles

all_dates = sorted(cache.keys(), reverse=True)
for old_date in all_dates[3:]:
    del cache[old_date]

cache_file.parent.mkdir(parents=True, exist_ok=True)
cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'タイトルキャッシュ保存完了: {len(titles)}件 -> {cache_file}')
" 2>> "$LOG_FILE" || log "WARN: タイトルキャッシュ保存失敗（メインレポートは生成済み）"
else
    log "ERROR: 出力ファイルが生成されませんでした: $OUTPUT_FILE"
    bash "$SCRIPT_DIR/ntfy.sh" "⚠️ genai日報生成失敗: レポートが空です (${DATE_STR})" 2>/dev/null || true
    exit 1
fi

log "=== 完了 ==="

# ---- 重複排除（URL一致+Embedding類似度3段階）--------------------------
log "重複排除を開始..."
DEDUP_API_KEY="${GEMINI_API_KEY:-AIzaSyBWlyApVA01J0DhfEDLojMajkWeARaB-d8}"
source ~/.bashrc 2>/dev/null || true
GEMINI_API_KEY="$DEDUP_API_KEY" python3 "$SCRIPT_DIR/genai_dedup.py" "$DATE_STR" 2>> "$LOG_FILE" || log "WARN: 重複排除失敗（メインレポートは生成済み）"

# ---- P1: Top3 ntfy配信 ----------------------------------------------
log "Top3 ntfy配信を開始..."
bash "$SCRIPT_DIR/genai_ntfy_top3.sh" "$DATE_STR" || log "WARN: Top3配信失敗（メインレポートは生成済み）"

# ---- スコアリング: 各トピック見出しにスコアを追記 --------------------
log "トピックスコアリングを開始..."
bash "$SCRIPT_DIR/genai_score_topics.sh" "$DATE_STR" || log "WARN: スコアリング失敗（メインレポートは生成済み）"

# ---- OGP事前取得（バックグラウンド）-----------------------------------
log "OGP事前取得を開始（バックグラウンド）..."
python3 "$SCRIPT_DIR/genai_ogp_prefetch.py" "$DATE_STR" >> "$LOG_FILE" 2>&1 &

# ---- 静的サイトビルド + Cloudflare Pagesデプロイ -------------------
log "静的サイトビルドを開始..."
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)" bash "$SCRIPT_DIR/genai_build_static.sh" >> "$LOG_FILE" 2>&1 && {
    log "静的サイトビルド完了"
    npx wrangler pages deploy "$(cd "$SCRIPT_DIR/.." && pwd)/dist/" --project-name=genai-daily >> "$LOG_FILE" 2>&1 \
        && log "Cloudflare Pagesデプロイ完了" \
        || log "WARN: wrangler未設定 or デプロイ失敗（静的ビルドは完了済み）"
} || log "WARN: 静的サイトビルド失敗"
