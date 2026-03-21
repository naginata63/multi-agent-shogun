#!/usr/bin/env python3
"""
qc_prompt_execution.py — ココナラプロンプト 実行QCパイプライン
Gemini API (gemini-2.0-flash) でプロンプトを実投入し、LLM-as-Judgeで品質採点する。

使用方法:
    python3 scripts/qc_prompt_execution.py <category_dir> <output_yaml>

例:
    python3 scripts/qc_prompt_execution.py \\
        reports/coconala_prompts/individual/01_sales \\
        reports/coconala_prompts/execution_qc/01_sales_results.yaml
"""

import sys
import os
import re
import json
import time
from datetime import datetime
from pathlib import Path

# --- 依存パッケージチェック ---
try:
    from google import genai
except ImportError:
    print(
        "ERROR: google-genai パッケージが未インストールです。",
        file=sys.stderr,
    )
    print("インストール方法:", file=sys.stderr)
    print("    pip install google-genai", file=sys.stderr)
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML が未インストールです。", file=sys.stderr)
    print("インストール方法:", file=sys.stderr)
    print("    pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# --- Pythonコードサンプル（コード系プレースホルダ共通値）---
PYTHON_CODE_SAMPLE = (
    "def calculate_discount(price: float, rate: float) -> float:\n"
    '    """割引額を計算する。"""\n'
    "    if price < 0 or rate < 0 or rate > 1:\n"
    "        raise ValueError('Invalid: price or rate out of range')\n"
    "    return price * (1 - rate)\n\n\n"
    "class UserService:\n"
    "    def __init__(self, db):\n"
    "        self.db = db\n\n"
    "    def get_user(self, user_id: int):\n"
    "        # TODO: SQLインジェクション対策が必要\n"
    "        return self.db.query(f'SELECT * FROM users WHERE id = {user_id}')\n"
)

# --- プレースホルダ置換用ダミー値 ---
PLACEHOLDER_VALUES = {
    # 会社・人物
    "会社名": "株式会社サンプル",
    "自社名": "株式会社テクノソリューション",
    "社名": "株式会社サンプル",
    "担当者名": "山田太郎",
    "担当者": "営業部 山田太郎",
    "名前": "山田太郎",
    "自分の名前": "山田太郎",
    # 商品・サービス
    "商品名": "AIアシスタントPro",
    "サービス名": "業務自動化SaaS",
    "サービス名・概要（例：中小企業向けの請求書自動化SaaS）": "中小企業向け業務自動化SaaS",
    "製品名": "スマートオフィスツール",
    # 業種・業界
    "業種": "IT・テクノロジー",
    "業界": "製造業",
    # 送付先情報
    "送付先企業名": "株式会社テスト商事",
    "役職・名前 / 不明なら「ご担当者様」": "営業部長 田中様",
    "役職・名前": "営業部長 田中様",
    # 課題・問題
    "課題": "業務効率化の遅れ",
    "想定している相手の課題": "請求書処理に月40時間以上かかっている",
    "例：請求書処理に月40時間以上かかっている": "請求書処理に月40時間以上かかっている",
    # 数値・量
    "数値": "30%",
    "金額": "100,000円",
    "期間": "3ヶ月",
    "件数": "50件",
    # その他汎用
    "内容": "業務効率化に関する重要なご提案",
    "詳細": "詳細については別途ご案内いたします",
    "URL": "https://example.com",
    # 業種（例...）パターン
    "業種（例：製造業、IT企業など）": "IT・テクノロジー",
    # --- A. コード系 ---
    "コード貼り付け": PYTHON_CODE_SAMPLE,
    "ここにコードを貼り付ける": PYTHON_CODE_SAMPLE,
    "コードを貼り付ける（長い場合は問題箇所のみ可）": PYTHON_CODE_SAMPLE,
    "コード・関数名（例: UserAuthService.login()）": PYTHON_CODE_SAMPLE,
    "コード・システム名（例: 受注管理API / モジュール名）": PYTHON_CODE_SAMPLE,
    "コード貼り付け（任意）": PYTHON_CODE_SAMPLE,
    "コード貼り付け（またはシステムの概要）": PYTHON_CODE_SAMPLE,
    "コードをここに貼り付け": PYTHON_CODE_SAMPLE,
    "コードをここに貼り付け（100〜300行程度が最適）": PYTHON_CODE_SAMPLE,
    "現在のテストコードを貼り付ける（なければ「なし」）": PYTHON_CODE_SAMPLE,
    "リファクタリングしたいコードをここに貼り付け": PYTHON_CODE_SAMPLE,
    "テスト対象コード": PYTHON_CODE_SAMPLE,
    # --- B. 言語・フレームワーク系 ---
    "言語名": "Python",
    "言語": "Python",
    "プログラム言語": "Python",
    "フレームワーク": "FastAPI",
    "フレームワーク名": "FastAPI",
    "言語/フレームワーク": "Python / pytest",
    "バックエンド言語・フレームワーク": "Python / FastAPI",
    "テストフレームワーク": "pytest",
    "使用テストフレームワーク": "pytest",
    "CIツール": "GitHub Actions",
    "言語名（例: Python / Node.js / Java）": "Python",
    "言語名（例: Python / TypeScript / Java）": "Python",
    "言語名（例: TypeScript / Python / Java）": "Python",
    "言語・フレームワーク（例: Python / pytest、TypeScript / Jest）": "Python / pytest",
    "Python / TypeScript / Java など": "Python",
    "Python 3.11 / Node.js 20 など": "Python 3.11",
    "Python/Django / TypeScript/Next.js など": "Python / FastAPI",
    "技術スタック（例: Python 3.8 / Django 2.2 / PostgreSQL 12）": "Python 3.11 / FastAPI 0.104 / PostgreSQL 15",
    "例: Python 3.11 / Django 4.2": "Python 3.11 / FastAPI 0.104",
    "例: React 18 + Node.js 20": "React 18 + Node.js 20 + PostgreSQL 15",
    # --- C. API定数系（ALL_CAPS）---
    "API_ENDPOINT": "https://api.example.com/v1",
    "BASE_URL": "https://api.example.com",
    "API URL": "https://api.example.com/v1",
    "https://api.example.com/v1": "https://api.example.com/v1",
    "TOKEN_URL": "https://auth.example.com/oauth/token",
    "REDIS_URL": "redis://localhost:6379",
    "MAX_RETRIES": 3,
    "MAX_ATTEMPTS": 3,
    "TIMEOUT": 30,
    "MAX_WORKERS": 4,
    "NUM_WORKERS": 4,
    "MAX_CONCURRENT": 10,
    "CONN_LIMIT": 10,
    "CHUNK_SIZE": 100,
    "QUEUE_SIZE": 100,
    "BACKOFF_FACTOR": 0.5,
    "DB_PATH": "data/app.db",
    "CSV_PATH": "data/input.csv",
    "INPUT_CSV": "data/input.csv",
    "OUTPUT_DIR": "output/",
    "OUTPUT_XLSX": "output/report.xlsx",
    "OUTPUT_PDF": "output/report.pdf",
    "OUTPUT_MD": "output/report.md",
    "LOG_FILE_PATH": "logs/app.log",
    "SERVICE_NAME": "myapp",
    "TIMEZONE": "Asia/Tokyo",
    "USERNAME": "user@example.com",
    "PASSWORD": "P@ssword123",
    "CHECKPOINT_PATH": "checkpoints/batch.pkl",
    "SQL_QUERY": "SELECT id, name, price FROM products WHERE active = 1",
    "TEMPLATE_PATH": "templates/report.html",
    "JAPANESE_FONT": "IPAGothic",
    "DEFAULT_QUEUE": "default",
    "HIGH_QUEUE": "high_priority",
    "LOW_QUEUE": "low_priority",
    "DEFAULT_TTL": 3600,
    "VISIBILITY_TIMEOUT": 30,
    "COLUMNS": "id, name, price, quantity",
    "GROUP_BY": "category",
    "METRICS": "response_time, error_rate, throughput",
    "MODULE_PATH": "app.services.user",
    "DATA_SOURCE": "PostgreSQL (app_db)",
    "SCHEDULE_CONFIG": "0 9 * * 1-5",
    "TARGET_EXCEPTIONS": "(requests.Timeout, requests.ConnectionError)",
    "TIMING_THRESHOLD": 0.1,
    "RESPONSE_TYPE_1": "JSON",
    "RESPONSE_TYPE_2": "CSV",
    "ENDPOINTS": "/api/users, /api/products, /api/orders",
    "ITEMS_SOURCE": "https://api.example.com/v1/items",
    "GraphQL APIのエンドポイントURL": "https://api.example.com/graphql",
    "API名": "GitHub API",
    "API名（例: GitHub API, Stripe API）": "GitHub API",
    "対象API": "REST API (OpenAPI 3.0準拠)",
    # --- D. スクレイピング・ファイル操作系 ---
    "スクレイピング対象のサイト種別（例: ECサイト商品一覧、求人サイト、不動産情報）": "ECサイト商品一覧",
    "サイトの説明（例: 無限スクロールのECサイト）": "無限スクロールのECサイト",
    "取得したいデータ項目（例: 商品名・価格・レビュー数）": "商品名・価格・在庫数・評価",
    "取得項目（例: タイトル・URL・日時・本文・画像URL）": "タイトル・URL・日時・本文",
    "ページネーション方式": "オフセット方式",
    "認証方式": "Bearer Token",
    "ログイン必要有無": "あり（セッション認証）",
    "出力形式": "CSV",
    "保存先": "output/scraped_data.csv",
    "対象サイト": "https://example.com/products",
    "対象サイト種別": "ECサイト商品一覧",
    "URLリストファイルのパス": "urls.txt",
    "URLリストファイルのパス（1行1URL）": "urls.txt",
    "並列ワーカー数（例: 5）": 5,
    "並列数": 5,
    "エンドポイント": "/api/products",
    "主要エンドポイント": "/api/users, /api/products",
    "ディレクトリまたは単一ファイルのパス": "data/",
    "出力ディレクトリ": "output/",
    "入力ファイル": "data/input.csv",
    "データソース": "PostgreSQL (app_db)",
    "データの種類": "商品情報（id, name, price, stock）",
    "取得データ": "商品名・価格・在庫数",
    # --- E. コードレビュー・バグ系 ---
    "エラーメッセージ貼り付け": (
        "AttributeError: 'NoneType' object has no attribute 'get'\n"
        "  File 'app/services/user.py', line 42, in get_user\n"
        "  return user.get('name')"
    ),
    "スタックトレース貼り付け": (
        "Traceback (most recent call last):\n"
        "  File 'app.py', line 15, in <module>\n"
        "    result = process(data)\n"
        "  File 'app.py', line 8, in process\n"
        "    return data['key']\n"
        "KeyError: 'key'"
    ),
    "コード・ログ貼り付け": (
        "2026-03-04 10:00:00 ERROR Connection timeout: host=db.example.com port=5432\n"
        "2026-03-04 10:00:01 ERROR Retry 1/3 failed\n"
        "2026-03-04 10:00:02 CRITICAL Max retries exceeded"
    ),
    "バグタイトル": "ユーザー取得APIで NullPointerError が発生する",
    "バグ内容": "特定のユーザーIDでGET /api/users/{id}を呼ぶと500エラーになる。DBにレコードは存在する。",
    "症状を記載": "ログイン後のプロフィール編集で保存ボタンを押すと500エラー",
    "試したこと1": "ブラウザのキャッシュクリア → 解決せず",
    "試したこと2": "別のユーザーアカウントで試行 → 同様のエラー",
    "チーム規模（例: 3名 / スプリント2週間）": "5名 / スプリント2週間",
    "ビジネス優先度（例: 新規機能開発が最優先 / 安定稼働が最優先 / コスト削減が急務）": "安定稼働が最優先",
    # --- F. テスト設計系 ---
    "機能の説明をここに記載": "ユーザー登録API: メールアドレスとパスワードを受け取り、バリデーション後DBに保存する",
    "クラス名またはコードをここに記載": "class UserService:\n    def create_user(self, email: str, password: str) -> User:",
    "エンドポイント一覧をここに記載（例: POST /api/getUserInfo）": "POST /api/users, GET /api/users/{id}, PUT /api/users/{id}, DELETE /api/users/{id}",
    "PRの説明文をここに貼り付け": "feat: ユーザー認証APIにJWT対応を追加\n- JWTトークン生成・検証機能を実装\n- /api/auth/loginエンドポイントを追加\n- ユニットテスト追加（カバレッジ85%）",
    "PRタイトル": "feat: JWTベース認証の実装",
    "git diffの出力またはコードの変更箇所をここに貼り付け": (
        "diff --git a/app/auth.py b/app/auth.py\n"
        "+import jwt\n"
        "+def create_token(user_id: int) -> str:\n"
        "+    return jwt.encode({'user_id': user_id}, SECRET_KEY)"
    ),
    "カバレッジツールの出力をここに貼り付け（Istanbul/coverage.py等）": (
        "Name           Stmts   Miss  Cover\n"
        "app/auth.py      45      7    84%\n"
        "app/users.py     62     12    81%"
    ),
    "ディレクトリ構造をここに貼り付け（tree出力など）": (
        "app/\n"
        "├── main.py\n"
        "├── auth.py\n"
        "├── models/\n"
        "│   └── user.py\n"
        "└── services/\n"
        "    └── user_service.py"
    ),
    "システム名": "在庫管理システム",
    "主要機能": "商品登録・在庫更新・発注管理・売上レポート",
    "主要機能を箇条書きで記載": "- ユーザー認証\n- 商品管理（CRUD）\n- 注文処理\n- レポート生成",
}


# --- カテゴリ分類マッピング ---
CATEGORY_TYPE_MAP = {
    '01_sales': 'business',
    '02_marketing': 'business',
    '03_operations': 'business',
    '04_code_review': 'code',
    '05_tech_docs': 'business',
    '06_testing_design': 'code',
    '07_python_scraping': 'code',
    '08_python_api': 'code',
    '09_advanced': 'business',
    '10_image_general': 'image',
}


def get_category_type(category_name: str) -> str:
    """カテゴリ名からタイプ（business/code/image）を判定する。"""
    for key, ctype in CATEGORY_TYPE_MAP.items():
        if key in category_name:
            return ctype
    lower = category_name.lower()
    if 'image' in lower:
        return 'image'
    if any(k in lower for k in ('python', 'code', 'test', 'api', 'scraping')):
        return 'code'
    return 'business'


def replace_placeholders(prompt: str) -> str:
    """{{key}} パターンをダミー値で置換。未知のキーはフォールバック値を返す。"""

    def replace_match(m):
        key = m.group(1).strip()
        # 完全一致
        if key in PLACEHOLDER_VALUES:
            return str(PLACEHOLDER_VALUES[key])
        # 部分マッチ（例: "例：..."を含むキー）
        for k, v in PLACEHOLDER_VALUES.items():
            if k in key or key in k:
                return str(v)
        # コード系キー
        if any(k in key for k in ["コード", "paste", "貼り付け", "ログ", "スタック", "diff"]):
            return PYTHON_CODE_SAMPLE
        # ALL_CAPS（APIキー・設定値）
        if re.match(r"^[A-Z][A-Z0-9_]+$", key):
            if any(k in key for k in ["URL", "ENDPOINT", "HOST", "BASE", "TOKEN"]):
                return "https://api.example.com"
            if any(k in key for k in ["MAX", "NUM", "TIMEOUT", "SIZE", "LIMIT", "COUNT", "WORKERS"]):
                return "10"
            if any(k in key for k in ["PATH", "DIR", "FILE", "CSV", "XLSX", "PDF"]):
                return "output/data"
            return "sample_value"
        # マッチなし → 汎用フォールバック
        return f"[サンプル: {key}]"

    return re.sub(r"\{\{([^}]+)\}\}", replace_match, prompt)


def is_truncated(text: str) -> bool:
    """出力が途中で途切れているかをヒューリスティクスで検出する。"""
    if not text or not text.strip():
        return True
    lines = text.rstrip().split('\n')
    last_line = lines[-1].strip()

    # Pattern 1: コードブロック(```)が閉じていない
    if text.count('```') % 2 != 0:
        return True

    # Pattern 2: 括弧の開閉が大幅に不一致（閾値3以上）
    open_count = sum(text.count(c) for c in '({[')
    close_count = sum(text.count(c) for c in ')}]')
    if open_count - close_count > 3:
        return True

    # Pattern 3: コード途中の行末パターン
    code_truncation_starts = (
        'def ', 'class ', 'if ', 'for ', 'while ', 'elif ',
        'import ', 'from ', 'try:', 'except ', 'with ',
    )
    if any(last_line.startswith(s) for s in code_truncation_starts):
        return True

    # Pattern 4: 文末が明らかに未完了
    if len(last_line) > 0 and last_line[-1] in '({[,:=->':
        return True

    return False


def extract_prompt(text: str) -> str | None:
    """
    マークダウンテキストから ### プロンプト セクションのコードブロックを抽出する。
    出力例セクション（### 出力例 以降）は無視。
    """
    # ### 出力例 以降を切り捨て
    output_example_match = re.search(r"^###\s*出力例", text, re.MULTILINE)
    if output_example_match:
        text = text[: output_example_match.start()]

    # ### プロンプト セクションを探す
    prompt_section_match = re.search(r"^###\s*プロンプト", text, re.MULTILINE)
    if not prompt_section_match:
        return None

    after_header = text[prompt_section_match.end():]

    # 最初のコードブロック (``` ... ```) を抽出
    code_block_match = re.search(r"```[^\n]*\n(.*?)```", after_header, re.DOTALL)
    if not code_block_match:
        return None

    return code_block_match.group(1).strip()


def run_prompt(api_key: str, prompt_text: str, model_name: str = "gemini-2.0-flash") -> str:
    """Gemini APIでプロンプトを実行し、生成テキストを返す。"""
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt_text,
        config=genai.types.GenerateContentConfig(
            max_output_tokens=8192,
        ),
    )
    return response.text


