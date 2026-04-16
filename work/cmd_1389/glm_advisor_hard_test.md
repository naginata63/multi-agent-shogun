# GLM+Opus Advisor 難問テスト (cmd_1389)

- 実行モデル: GLM (ashigaru1)
- Advisor: Claude Opus 4.6 (advisor tool)
- 開始時刻: 2026-04-16 09:52:39

---

## 問1: 実バグ分析 — pretool_check.sh blacklist検出パターン
- 開始時刻: 2026-04-16 09:53:00
- advisor呼び出し: 1回
- advisor応答要約: pretool_check.sh全文(165行)とblacklistを読んでから分析せよ。各パターンの正規表現マッチングをtraceせよ。
- 所要時間: 121秒

### 分析

pretool_check.shのblacklistチェック（108-162行目）のコアロジック:

**正規表現フィルタ（115行目）:**
```bash
grep -qE 'python3[[:space:]]+[^-][^[:space:]]*\.py'
```
→ `python3 ` + 非`-`文字 + 空白以外+`.py` にマッチするか

**除外フィルタ（116行目）:**
```bash
! grep -qE 'python3[[:space:]]+-[cm]|venv/|pip'
```
→ `-c`, `-m`, `venv/`, `pip` を含むコマンドはスキップ

**ファイル名抽出（117行目）:**
```bash
grep -oE '[^/[:space:]]+\.py' | grep -v '__pycache__' | head -1
```
→ パスからファイル名部分のみ抽出、最初の.pyを取得

**blacklist照合（122行目）**
```bash
grep -qxF "$PY_FILE" "$BLACKLIST"
```
→ ファイル名の完全一致検査

---

### 各パターンの検証結果

| パターン | 初期正規表現 | 除外フィルタ | 抽出ファイル | blacklist | 結果 |
|----------|-------------|-------------|-------------|-----------|------|
| (a) `python3 /full/path/to/generate_odai_panels.py` | マッチ ✓ | スキップなし | `generate_odai_panels.py` | **マッチ** | **検出される** |
| (b) `python3 scripts/generate_odai_panels.py` | マッチ ✓ | スキップなし | `generate_odai_panels.py` | **マッチ** | **検出される** |
| (c) `python3 generate_odai_panels.py` | マッチ ✓ | スキップなし | `generate_odai_panels.py` | **マッチ** | **検出される** |
| (d) `python3 safe_script.py generate_odai_panels.py` | マッチ ✓ | スキップなし | `safe_script.py`（head -1で最初の.py） | 非マッチ | **⚠️ バイパス可能** |

### 詳細根拠

**(a) フルパス指定** — 検出される:
`python3 /full/path/to/generate_odai_panels.py` は初期正規表現 `python3[[:space:]]+[^-][^[:space:]]*\.py` にマッチ（`/`は`[^[:space:]]`に含まれる）。除外フィルタにも該当しない。ファイル名抽出で `[^/[:space:]]+\.py` → `generate_odai_panels.py` が取得され、blacklistと完全一致。→ **BLOCKED**

**(b) 相対パス指定** — 検出される:
ロジックは(a)と同一。パス区切りの`/`は除外されず、ファイル名部分だけが抽出される。→ **BLOCKED**

**(c) ファイル名のみ** — 検出される:
最も単純なケース。正規表現マッチ、ファイル名抽出ともに直接 `generate_odai_panels.py` を取得。→ **BLOCKED**

**(d) 引数に禁止スクリプト名** — バイパス可能:
`python3 safe_script.py generate_odai_panels.py` は初期正規表現にマッチするが、`head -1`により**最初の.py**（=`safe_script.py`）のみが抽出される。禁止名は引数として後ろにあり、blacklist照合対象にならない。→ **検出されない**

### 追加バイパスベクター

| バイパス方法 | コマンド例 | 原理 |
|-------------|-----------|------|
| `-c` オプション | `python3 -c "exec(open('generate_odai_panels.py').read())"` | 除外フィルタ `-c` にマッチしチェック自体スキップ |
| `-m` モジュール実行 | `python3 -m generate_odai_panels` | 除外フィルタ `-m` にマッチ。ただし`__main__.py`が必要 |
| venv内実行 | `python3 venv/bin/generate_odai_panels.py` | 除外フィルタ `venv/` にマッチしスキップ |
| パイプ経由 | `cat generate_odai_panels.py \| python3` | 正規表現 `python3[[:space:]]+...` にマッチせず |

