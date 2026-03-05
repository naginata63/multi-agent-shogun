#!/usr/bin/env python3
"""
店舗オーナーDXパック ツールマニュアルPDF生成スクリプト
EC商品説明ツール / SNS投稿文ツール の購入者向けマニュアルを生成

Usage:
    python3 scripts/generate_tool_manual_pdf.py
"""

import sys
import base64
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# ツール定義
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "EC出品者向け 商品説明文\n自動生成スプレッドシート",
        "tagline": "商品説明文、手打ちしてませんか？AIに任せれば、5秒で完成します。",
        "project_dir": BASE_DIR / "projects" / "ec_description_tool",
        "output_pdf": BASE_DIR / "projects" / "ec_description_tool" / "manual.pdf",
        "features": [
            "Googleスプレッドシートで完結——インストール不要",
            "Amazon・楽天・BASE・メルカリ・汎用 5種類のプラットフォームに最適化した出力",
            "ワンクリックでキャッチコピー・短文・長文・SEOキーワード・SNS投稿文を一括生成",
            "買い切り——月額費用なし（Gemini API無料枠で運用可能）",
            "デモデータ5件入力済み——購入後すぐ動作確認できる",
        ],
        "sheet_structure_tables": [
            {
                "title": "「メイン」シート 列定義",
                "headers": ["列", "ラベル", "種別", "説明"],
                "rows": [
                    ["A", "商品名", "入力（必須）", "EC掲載用の商品名。空欄でループ終了"],
                    ["B", "特徴・スペック", "入力（推奨）", "スペック・機能・素材など"],
                    ["C", "ターゲット層", "入力（推奨）", "想定購買者（例: スマホユーザー）"],
                    ["D", "価格", "入力（任意）", "表示価格（例: 2,980円）"],
                    ["E", "販売プラットフォーム", "入力（プルダウン）", "Amazon / 楽天 / メルカリ / BASE / 汎用"],
                    ["F", "備考", "入力（任意）", "追加情報など"],
                    ["G", "キャッチコピー", "出力", "Gemini生成。30文字以内"],
                    ["H", "商品説明文・短", "出力", "Gemini生成。100文字程度"],
                    ["I", "商品説明文・長", "出力", "Gemini生成。300〜500文字"],
                    ["J", "SEOキーワード", "出力", "Gemini生成。カンマ区切り5キーワード"],
                    ["K", "SNS投稿文", "出力", "Gemini生成。Twitterスタイル・140文字以内"],
                    ["L", "ステータス", "出力", "⏳生成中 / ✅生成完了 / ❌エラー"],
                ],
            },
            {
                "title": "「設定」シート セル定義",
                "headers": ["セル", "項目名", "必須/任意", "説明"],
                "rows": [
                    ["B2", "Gemini APIキー", "必須", "設定シートのみに保管。他者に共有禁止"],
                    ["B4", "APIキー取得URL", "参照用", "https://aistudio.google.com/app/apikey"],
                    ["B6", "文体トーン設定", "任意", "標準 / 丁寧 / カジュアル / 専門的（プルダウン）"],
                ],
            },
        ],
        "how_to_use_steps": [
            "「設定」シートのB2セルにGemini APIキーを貼り付ける",
            "「メイン」シートのA列（商品名）〜E列（プラットフォーム）に商品情報を入力する",
            "メニューバーの「AI生成」→「商品説明文を生成」をクリック",
            "数秒でG〜K列にキャッチコピー・説明文・SEOキーワード・SNS投稿文が生成される",
            "L列のステータス（✅ 生成完了 / ❌ エラー）で結果を確認し、コピペして使用する",
        ],
        "faq": [
            ("Gemini APIキーは必ず必要ですか？",
             "はい、必要です。ただしGoogle AI StudioでGoogleアカウントがあれば無料で発行できます。クレジットカードの登録も不要です。"),
            ("月額費用はかかりますか？",
             "本ツール自体は買い切りで、月額費用はありません。Gemini APIの使用量は通常の出品作業（1日数十件程度）であれば無料枠内に収まることがほとんどです。"),
            ("Amazon・楽天以外のECにも使えますか？",
             "「汎用」プラットフォームを選択すると、特定のECに依存しない標準的な説明文が生成されます。Yahoo!ショッピング等にも応用可能です。"),
            ("APIキーエラーが出た場合は？",
             "「設定」シートのB2セルにAPIキーが正しく入力されているか確認してください。先頭・末尾のスペースや改行が入っている場合はエラーになります。"),
            ("「このアプリは確認されていません」と表示される",
             "個人使用の自作スクリプトでは通常表示されます。「詳細」→「〜に移動（安全でない）」をクリックして進んでください。"),
            ("文字化けする・日本語が出力されない",
             "Gemini APIへの接続は正常でも、稀に英語で返答される場合があります。プロンプトに「必ず日本語で回答してください」と追加するか、再実行してください。"),
        ],
    },
    {
        "name": "SNS投稿文 30日分\n自動生成Googleスプレッドシート",
        "tagline": "30日分のSNS投稿を1クリックで自動生成。毎日の更新作業ゼロで、SNS集客自動化で本業売上を伸ばす。",
        "project_dir": BASE_DIR / "projects" / "sns_post_tool",
        "output_pdf": BASE_DIR / "projects" / "sns_post_tool" / "manual.pdf",
        "features": [
            "投稿ネタ × 3媒体文章 × 30日分を一括生成——SNS更新の工数をゼロに",
            "飲食店・美容サロン・EC・士業・フィットネス・教室の6業種特化プロンプト内蔵",
            "情報提供・裏側紹介・お客様の声・セール・季節ネタのカテゴリバランスを自動調整",
            "Twitter/X（140文字）・Instagram（ハッシュタグ付き）・Facebook（400文字）3媒体に最適化",
            "Gemini API無料枠対応——月額費用なし（月1〜2回の一括生成は無料枠内）",
        ],
        "sheet_structure_tables": [
            {
                "title": "「メイン」シート 列定義（30日分の投稿結果）",
                "headers": ["列", "ラベル", "種別", "説明"],
                "rows": [
                    ["A", "日付", "出力", "投稿日。開始日設定時はYYYY/MM/DD、未設定時はN日目"],
                    ["B", "曜日", "出力", "投稿開始日(B16)設定時のみ「○曜日」が自動計算される"],
                    ["C", "投稿テーマ", "出力", "Gemini生成。その日の投稿の軸（20文字以内）"],
                    ["D", "Twitter/X", "出力", "Gemini生成。140文字以内（ハッシュタグ込み）"],
                    ["E", "Instagram", "出力", "Gemini生成。本文100〜300文字 + ハッシュタグ20〜30個"],
                    ["F", "Facebook", "出力", "Gemini生成。400文字以内（ハッシュタグ3〜5個）"],
                    ["G", "投稿カテゴリ", "出力", "情報提供 / 裏側紹介 / お客様の声 / セール / 季節 / その他"],
                    ["H", "ステータス", "出力", "⏳待機中 / ✅生成済み / ❌エラー"],
                ],
            },
            {
                "title": "「設定」シート セル定義",
                "headers": ["セル", "項目名", "必須/任意", "説明"],
                "rows": [
                    ["B2", "Gemini APIキー", "必須", "設定シートのみに保管。他者に共有禁止"],
                    ["B4", "APIキー取得URL", "参照用", "https://aistudio.google.com/app/apikey"],
                    ["B6", "業種", "推奨", "飲食店 / 美容サロン / EC・ネットショップ / 士業 / フィットネス / 教室・スクール"],
                    ["B8", "サービス名", "必須", "お店・サービスの正式名称"],
                    ["B10", "ターゲット顧客", "推奨", "想定フォロワー・顧客層（例: 20〜30代の女性）"],
                    ["B12", "投稿の目的", "推奨", "集客 / ブランディング / エンゲージメント向上 / 商品販売 / 採用 / その他"],
                    ["B14", "文体トーン", "推奨", "親しみやすい / プロフェッショナル / カジュアル / 丁寧 / ポップ"],
                    ["B16", "投稿開始日", "任意", "設定すると曜日が自動計算され、A列に実際の日付が入る"],
                    ["B18", "特記事項", "任意", "キャンペーン情報・禁止ワード・強調ポイント等"],
                ],
            },
        ],
        "how_to_use_steps": [
            "「設定」シートのB2セルにGemini APIキーを貼り付ける",
            "「設定」シートのB6（業種）、B8（サービス名）、B10〜B18の各項目を入力する",
            "メニューバーの「AI生成」→「SNS投稿を一括生成」をクリック",
            "約30〜60秒で30日分（Twitter/X・Instagram・Facebook 合計90投稿文）が生成される",
            "H列のステータスで確認後、各SNSに投稿テキストをコピペして使用する",
        ],
        "faq": [
            ("Googleアカウントは必要ですか？",
             "はい、必要です。スプレッドシートの操作とGemini APIの利用にGoogleアカウントが必要です。無料で作成できます。"),
            ("月額費用はかかりますか？",
             "本ツール自体は買い切りで、月額費用はありません。月1〜2回の一括生成（30日分）であればGemini API無料枠の範囲内に収まります。"),
            ("APIキーエラーが出た場合は？",
             "「設定」シートのB2セルにAPIキーが正しく入力されているか確認してください。B8のサービス名が空欄の場合もエラーになります。"),
            ("「このアプリは確認されていません」と表示される",
             "個人使用の自作スクリプトでは通常表示されます。「詳細」→「〜に移動（安全でない）」をクリックして進んでください。"),
            ("生成した投稿文を修正したい",
             "「メイン」シートのセルを直接編集して修正できます。AIが生成したたたき台をベースに手直しすることでより効果的な投稿になります。"),
            ("スマートフォンでも使えますか？",
             "スプレッドシートアプリで閲覧・編集は可能ですが、GASによる自動生成機能はPCのブラウザ版での動作を推奨します（スマホではメニューバーが表示されない場合があります）。"),
        ],
    },
]