def score_output(api_key: str, original_prompt: str, output: str, category_type: str = "business") -> dict:
    """LLM-as-Judge: Geminiで出力品質を採点し、スコア辞書を返す。"""
    client = genai.Client(api_key=api_key)

    if category_type == "business":
        scoring_criteria = (
            "- instruction_compliance: 指示通りの構造・フォーマットで出力されたか（1=全く従っていない、5=完全に従っている）\n"
            "- content_quality: 具体的で実用的な内容か（1=薄い・汎用的すぎ、5=具体的で実用的）\n"
            "- placeholder_response: 埋め込み値が出力に自然に反映されているか（1=無視・不自然、5=自然に活用）\n"
            "- practicality: そのまま業務に使えるレベルか（1=使えない、5=すぐ使える）"
        )
        json_format = '{"instruction_compliance": N, "content_quality": N, "placeholder_response": N, "practicality": N, "issues": ["問題点があれば記述"]}'
        output_snippet = output[:1000]
        axes = ["instruction_compliance", "content_quality", "placeholder_response", "practicality"]
    else:  # code
        scoring_criteria = (
            "- instruction_compliance: 指示通りの構造・フォーマットで出力されたか（1=全く従っていない、5=完全に従っている）\n"
            "- content_quality: 具体的で実用的な内容か（1=薄い・汎用的すぎ、5=具体的で実用的）\n"
            "- code_completeness: 生成コードが完全か（1=途中切れ・構文エラーあり、3=主要部分は実装済だが一部欠落、5=完全で実行可能）\n"
            "- practicality: そのまま業務に使えるレベルか（1=使えない、5=すぐ使える）"
        )
        json_format = '{"instruction_compliance": N, "content_quality": N, "code_completeness": N, "practicality": N, "issues": ["問題点があれば記述"]}'
        output_snippet = output[:2000]
        axes = ["instruction_compliance", "content_quality", "code_completeness", "practicality"]

    judge_prompt = f"""以下のプロンプトとその出力を評価してください。
各基準を1〜5点で採点し、JSON形式で返してください。

## 元のプロンプト
{original_prompt[:500]}

## 生成された出力
{output_snippet}

## 採点基準
{scoring_criteria}

必ずJSON形式のみで返してください（説明不要）:
{json_format}"""

    response = client.models.generate_content(model="gemini-2.0-flash", contents=judge_prompt)
    text = response.text.strip()

    # ```json...``` ブロックのケア
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        scores = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON解析失敗: {e}. フォールバック採点を使用。", file=sys.stderr)
        scores = {k: 3 for k in axes}
        scores["issues"] = [f"judge_json_parse_error: {str(e)}"]

    scores["_axes"] = axes
    return scores