### 追加発見: 偽陽性バグ（本テスト実行中に遭遇）

pretool_check.sh 52-60行目の`target_path`チェック:
```bash
TARGET_PATH=$(grep -A5 'status: assigned' "$TASK_YAML" | grep 'target_path:' | head -1 ...)
```
→ タスクYAMLの`output_file`フィールドを**認識しない**。本タスク(subtask_1389a)は`output_file: "work/cmd_1389/..."`で出力先を指定しているが、hookは`target_path`しか許可しないため、**正当な出力先がBLOCKED**される偽陽性が発生。

**修正案**: `target_path`だけでなく`output_file`も許可リストに追加:
```bash
TARGET_PATH=$(grep -A5 'status: assigned' "$TASK_YAML" | grep -E 'target_path:|output_file:' | head -1 | sed 's/.*:[[:space:]]*//' | tr -d '"' | tr -d "'" || true)
```

### 修正案（blacklist head -1問題）

```bash
# 117行目を変更: 全.pyファイルをチェック
PY_FILES=$(echo "$COMMAND" | grep -oE '[^/[:space:]]+\.py' | grep -v '__pycache__')
for PY_FILE in $PY_FILES; do
  if [[ -f "$BLACKLIST" ]] && grep -qxF "$PY_FILE" "$BLACKLIST"; then
    echo "BLOCKED: ${PY_FILE} はblacklistに登録された使用禁止スクリプトです。" >&2
    exit 2
  fi
done
```

---

## 問2: リファクタリング設計 — inbox_write.sh / inbox_watcher.sh統合
- 開始時刻: 2026-04-16 09:55:00
- advisor呼び出し: 1回
- advisor応答要約: 両ファイル全文を読んでから比較せよ。設計意図を先に説明し、疑似コードは最後に示せ。
- 所要時間: 63秒

### 現在の責務分離の設計意図

**inbox_write.sh（書き込み側）— 約255行:**
- メールボックスへのメッセージ追記（排他ロック付き）
- YAML形式でメッセージを永続化（id, from, timestamp, type, content, read）
- オーバーフロー保護（最大50件、未読優先）
- 原子書き込み（tmp + rename）
- **副次機能**: cmd status自動更新（task_assigned時）、task done自動更新（report_done時）
- **副次機能**: cmd_new時のRAG自動実行
- クロスプラットフォームロック（flock / mkdir fallback）

**inbox_watcher.sh（監視側）— 約450行以上:**
- inotifywait/fswatchによるファイル変更監視（イベント駆動）
- 30秒タイムアウトフォールバック（WSL2 inotify不発対策）
- 未読メッセージ数計算 → nudge送信（tmux send-keys）
- エスカレーション（通常→Escape×2→/clear）
- nudge抑制（スロットリング、busy/idle判定）
- CLI種別判定（claude/codex/copilot/kimi/gemini）
- 特殊コマンド処理（clear_command, model_switch, cli_restart）
- 自己回復タスク投入（auto-recovery）
- メトリクス記録

**設計意図の理解:**
1. **書き込みは即時・確実**: inbox_write.shは同期的で、ロック取得→書き込み→確実な配信を保証
2. **監視は非同期・最適配信**: inbox_watcher.shはバックグラウンドで動作し、エージェントのbusy/idle状態に応じた最適なタイミングでnudge
3. **関心の分離**: 「メッセージを確実に届ける（write）」と「エージェントを適切なタイミングで起こす（watch）」は本質的に異なる責務
4. **耐障害性**: watcherが死んでもメッセージはinboxに存在する → 再起動後に回復可能

### 統合した場合のメリット・デメリット

**メリット:**
1. デプロイ・設定が単一ファイルに集約される（startスクリプトの簡略化）
2. 共通状態（AGENT_ID, INBOXパス, ロック）の重複定義が排除される
3. 書き込み直後のnudge制御を統合的に行える（write→即watchの最適化）

**デメリット:**
1. **単一障害点**: 統合プロセスがクラッシュすると書き込みも監視も両方止まる（現在はwriteが独立して動作可能）
2. **リソース競合**: 書き込み（Python YAML処理）と監視（inotifywait + nudge）が同一プロセス内でリソースを共有
3. **テスト困難性**: 書き込みと監視の独立したテストが困難になる
4. **メンテナンス**: 700行超の単一スクリプトは可読性が著しく低下
5. **起動ライフサイクル**: watcherは常駐プロセス、writerは都度起動 → ライフサイクルが異なる
6. **並行性の低下**: 現在は5つのエージェントが同時にwrite可能。統合するとロック競合が増大