# ---------------------------------------------------------------------------
# HTML / CSS 生成
# ---------------------------------------------------------------------------

def escape_html(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def build_css() -> str:
    return """
@page {
    size: A4;
    margin: 20mm;
    @bottom-center {
        content: counter(page);
        font-size: 9pt;
        color: #888;
        font-family: "Noto Sans CJK JP", sans-serif;
    }
}

body {
    font-family: "Noto Sans CJK JP", sans-serif;
    font-size: 10pt;
    line-height: 1.7;
    color: #1a1a1a;
}

/* Cover */
.cover {
    text-align: center;
    padding-top: 80px;
    page-break-after: always;
    background: #f8f9fa;
    min-height: 200mm;
}

.cover h1 {
    font-size: 22pt;
    margin-top: 60px;
    margin-bottom: 10pt;
    line-height: 1.4;
    color: #1a237e;
}

.cover .tagline {
    font-size: 12pt;
    color: #555;
    margin: 16pt 20pt;
    line-height: 1.6;
    font-style: italic;
}

.cover .date-label {
    font-size: 10pt;
    color: #888;
    margin-top: 30pt;
}

.cover .badge {
    display: inline-block;
    background: #1a237e;
    color: white;
    font-size: 10pt;
    padding: 4pt 12pt;
    border-radius: 4pt;
    margin-top: 20pt;
}

/* Section headings */
h2 {
    font-size: 16pt;
    border-bottom: 2px solid #333;
    padding-bottom: 4pt;
    margin-top: 24pt;
    margin-bottom: 10pt;
    color: #1a237e;
}

h3 {
    font-size: 12pt;
    margin-top: 16pt;
    margin-bottom: 6pt;
    color: #333;
}

p {
    margin: 6pt 0;
}

/* Feature list */
.feature-list {
    margin: 8pt 0 8pt 0;
    padding-left: 0;
    list-style: none;
}

.feature-list li {
    padding: 6pt 10pt;
    margin-bottom: 4pt;
    background: #e8eaf6;
    border-left: 4px solid #1a237e;
    border-radius: 2pt;
    font-size: 10.5pt;
}

/* Setup steps */
.setup-steps {
    margin: 8pt 0;
    padding-left: 0;
    list-style: none;
    counter-reset: step-counter;
}

.setup-steps li {
    counter-increment: step-counter;
    padding: 6pt 10pt 6pt 40pt;
    margin-bottom: 4pt;
    background: #f5f5f5;
    border-radius: 4pt;
    position: relative;
    font-size: 10pt;
}

.setup-steps li::before {
    content: "STEP " counter(step-counter);
    position: absolute;
    left: 6pt;
    top: 6pt;
    background: #333;
    color: white;
    font-size: 7pt;
    font-weight: bold;
    padding: 1pt 4pt;
    border-radius: 2pt;
    white-space: nowrap;
}

/* How-to steps */
.howto-steps {
    margin: 8pt 0;
    padding-left: 0;
    list-style: none;
    counter-reset: howto-counter;
}

.howto-steps li {
    counter-increment: howto-counter;
    padding: 5pt 10pt 5pt 36pt;
    margin-bottom: 4pt;
    background: #e8f5e9;
    border-radius: 4pt;
    position: relative;
    font-size: 10pt;
}

.howto-steps li::before {
    content: counter(howto-counter);
    position: absolute;
    left: 10pt;
    top: 5pt;
    background: #34a853;
    color: white;
    font-size: 9pt;
    font-weight: bold;
    width: 16pt;
    height: 16pt;
    line-height: 16pt;
    text-align: center;
    border-radius: 50%;
}

/* Tables */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 8pt 0;
    font-size: 9pt;
}

th, td {
    border: 1px solid #ccc;
    padding: 5pt 8pt;
    text-align: left;
    vertical-align: top;
}

th {
    background: #e8eaf6;
    font-weight: bold;
    color: #333;
}

tr:nth-child(even) td {
    background: #fafafa;
}

/* Code block */
pre {
    background: #f4f4f4;
    padding: 12px;
    border-radius: 4px;
    overflow-wrap: break-word;
    margin: 8pt 0;
}

code {
    font-family: "Noto Sans Mono CJK JP", "Courier New", monospace;
    font-size: 7.5pt;
    white-space: pre-wrap;
    word-break: break-all;
    line-height: 1.5;
}

/* FAQ */
.faq-item {
    margin-bottom: 10pt;
    page-break-inside: avoid;
}

.faq-q {
    font-weight: bold;
    color: #1a237e;
    margin-bottom: 3pt;
    font-size: 10pt;
}

.faq-q::before {
    content: "Q. ";
}

.faq-a {
    padding-left: 14pt;
    font-size: 9.5pt;
    color: #333;
}

.faq-a::before {
    content: "A. ";
    font-weight: bold;
    color: #34a853;
}

/* Code section break */
.code-section {
    page-break-before: always;
}
"""


def build_cover_html(tool: dict, today: str) -> str:
    name_html = escape_html(tool["name"]).replace("\n", "<br>")
    tagline_html = escape_html(tool["tagline"])
    return f"""
<div class="cover">
    <h1>{name_html}</h1>
    <div class="tagline">{tagline_html}</div>
    <div class="badge">Gemini API 対応 | Google Apps Script</div>
    <div class="date-label">購入者向けセットアップマニュアル<br>{today}</div>
</div>
"""


def build_features_html(tool: dict) -> str:
    items = "".join(f"<li>{escape_html(f)}</li>" for f in tool["features"])
    return f"""
<h2>このツールでできること</h2>
<ul class="feature-list">
{items}
</ul>
"""


def build_setup_html() -> str:
    steps = [
        "Googleスプレッドシートを新規作成",
        "メニュー「拡張機能」→「Apps Script」でGASエディタを開く",
        "下記「GASコード全文」を全文コピーして貼り付け、保存（Ctrl+S）",
        "スプレッドシートに戻り「メニューが追加されたか」確認。APIキーを「設定」シートのB2セルに入力",
    ]
    items = "".join(f"<li>{escape_html(s)}</li>" for s in steps)
    return f"""
<h2>セットアップ手順</h2>
<ol class="setup-steps">
{items}
</ol>
<p><strong>初回実行時の権限承認について</strong>: 「このアプリは確認されていません」と表示されます。
「詳細」→「〜に移動（安全でない）」をクリックして進んでください。個人使用の自作スクリプトでは通常表示されます。</p>
"""


def build_setup_with_screenshots_html(tool: dict, ss_dir: Path) -> str:
    """セットアップ手順を各STEPテキスト+スクショの交互配置で生成"""
    SETUP_STEPS = [
        {
            "text": "メニュー「拡張機能」→「Apps Script」でGASエディタを開き、"
                    "下記コードを全文コピーして貼り付け、保存（Ctrl+S）",
            "screenshot": "01_gas_editor.png",
            "caption": "▲ STEP1：GASエディタにコードを貼り付けた状態（拡張機能→Apps Scriptで開く）",
        },
        {
            "text": "スプレッドシートに戻り、ページをリロード（F5キーまたはブラウザの再読み込みボタン）してから、メニューバーに「EC商品説明AI」が追加されていることを確認",
            "screenshot": "02_menu_open.png",
            "caption": "▲ STEP2：カスタムメニュー「EC商品説明AI」がメニューバーに表示されます",
        },
        {
            "text": "「EC商品説明AI」→「🚀 セットアップ（初回設定）」をクリックして初期化を実行",
            "screenshot": "03_setup_menu.png",
            "caption": "▲ STEP3：「🚀 セットアップ（初回設定）」を選択します",
        },
        {
            "text": "シート初期化の確認ダイアログが表示されたら「OK」をクリック",
            "screenshot": "04_api_dialog.png",
            "caption": "▲ STEP4：シート初期化の確認ダイアログが表示されます。「OK」をクリックして初期化を実行します",
        },
        {
            "text": "「設定」シートのB2セルにGemini APIキーを貼り付ける",
            "screenshot": "04b_settings_sheet.png",
            "caption": "▲ STEP5：「設定」シートのB2セルにAPIキーを入力します",
        },
    ]
    html = "<h2>セットアップ手順</h2>\n"
    for i, step in enumerate(SETUP_STEPS, 1):
        html += (
            f'<div style="margin:12pt 0;">\n'
            f'<p><strong>STEP {i}：</strong>{escape_html(step["text"])}</p>\n'
            + build_screenshot_html(ss_dir / step["screenshot"], step["caption"])
            + "</div>\n"
        )
    html += build_screenshot_html(
        ss_dir / "05_setup_complete.png",
        "▲ 初回設定完了。テストデータ5件が自動入力されます",
    )
    html += (
        "<p><strong>初回実行時の権限承認について</strong>: 「このアプリは確認されていません」と表示されます。"
        "「詳細」→「〜に移動（安全でない）」をクリックして進んでください。個人使用の自作スクリプトでは通常表示されます。</p>\n"
    )
    return html


def build_sheet_structure_html(tool: dict) -> str:
    html = "<h2>シート構成</h2>\n"
    for table_def in tool["sheet_structure_tables"]:
        html += f"<h3>{escape_html(table_def['title'])}</h3>\n"
        html += "<table>\n<tr>"
        for h in table_def["headers"]:
            html += f"<th>{escape_html(h)}</th>"
        html += "</tr>\n"
        for row in table_def["rows"]:
            html += "<tr>"
            for cell in row:
                html += f"<td>{escape_html(cell)}</td>"
            html += "</tr>\n"
        html += "</table>\n"
    return html


def build_code_html(code_gs_path: Path) -> str:
    lines = code_gs_path.read_text(encoding="utf-8").split('\n')
    header = '\n'.join(lines[:20])
    gist_url = "https://gist.github.com/naginata63/c2eab9565928de5e492a9fa0f5e550e0"
    return f'''
<div class="code-section">
<h2>GASコード全文</h2>
<p>GASコードの全文は以下のGistからコピーしてください（「Raw」ボタンで全文一括コピー可能です）:</p>
<p><a href="{gist_url}">{gist_url}</a></p>
<p>コードの概要（先頭部分）:</p>
<pre><code>{escape_html(header)}

// ▼ 全コードはGistを参照してください ▼
// {gist_url}</code></pre>
</div>
'''


def _img_b64(path: Path) -> str:
    """画像ファイルをBase64エンコードして返す。ファイルがなければ空文字。"""
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


def build_screenshot_html(path: Path, caption: str) -> str:
    """1枚のスクリーンショットをfigure要素として埋め込む。"""
    b64 = _img_b64(path)
    if not b64:
        return ""
    return (
        f'<figure style="margin:16px 0;text-align:center;page-break-inside:avoid;">'
        f'<img src="data:image/png;base64,{b64}" '
        f'style="max-width:480px;width:100%;display:block;margin:0 auto;'
        f'border:1px solid #e0e0e0;border-radius:4px;">'
        f'<figcaption style="font-size:9pt;color:#666;margin-top:6px;'
        f'font-style:italic;text-align:center;">{caption}</figcaption>'
        f'</figure>\n'
    )


def build_howto_html(tool: dict) -> str:
    items = "".join(f"<li>{escape_html(s)}</li>" for s in tool["how_to_use_steps"])
    return f"""
<h2>使い方</h2>
<ol class="howto-steps">
{items}
</ol>
"""


def build_faq_html(tool: dict) -> str:
    html = "<h2>FAQ・トラブルシューティング</h2>\n"
    for q, a in tool["faq"]:
        html += f"""<div class="faq-item">
<div class="faq-q">{escape_html(q)}</div>
<div class="faq-a">{escape_html(a)}</div>
</div>
"""
    return html


def build_full_html(tool: dict) -> str:
    today = date.today().strftime("%Y年%m月%d日")
    css = build_css()
    ss_dir = tool["project_dir"] / "screenshots"
    body = (
        build_cover_html(tool, today)
        + build_features_html(tool)
        + build_setup_with_screenshots_html(tool, ss_dir)
        + build_sheet_structure_html(tool)
        + build_code_html(tool["project_dir"] / "Code.gs")
        + build_howto_html(tool)
        + build_screenshot_html(
            ss_dir / "06_generate_result.png",
            "▲ 生成結果：G〜L列にキャッチコピー・説明文・SEOキーワード・SNS投稿文が自動入力されます"
        )
        + build_faq_html(tool)
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    try:
        import weasyprint
    except ImportError:
        print("ERROR: weasyprint がインストールされていません。pip install weasyprint")
        sys.exit(1)

    for tool in TOOLS:
        print(f"\n--- {tool['name'].strip()} ---")
        html = build_full_html(tool)

        # debug HTML
        debug_path = tool["output_pdf"].with_suffix(".html")
        debug_path.write_text(html, encoding="utf-8")
        print(f"Debug HTML: {debug_path}")

        print("Converting to PDF...")
        try:
            doc = weasyprint.HTML(string=html, base_url=str(tool["project_dir"]))
            doc.write_pdf(str(tool["output_pdf"]))
            size_kb = tool["output_pdf"].stat().st_size / 1024
            print(f"PDF generated: {tool['output_pdf']}")
            print(f"File size: {size_kb:.0f} KB")
        except Exception as e:
            print(f"ERROR during PDF generation: {e}")
            sys.exit(1)

    print("\nAll PDFs generated successfully.")


if __name__ == "__main__":
    main()