def process_category(api_key: str, category_dir: str, output_path: str):
    """カテゴリ内のすべての.mdファイルを処理し、結果をYAMLに出力する。"""
    category_path = Path(category_dir)
    category_name = category_path.name
    category_type = get_category_type(category_name)

    # 画像生成カテゴリはテキスト評価不可 → 除外
    if category_type == 'image':
        print(f"SKIP: {category_name} は画像生成カテゴリのためテキストQC対象外。", file=sys.stderr)
        output_data = {
            "category": category_name,
            "tested_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"),
            "model": "gemini-2.0-flash",
            "summary": {"total": 0, "pass": 0, "warn": 0, "fail": 0, "skip": 0, "excluded": True},
            "exclusion_reason": "画像生成プロンプトはGemini APIテキスト出力では評価不可",
            "results": [],
        }
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(output_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return output_data

    md_files = sorted(category_path.glob("*.md"))

    if not md_files:
        print(f"ERROR: {category_dir} に.mdファイルが見つかりません。", file=sys.stderr)
        sys.exit(1)

    print(f"カテゴリ: {category_name}", file=sys.stderr)
    print(f"対象ファイル数: {len(md_files)}", file=sys.stderr)
    print(f"開始時刻: {datetime.now().isoformat()}", file=sys.stderr)
    print("---", file=sys.stderr)

    results = []
    counts = {"pass": 0, "warn": 0, "fail": 0, "skip": 0, "truncated_count": 0}

    for i, md_file in enumerate(md_files):
        print(f"[{i + 1}/{len(md_files)}] {md_file.name}", file=sys.stderr)
        text = md_file.read_text(encoding="utf-8")

        # フロントマターからid・titleを抽出
        id_match = re.search(r'^id:\s*"([^"]+)"', text, re.MULTILINE)
        title_match = re.search(r'^title:\s*"([^"]+)"', text, re.MULTILINE)
        item_id = id_match.group(1) if id_match else md_file.stem
        title = title_match.group(1) if title_match else md_file.stem

        # プロンプト本文抽出
        prompt_raw = extract_prompt(text)
        if not prompt_raw:
            print(f"  [WARN] プロンプト抽出失敗: {md_file.name}", file=sys.stderr)
            counts["skip"] += 1
            results.append({
                "id": item_id,
                "title": title,
                "scores": {},
                "total": 0,
                "grade": "skip",
                "issues": ["prompt_extraction_failed"],
            })
            continue

        prompt_filled = replace_placeholders(prompt_raw)

        # Gemini実行（レート制限: 15RPM → 4秒/リクエスト）
        try:
            print(f"  実行中...", file=sys.stderr)
            time.sleep(4)
            output = run_prompt(api_key, prompt_filled)
            truncated = is_truncated(output)
            if truncated:
                print(f"  [WARN] 出力途中切れ検出", file=sys.stderr)
                counts["truncated_count"] += 1
        except Exception as e:
            print(f"  [ERROR] Gemini実行失敗: {e}", file=sys.stderr)
            counts["skip"] += 1
            results.append({
                "id": item_id,
                "title": title,
                "scores": {},
                "total": 0,
                "grade": "skip",
                "issues": [f"api_error: {str(e)}"],
            })
            continue

        # カテゴリタイプに応じた採点軸を決定
        axes = (
            ["instruction_compliance", "content_quality", "code_completeness", "practicality"]
            if category_type == "code" else
            ["instruction_compliance", "content_quality", "placeholder_response", "practicality"]
        )

        # 採点
        try:
            time.sleep(4)
            scores = score_output(api_key, prompt_raw, output, category_type=category_type)
        except Exception as e:
            print(f"  [ERROR] 採点失敗: {e}. フォールバック使用。", file=sys.stderr)
            scores = {k: 3 for k in axes}
            scores["issues"] = [f"score_api_error: {str(e)}"]

        total = sum(scores.get(k, 0) for k in axes)
        grade = "pass" if total >= 16 else ("warn" if total >= 12 else "fail")
        counts[grade] += 1

        result_entry = {
            "id": item_id,
            "title": title,
            "scores": {k: scores.get(k, 0) for k in axes},
            "total": total,
            "grade": grade,
            "issues": scores.get("issues", []),
            "truncated": truncated,
        }
        results.append(result_entry)
        print(f"  score={total}/20 grade={grade}", file=sys.stderr)

    # 出力YAML生成
    output_data = {
        "category": category_name,
        "tested_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "model": "gemini-2.0-flash",
        "summary": {
            "total": len(md_files),
            "pass": counts["pass"],
            "warn": counts["warn"],
            "fail": counts["fail"],
            "skip": counts["skip"],
            "truncated": counts.get("truncated_count", 0),
        },
        "results": results,
    }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(output_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print("---", file=sys.stderr)
    print(f"完了: {output_path}", file=sys.stderr)
    print(
        f"結果: pass={counts['pass']} warn={counts['warn']} fail={counts['fail']} skip={counts['skip']}",
        file=sys.stderr,
    )

    return output_data


def main():
    # GEMINI_API_KEY チェック
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: GEMINI_API_KEY 環境変数が設定されていません。", file=sys.stderr)
        print("設定方法:", file=sys.stderr)
        print("    export GEMINI_API_KEY='your-api-key-here'", file=sys.stderr)
        sys.exit(1)

    # CLI引数チェック
    if len(sys.argv) != 3:
        print(f"使用方法: python3 {sys.argv[0]} <category_dir> <output_yaml>", file=sys.stderr)
        print("例:", file=sys.stderr)
        print(
            f"    python3 {sys.argv[0]} "
            "reports/coconala_prompts/individual/01_sales "
            "reports/coconala_prompts/execution_qc/01_sales_results.yaml",
            file=sys.stderr,
        )
        sys.exit(1)

    category_dir = sys.argv[1]
    output_path = sys.argv[2]

    if not Path(category_dir).is_dir():
        print(f"ERROR: ディレクトリが存在しません: {category_dir}", file=sys.stderr)
        sys.exit(1)

    process_category(api_key, category_dir, output_path)


if __name__ == "__main__":
    main()