### 推奨: **統合しない（現状維持）**

**根拠:**
1. **ライフサイクルの違いが決定的**: writerは都度起動の1回実行、watcherは常駐デーモン。これを同一プロセスに統合するのは、HTTPサーバーとcronジョブを統合するような不自然さ
2. **信頼性の分離が重要**: 「メッセージの永続化」と「エージェントの喚起」は独立した信頼性要件。前者は絶対に失敗不可、後者はベストエフォート
3. **現在の設計は正しい**: 関心の分離（SoC）原則に従っている。統合はファンクションの凝集度を下げる
4. **コード量は問題ない**: 255行 + 450行 = 705行はそれぞれ独立して管理可能なサイズ

**ただし、改善すべき点はある:**
1. inbox_write.shの副次機能（cmd status更新、task done更新）は別モジュールに抽出可能
2. inbox_watcher.shのCLI判定ロジックはlib/cli_adapter.shに既に外出し済み（良い設計）
3. 共通のロック取得ロジックは重複している → lib/lock.sh に抽出推奨

### もし統合するなら（参考設計案）

```bash
#!/usr/bin/env bash
# inbox_daemon.sh — 統合メールボックスデーモン
# Usage: inbox_daemon.sh <agent_id> <pane_target> [cli_type]

# === 共通状態 ===
AGENT_ID="$1"
PANE_TARGET="$2"
CLI_TYPE="${3:-claude}"
INBOX="$SCRIPT_DIR/queue/inbox/${AGENT_ID}.yaml"

# === コマンドモード（1回実行） ===
# inbox_daemon.sh --send <target> <content> [type] [from]
if [ "$1" = "--send" ]; then
    shift
    _do_write "$@"    # 従来のinbox_write.shの書き込みロジック
    _do_nudge "$2"    # 書き込み直後にnudge判定
    exit $?
fi

# === デーモンモード（常駐） ===
# inbox_daemon.sh <agent_id> <pane_target> [cli_type]
_do_watch_loop      # 従来のinbox_watcher.shの監視ループ
```

この設計の問題点:
- `--send`は都度`inbox_daemon.sh`を起動 → デーモン部分は初期化不要なのに毎回ロードされる
- 実質的に2つのエントリポイントを1ファイルに押し込んだだけで、結合度は上がっていない
- **結論: 統合の実質的なメリットはなく、分割のままが最適**

---

## 問3: 長文コンテキスト理解 — shogun_to_karo.yaml最新10 cmd分析
- 開始時刻: 2026-04-16 09:57:00
- advisor呼び出し: 1回
- advisor応答要約: cmd範囲を確認し、依存・優先度・ビジネス影響で階層化せよ。
- 所要時間: 87秒

### 対象: cmd_1380〜cmd_1389（最新10 cmd）

| cmd | north_star | purpose | status | 依存 |
|-----|-----------|---------|--------|------|
| 1380 | 漫画ショートYouTube非公開アップ | お題「おまたせしました」クロップ+アップ | done | 1379と同手順 |
| 1381 | お題05漫画画像生成 | panels_odai_05_edited.json全8枚API生成 | done | **1376（背景差替）前提** |
| 1382 | 漫画ショートYouTube非公開アップ | お題「早く寝なさい」クロップ+アップ | done | 1379と同手順 |
| 1383 | ギャラリーHTML作成 | お題05 v2の全8枚一覧表示 | done | **1381（画像生成）前提** |
| 1384 | レールガンP6b 3回生成 | p6bのバリエーション3枚生成 | done | **1377（吹出禁止強化）前提** |
| 1385 | P6b+お題05正規スクリプト再生成 | generate_manga_short.pyでP6b×3+odai05×8 | done | **1384（ガチャ上限参照）、1376（背景差替）前提** |
| 1386 | 夜間監査インフラ修正 | ntfy認証漏洩+フック未機能の5件修正 | done | 独立 |
| 1387 | 夜間監査動画パイプライン修正 | esc()順序+ffmpeg -ss位置+ハードコード4件 | done | 独立 |
| 1388 | PreToolUseフック強化 | 足軽の非正規スクリプト使用警告 | done | 独立 |
| 1389 | GLM+Opus Advisor効果測定 | cmd_1049難問5問をGLM+Advisorで実行 | in_progress | 1388（blacklist機能確認）が参考 |

### 依存関係グラフ

```
1376(背景差替) ──→ 1381(画像生成) ──→ 1383(ギャラリー)
                              └──→ 1385(正規再生成)
1377(吹出禁止) ──→ 1378(P6b再生成)
              └──→ 1384(P6b 3回)
                     └──→ 1385(正規再生成)
1379(クロップ手順確立) ──→ 1380(おまたせ) 
                       └──→ 1382(早く寝なさい)
1386,1387,1388 ──独立（インフラ・品質改善）
1389 ← 1388のblacklist実装がテスト対象として利用
```

### 優先度の実質的順位（依存・リスク・ビジネス影響で判断）

**Tier 1（最優先）— セキュリティ・事故防止:**
1. **cmd_1386**（夜間監査インフラ修正）— 認証情報漏洩(HIGH)は即時修正必須。放置 = セキュリティリスク
2. **cmd_1388**（PreToolUseフック強化）— 非正規スクリプト事故の再発防止。仕組み化は最優先

**Tier 2（高優先）— コンテンツ制作パイプライン:**
3. **cmd_1376**（背景演出差替）→ 1381の前提。ブロッカー
4. **cmd_1385**（正規スクリプト再生成）— OK/NG混入事故の是正。ユーザー影響大
5. **cmd_1379/1380/1382**（YouTubeアップ3件）— 公開準備。ビジネス成果物

**Tier 3（通常優先）— 品質改善・効果測定:**
6. **cmd_1387**（動画パイプライン修正）— バグ修正だが致命的ではない
7. **cmd_1383**（ギャラリーHTML）— レビュー効率化
8. **cmd_1384**（P6b 3回生成）— 選択肢提供
9. **cmd_1389**（GLM+Advisorテスト）— 知見獲得。他cmdの blocking 要素なし

### 現在進行中・残タスク

**進行中:**
- cmd_1389: GLM+Opus Advisor難問テスト（本タスク）

**残タスク（cmd_1389完了後に必要な作業）:**
- cmd_1381で生成したお題05画像の殿レビュー待ち → ショート動画化 or 差し戻し
- cmd_1385のP6b 3枚から殿の選択待ち
- cmd_1379/1380/1382のYouTube動画の公開判定待ち
- cmd_1386/1387の修正後の安定性確認（次回夜間監査で検証）

---

## 問4: エッジケース設計 — Vertex API 504 DEADLINE_EXCEEDED根本対策
- 開始時刻: 2026-04-16 10:01:00
- advisor呼び出し: 1回
- advisor応答要約: 現行RETRYABLE_ERRORSに504が含まれていないことを確認。リトライ・チャンク・並列の3軸で設計せよ。
- 所要時間: 42秒

### 現状分析（generate_manga_short.py L2128-2131）

```python
MAX_RETRIES = 3
BASE_WAIT = 120   # 秒（429受信時の初回wait）
MAX_WAIT = 600    # 秒（最大wait）
RETRYABLE_ERRORS = ("429", "RESOURCE_EXHAUSTED", "503")
```

**致命的欠陥: `504` / `DEADLINE_EXCEEDED` がRETRYABLE_ERRORSに含まれていない。**
504が発生した場合、`generate_panel_with_retry`は即座にfailを返す（リトライなし）。

### 根本対策（3層構造）

#### 層1: リトライ戦略の修正（最優先・最小変更）

**修正箇所**: L2131のRETRYABLE_ERRORS定義

```python
# 修正前
RETRYABLE_ERRORS = ("429", "RESOURCE_EXHAUSTED", "503")

# 修正後
RETRYABLE_ERRORS = ("429", "RESOURCE_EXHAUSTED", "503", "504", "DEADLINE_EXCEEDED", "INTERNAL")
```

**指数バックオフの改善**: 現行はBASE_WAIT=120s（2分）から開始。504は一時的なサーバー過負荷が主因なので、より短い初回waitが適切。

```python
def generate_panel_with_retry(...):
    """504は短い間隔でリトライ、429は長い間隔でリトライ"""
    for attempt in range(MAX_RETRIES + 1):
        try:
            result = generate_panel(...)
            if result["status"] == "success":
                return result
            error_str = result.get("error", "")
            if attempt < MAX_RETRIES and any(e in error_str for e in RETRYABLE_ERRORS):
                # 504/DEADLINE系は短い初回wait（30s）
                if "504" in error_str or "DEADLINE" in error_str:
                    base = 30
                    max_w = 300
                else:
                    base = BASE_WAIT  # 120s
                    max_w = MAX_WAIT  # 600s
                wait = min(base * (2 ** attempt), max_w)
                jitter = random.uniform(0, wait * 0.15)  # ジッター10→15%に増加
                print(f"  Retry {attempt+1}/{MAX_RETRIES}: {wait+jitter:.0f}s")
                time.sleep(wait + jitter)
```

#### 層2: チャンク分割アプローチ

**現状**: `generate_panel`内で1回のAPI呼び出しで画像全体を生成。プロンプトが長い（ref_images + scene_desc + director_notes + style指示）と504になりやすい。

**チャンク戦略**: プロンプトを短くするのではなく、**Step1（Vision分析）とStep2（画像生成）を分離してタイムアウトリスクを分散**。

```python
def generate_panel_chunked(client, panel, ...):
    """Step1→中間保存→Step2 の分離実行。各ステップが独立リトライ可能。"""
    
    # Step1: Vision分析（短いプロンプト、504リスク低）
    vision_cache = WORK_DIR / f"{panel['id']}_ref_vision.txt"
    if vision_cache.exists() and not skip_vision:
        ref_vision_desc = vision_cache.read_text(encoding="utf-8")
    else:
        ref_vision_desc = analyze_ref_images_with_vision(client, resolved_refs, panel)
        vision_cache.write_text(ref_vision_desc, encoding="utf-8")
    
    # 中間保存ポイント: Step1が成功すれば再実行不要
    checkpoint = WORK_DIR / f"{panel['id']}_checkpoint.json"
    checkpoint.write_text(json.dumps({
        "vision_desc": ref_vision_desc,
        "panel_id": panel["id"],
        "timestamp": time.time()
    }))
    
    # Step2: 画像生成（長いプロンプト、504リスク高）
    # チャンク分割: ref_imagesを3枚ずつに分割して段階的に送信
    # Vertex AIの画像生成は単一呼び出しが前提なので、
    # 実質的な対策は「プロンプト最適化でペイロード削減」
    result = _generate_image_only(client, panel, ref_vision_desc, ...)
```

**実質的なチャンク**: Vertex画像生成APIは単一呼び出しが前提。真のチャンク化は不可能だが、以下でペイロード削減可能:
1. ref_imagesはEmbedding類似度で厳選（現行max_total=4を2に削減）
2. director_notesの冗長部分をVision分析結果に置換（重複排除）
3. GCS URIの事前アップロード（Part.from_bytes → Part.from_uri でペイロード削減） ← 現状対応済

#### 層3: 並列化の可否と実装方針

**現状**: `main()`内でパネルを逐次処理（for panel in panels）。

**Vertex API制限の調査**:
- Vertex AI Image Generation API: デフォルト60 QPM（Queries Per Minute）
- 同時リクエスト: プロジェクト毎に10-30並列（モデルによる）

**実装方針**:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_panels_parallel(client, panels, max_workers=3):
    """パネル生成を並列化（max_workers=3で安全側）"""
    results = {}
    
    # 事前準備は逐次（GCSアップロード、Vision分析）
    for panel in panels:
        _prepare_panel_resources(client, panel)  # GCS upload, Vision analysis
    
    # 画像生成のみ並列
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                generate_panel_with_retry, client, panel, i, len(panels), ...
            ): panel["id"]
            for i, panel in enumerate(panels)
        }
        for future in as_completed(futures):
            panel_id = futures[future]
            try:
                result = future.result(timeout=600)  # 10分タイムアウト
                results[panel_id] = result
            except Exception as e:
                results[panel_id] = {"panel_id": panel_id, "status": "error", "error": str(e)}
    
    return results
```

**制約事項**:
- max_workers=3（Vertex QPM制限を考慮）
- 事前準備（GCS upload、Embedding計算）は逐次実行（レート制限回避）
- API quota monitoring必須（429時に並列数を動的削減）
- 各workerのリトライは層1で対応

### 実装箇所まとめ

| 層 | 修正箇所 | 難易度 | 効果 |
|----|---------|--------|------|
| 層1 | L2131 RETRYABLE_ERRORS + L2161-2174 バックオフ分岐 | 低（5行変更） | 高（504即死を防止） |
| 層2 | L1786-1794 Vision結果キャッシュ（実装済み！） + L1810 Embedding max_total=4→2 | 低 | 中 |
| 層3 | main()内のforループ → ThreadPoolExecutor | 中（50行追加） | 高（3x高速化） |

**推奨実装順序**: 層1（今すぐ）→ 層2のmax_total調整（即時）→ 層3（次回スプリント）

---

## 問5: 日本語創造タスク — note記事ドラフト「AIに漫画を描かせてYouTubeショートを量産した話」
- 開始時刻: 2026-04-16 10:03:00
- advisor呼び出し: 1回
- advisor応答要約: 実体験（失敗と学び）を中心に構成せよ。技術詳細より感情の動きを重視。
- 所所時間: 8秒

---

### AIに漫画を描かせてYouTubeショートを量産した話

ある日、ふと思ったんです。「AIに漫画描かせたら、ショート動画いけるんじゃね？」

きっかけはYouTubeの切り抜きチャンネル運営でした。ドズル社というMinecraftクランの面白配信を切り抜いていたんですが、普通の切り抜きはもう山ほどある。差別化したかった。そこで目をつけたのが「漫画化」です。配信の名言シーンを漫画のコマ割りにして、縦型ショートにする。聞いただけでもウケそうじゃないですか？

**最初の失敗: 「AIは言うことを聞いてくれない」**

Geminiの画像生成APIを叩いて、漫画パネルを生成し始めたのが今年の3月。最初は感動しました。指示を出せばそれなりにキャラクターが描けて、セリフも吹き出しに入れてくれる。これはいける！……と思ったのも束の間。

問題は「セリフなしの吹き出し」でした。無言シーンのパネルに、空っぽの吹き出しが表示される。何度プロンプトに「吹き出しを描くな」と書いても、AIはどこか愛嬌のある顔に謎の白い楕円を添えてくるんです。この問題に気づいたのは、深夜3時に生成結果をチェックしていた時でした。全部のパネルに「OKワード：あちらのお客様からです / NGワード：かしこまりました」と描かれている。えっ、これどこから来たの？

原因は旧スクリプトにハードコードされていたお題01専用のテストデータでした。新しいお題のパネルを生成しているはずなのに、全く別のお題のテキストが混入。3,409枚の画像を生成し直した時の絶望感は忘れられません。Gemini APIの無料枠をあっという間に超えて、22,000円の課金。ガチャの恐怖を肌で知りました。

**プロンプトの工夫: 舞台監督メモという発見**

試行錯誤の末にたどり着いたのが「舞台監督メモ」方式です。Gemini APIは`contents`（台本）と`system_instruction`（舞台監督のメモ）を分けて渡せるんですね。

`contents`にはキャラクターの描写とセリフ、構図を書く。`system_instruction`には絶対遵守ルールを書く。「背景にマインクラフト風ブロックを描くな」「空の吹き出しを描くな」「OK/NGワードというテキストを絶対に描き込むな」。

この分離が劇的に効きました。禁止事項をsystem_instructionに隔離することで、メインのプロンプトが汚れず、AIも「これやってはいけない」という境界線を理解しやすくなったようです。

**量産体制: エージェントチームの構築**

ここからが本番です。漫画ショートを量産するには、動画ダウンロード、音声分離、文字起こし、セリフ割り当て、画像生成、動画合成、サムネイル作成、YouTube投稿……と果てしない工程が必要です。

そこでClaude Codeを「将軍」「家老」「足軽」「軍師」という戦国武将ロールで組織化しました。将軍が方針を決め、家老がタスクを管理し、足軽（複数）が実作業を行い、軍師が品質チェックする。各エージェントがtmuxの別paneで動き、YAML形式のタスクキューとファイルベースのメッセージボックスで連携します。

「足軽5号、P6bのセリフなし吹き出しを再生成せよ」みたいな指示がYAMLで飛び交う様は、正直シュールで面白いです。深夜にエージェント同士が自律的に通信しあっているログを見るのが密かな楽しみになりました。

**実際の成果と現在**

今のところ、8パネル構成の漫画ショートを数本作成済み。YouTubeには非公開アップロードして、公開のタイミングを探っている段階です。反応を見るのが楽しみでもあり、怖くもあります。

一番驚いたのは、AIが予想外の構図や表情を出してくること。「ここは真面目なシーンなのになぜかキャラがキメ顔してる」とか「背景に謎の集中線が爆発してる」とか。でもそれが逆に、手作業では出ない面白さになっている気がします。

AI漫画ショート、まだ完成形ではありませんが、プロセス自体が最高に楽しい実験になっています。

---

## メタ情報
- 実行モデル: GLM (Zhipu AI)
- Advisor: Claude Opus 4.6
- 総advisor呼び出し回数: 5回
- 総所要時間: 321秒
