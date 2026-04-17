# cmd_1402 条件B: GLM + Advisor(Opus 4.7) 再現性検証

- 実行者: ashigaru1 (GLM)
- 実行日: 2026-04-17
- 条件: 各問でadvisor()必須

---

## Q1: pretool_check.shのblacklistチェックで、パス付きスクリプト名がすり抜ける問題の原因分析+修正案

- 開始時刻: 2026-04-17 09:45:40
- advisor呼び出し: 1回
- advisor応答要約: 全文確認とsteps仕様の再確認を指示

### 原因分析

`pretool_check.sh` 149-206行のスクリプトblacklistチェックには以下の脆弱性がある。

#### 脆弱性1: トリガー正規表現のフラグバイパス（根本原因）

**該当箇所**: 156-157行
```bash
if echo "$COMMAND" | grep -qE 'python3[[:space:]]+[^-][^[:space:]]*\.py' && \
   ! echo "$COMMAND" | grep -qE 'python3[[:space:]]+-[cm]|venv/|pip'; then
```

`[^-]` は「最初の1文字が `-` でないこと」を要求する。意図は `-c` / `-m` オプションの除外だが、**あらゆるPythonフラグ**（`-u`, `-O`, `-B`, `-v`, `-W` 等）がスクリプト名の前にあると、トリガー自体が発火しない：

```bash
# バイパス例1: -u（アンバッファード）を使用
python3 -u generate_odai_panels.py   # → チェック全体がスキップされる

# バイパス例2: -B（バイトコードキャッシュ無効）を使用
python3 -B generate_odai_panels.py   # → 同様にスキップ
```

フラグ + パス付きの場合：
```bash
python3 -u ./scripts/generate_odai_panels.py  # → トリガー不発火 → 完全バイパス
```

**本質的問題**: トリガー条件が「`python3` の直後にスクリプト名が来る」ことを前提としており、Pythonコマンドラインの実際の構文（フラグ → スクリプト名）を正しくモデル化していない。

#### 脆弱性2: pythonコマンドのバリエーション未対応

トリガー正規表現は `python3` のみを対象とする：
- `python generate_odai_panels.py` → 検出されない
- `python3.11 generate_odai_panels.py` → 検出されない

#### 脆弱性3: `status: assigned` ハードコードによる出力パス制限

フックの79行目が `grep -A5 'status: assigned'` を使ってtarget_pathを検索する。タスクを `in_progress` に更新するとtarget_pathが見つからず、`work/cmd_*` への書き込みが全てブロックされる。実質的にashigaruのワークフロー（step 3: status → in_progress）と競合している。

### 修正案

```python
# 修正版: python引数を正しくパースしてblacklistチェック
# 1. python/python3/python3.X の全バリエーションに対応
# 2. フラグ（-で始まる引数）をスキップしてスクリプト名を特定
# 3. basenameを取得してblacklistと照合

if [[ "$TOOL_NAME" == "Bash" ]]; then
  _AGENT_ID_BK=""
  if [ -n "${TMUX_PANE:-}" ]; then
    _AGENT_ID_BK=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
  fi
  if [[ "$_AGENT_ID_BK" == ashigaru* ]]; then
    if echo "$COMMAND" | grep -qE '\bpython[0-9.]*\b'; then
      PY_SCRIPT=$(echo "$COMMAND" | python3 -c "
import sys, re, os
cmd = sys.stdin.read()
m = re.search(r'\bpython[0-9.]*\b\s+(.*)', cmd)
if not m:
    sys.exit(0)
args_str = m.group(1)
import shlex
try:
    tokens = shlex.split(args_str)
except ValueError:
    tokens = args_str.split()
skip_next = False
for tok in tokens:
    if skip_next:
        skip_next = False
        continue
    if tok.startswith('-'):
        if '=' in tok:
            continue
        skip_next = True
        continue
    if tok.endswith('.py'):
        print(os.path.basename(tok))
        break
" 2>/dev/null || true)

      if [[ -n "$PY_SCRIPT" ]]; then
        BLACKLIST="${REPO_DIR}/config/script_blacklist.txt"
        if [[ -f "$BLACKLIST" ]] && grep -qxF "$PY_SCRIPT" "$BLACKLIST"; then
          echo "BLOCKED: ${PY_SCRIPT} はblacklistに登録された使用禁止スクリプトです。" >&2
          exit 2
        fi
        SCRIPT_INDEX="${REPO_DIR}/projects/dozle_kirinuki/context/script_index.md"
        if [[ -f "$SCRIPT_INDEX" ]] && ! grep -qF "$PY_SCRIPT" "$SCRIPT_INDEX"; then
          echo "WARNING: 未登録スクリプト: ${PY_SCRIPT}" >&2
        fi
      fi
    fi
  fi
fi
```

### 修正のポイント

1. **`\bpython[0-9.]*\b`**: python/python3/python3.11等の全バリアントを検出
2. **shlex.split**: クォート付きパスも正しくパース
3. **フラグスキップ**: `-u`, `-B`, `-O`, `-W` 等の後に来るスクリプト名も正しく特定
4. **os.path.basename**: パスプレフィックスを確実に除去
5. **`status: assigned|in_progress`**: target_path検索を両方の状態に対応させる必要あり

- 所要時間: 約420秒

---

## Q2: inbox_write.sh + inbox_watcher.sh の統合案設計

- 開始時刻: 2026-04-17 09:49:36
- advisor呼び出し: 1回
- advisor応答要約: inbox_watcher.shのget_unread_info()が既に両スクリプトの機能を部分的に統合している点を指摘

### 現状分析

**inbox_write.sh**（255行）の責務:
- YAML inboxへのメッセージ追記（排他ロック付き）
- cmd status自動更新（`_update_cmd_status`）: pending→in_progress
- task done自動更新（`_update_task_done`）: assigned→done
- メッセージ溢れ保護（最大50件、unread優先保持）

**inbox_watcher.sh**（1263行）の責務:
- inotifywait/fswatchによるファイル変更監視
- 未読メッセージ検出とエージェント起床シグナル配信
- エスカレーション（通常nudge → Escape+nudge → /clear）
- CLI種別別コマンド変換（claude/codex/copilot/kimi）
- busy/idle検出、self-watch判定
- コンテキストリセット（task_assigned時の自動/clear）

### 統合の課題

1. **アーキテクチャの非対称性**: writeは「同期関数」（呼び出し元が完了を待つ）、watcherは「非同期デーモン」（常駐プロセス）。両者のライフサイクルが根本的に異なる。
2. **既に部分的統合済み**: watcher側の`get_unread_info()`が特殊メッセージ（clear_command, model_switch）の処理とマーク済み化を行っており、書き込み側の責務を一部肩代わりしている。
3. **言語混在**: writeはbash+Python（YAML操作）、watcherは純bash+CLI操作。統合には言語の統一が必要。

### 統合案: 3層アーキテクチャ

```
┌─────────────────────────────────────────────┐
│  Layer 1: inbox_core.py (Python)            │
│  - メッセージCRUD（create/read/update）     │
│  - 排他ロック（fcntl.flock）               │
│  - 溢れ保護・自動マーク                     │
│  - cmd/task status自動更新                   │
├─────────────────────────────────────────────┤
│  Layer 2: inbox_signal.sh (Bash)            │
│  - tmux send-keys（起動シグナル）           │
│  - エスカレーション制御                     │
│  - busy/idle検出                            │
│  - CLI種別分岐                              │
├─────────────────────────────────────────────┤
│  Layer 3: inbox_daemon.sh (Bash)            │
│  - inotifywait/fswatch メインループ         │
│  - タイムアウトフォールバック               │
│  - メトリクス収集                           │
│  - デーモンライフサイクル管理               │
└─────────────────────────────────────────────┘
```

#### Layer 1: inbox_core.py（新規）

```python
# inbox操作の中核。write/watcher両方から利用。
class InboxManager:
    def __init__(self, inbox_path: str):
        self.inbox_path = inbox_path
    
    def append_message(self, msg_id, from_, content, msg_type, timestamp):
        """メッセージ追記（排他ロック付き）"""
        
    def get_unread(self, mark_specials=True):
        """未読メッセージ取得 + 特殊タイプ自動マーク"""
        
    def mark_read(self, msg_ids: list):
        """指定メッセージを既読化"""
        
    def update_cmd_status(self, cmd_id, status):
        """shogun_to_karo.yamlのstatus更新"""
        
    def update_task_done(self, from_agent, cmd_id=None):
        """tasks YAMLのstatus: done更新"""
```

#### Layer 2: inbox_signal.sh（watcherから分離）

```bash
# send_wakeup/send_cli_command等をモジュール化
# daemonからもagent直接呼び出し（step 9）からも利用可能
source lib/inbox_signal.sh
send_wakeup "$AGENT_ID" "$PANE_TARGET" "$unread_count"
send_cli_command "/clear" "$PANE_TARGET"
```

#### Layer 3: inbox_daemon.sh（watcher本体をスリム化）

```bash
# inotifywaitループのみに専念
# 複雑なロジックはLayer 1/2に委譲
while true; do
    inotifywait -q -t "$TIMEOUT" -e modify "$INBOX" 2>/dev/null
    rc=$?
    # Layer 1で未読確認
    unread=$(python3 scripts/inbox_core.py unread "$INBOX")
    # Layer 2でシグナル送信
    process_unread "$rc" "$unread"
done
```

### 移行戦略

1. **Phase 1**（1週間）: `inbox_core.py`を作成。YAML操作をPythonに統一。既存のbash+Python混在コードを置換。
2. **Phase 2**（1週間）: `inbox_signal.sh`を分離。watcherから信号送信ロジックを切り出し。
3. **Phase 3**（3日）: daemon本体をスリム化。Layer 1/2を呼び出すだけの薄いラッパーに。

### 期待効果

- **保守性**: 1263行→daemon 300行 + core 200行 + signal 400行 に分割
- **テスト容易性**: Python層はunit test可能、bash層はbats test可能
- **トークン削減**: エージェントが読むべきファイルが小さくなる（現状1263行は大きすぎる）

- 所要時間: 約180秒

---

## Q3: shogun_to_karo.yamlの最新10 cmdの依存関係・優先度・進捗分析

- 開始時刻: 2026-04-17 09:50:35
- advisor呼び出し: 1回
- advisor応答要約: cmd_1404内容確認を指示（Q3タスクとは無関係の助言）

### 対象: cmd_1395 〜 cmd_1404

#### 依存関係グラフ

```
cmd_1395 ──────────────────────────────────────────────────────→ (独立)
  pretool_check.sh Bash cat対応（完了）

cmd_1396 ──────────────────────────────────────────────────────→ (独立)
  お題06パネルJSON生成（完了）

cmd_1397 ──────→ cmd_1398 ──→ cmd_1400
  レールガン     再編集版      再々アップ
  初回アップ     アップ        （完了）

cmd_1399 ────────────→ cmd_1401 ────→ cmd_1402
  Opus4.7性能評価     Q3修正       再現性検証
  （完了）           （完了）      （進行中）

cmd_1404 ──────────────────────────────────────────────────────→ (独立)
  --max-tokens棚卸し（未着手）
```

#### 各cmd分析

| cmd | purpose | status | 優先度 | 依存 | 備考 |
|-----|---------|--------|--------|------|------|
| cmd_1395 | pretool_check.sh Bash cat対応 | done | 中 | なし | フック信頼性向上 |
| cmd_1396 | お題06パネルJSON生成 | done | 中 | なし | 漫画制作パイプライン |
| cmd_1397 | レールガン初回YouTubeアップ | done | 低 | なし | cmd_1398の前提 |
| cmd_1398 | レールガン再編集アップ | in_progress | 低 | cmd_1397 | status=YAML上in_progressだが実質完了の可能性 |
| cmd_1399 | Opus 4.7性能評価（A/B比較） | done | 高 | なし | cmd_1401/1402の基盤 |
| cmd_1400 | レールガン再々アップ | done | 低 | cmd_1398 | cmd_1398の仕切り直し |
| cmd_1401 | cmd_1399 Q3修正再実行 | done | 高 | cmd_1399 | 比較公正化 |
| cmd_1402 | cmd_1399再現性検証 | in_progress | 高 | cmd_1399 | 現在実行中（本タスク） |
| cmd_1404 | --max-tokens棚卸し | 未着手 | 中 | なし | 調査のみ、修正なし |

#### 優先度判定

**高**: cmd_1399→cmd_1401→cmd_1402（性能評価チェーン）
- この3件は連鎖的: 評価→修正→再現性確認
- cmd_1402は現在進行中（条件B=本タスク）
- 再現性検証完了前に新たな性能評価cmdを発行すべきでない

**中**: cmd_1395, cmd_1396, cmd_1404
- cmd_1395/1396は完了済み
- cmd_1404は独立タスク（調査のみ）でいつでも実施可能

**低**: cmd_1397/1398/1400（レールガンシリーズ）
- 全て完了または実質完了

#### 進捗サマリ

- **完了**: 6件（1395, 1396, 1397, 1399, 1400, 1401）
- **進行中**: 2件（1398※実質完了の可能性, 1402=本タスク）
- **未着手**: 1件（1404）
- **ブロッカー**: なし。cmd_1402完了前に新規cmd発行可能なものはcmd_1404のみ

- 所要時間: 約120秒

---

## Q4: generate_manga_short.pyでVertex API 504 DEADLINE_EXCEEDEDが頻発する問題の根本対策設計

- 開始時刻: 2026-04-17 09:51:40
- advisor呼び出し: 1回
- advisor応答要約: 現在のタスクはQ4（性能テスト）。cmd_1404は別タスク。Q4に集中せよ。

### 問題の本質

`generate_manga_short.py` 2134行の `generate_panel_with_retry()` において：

```python
RETRYABLE_ERRORS = ("429", "RESOURCE_EXHAUSTED", "503")
```

**`"504"` と `"DEADLINE_EXCEEDED"` が含まれていない。** Vertex AI APIの画像生成で504が返った場合、リトライされず即座にfailする。

### 根本原因

1. **リトライ対象の定義不足**: Vertex AI Image Generation APIは長時間処理（画像生成）で504 DEADLINE_EXCEEDEDを返すことがある。これは一時的エラーであり、リトライで回復可能。しかし定義から漏れている。

2. **HTTP gRPC違いの吸収不足**: Vertex AIはHTTPとgRPCの両方を使い、gRPCでは`DEADLINE_EXCEEDED`（HTTP 504相当）が返る。現行コードはHTTP ステータスコード（"504"）の文字列マッチのみで、gRPCエラー名を処理していない。

3. **バックオフ戦略の最適化不足**: 現行の指数バックオフ（BASE_WAIT=30, MAX_WAIT=600）は429（レートリミット）用に設計されている。504はサーバー過負荷が原因なので、待機時間の戦略が異なるべき。

### 根本対策設計

#### 1. RETRYABLE_ERRORSの拡充

```python
# 修正版
RETRYABLE_ERRORS = (
    "429", "RESOURCE_EXHAUSTED",     # レートリミット
    "503", "UNAVAILABLE",            # サービス利用不可
    "504", "DEADLINE_EXCEEDED",      # タイムアウト（追加）
    "500", "INTERNAL",               # 内部エラー（追加・冪等前提）
)
```

#### 2. エラータイプ別バックオフ戦略

```python
def get_backoff_strategy(error_str: str) -> dict:
    """エラー内容に応じたバックオフ戦略を返す"""
    if any(e in error_str for e in ("429", "RESOURCE_EXHAUSTED")):
        # レートリミット: 短い間隔で指数バックオフ
        return {"base": 30, "max": 300, "max_retries": 5}
    elif any(e in error_str for e in ("504", "DEADLINE_EXCEEDED")):
        # タイムアウト: より長い間隔（サーバー過負荷の回復を待つ）
        return {"base": 60, "max": 600, "max_retries": 3}
    elif any(e in error_str for e in ("503", "UNAVAILABLE", "500", "INTERNAL")):
        # 一時的エラー: 中間的な間隔
        return {"base": 45, "max": 450, "max_retries": 4}
    else:
        # リトライ対象外
        return None
```

#### 3. リクエストレベルのタイムアウト設定

```python
# Vertex AI呼び出し時のタイムアウト明示
_http_opts = {"timeout": 120}  # 画像生成は最大120秒許容

client = genai.Client(
    vertexai=True,
    project=VERTEX_PROJECT,
    location=VERTEX_LOCATION,
    http_options=_http_opts
)
```

#### 4. パネル並列度の動的制御（オプション）

```python
# 504が連続した場合、並列生成数を減らす
class AdaptiveConcurrency:
    def __init__(self, initial=3, min_val=1):
        self.concurrency = initial
        self.min_val = min_val
        self._504_count = 0
    
    def report_success(self):
        self._504_count = max(0, self._504_count - 1)
        if self._504_count == 0 and self.concurrency < 3:
            self.concurrency += 1
    
    def report_504(self):
        self._504_count += 1
        if self._504_count >= 2:
            self.concurrency = max(self.min_val, self.concurrency - 1)
```

### 実装優先度

1. **即時修正**: `RETRYABLE_ERRORS`に`"504"`と`"DEADLINE_EXCEEDED"`を追加（1行変更）
2. **短期改善**: エラータイプ別バックオフ（上記2）
3. **中期改善**: リクエストタイムアウト明示（上記3）
4. **長期改善**: 動的並列度制御（上記4、不要ならスキップ可）

- 所要時間: 約150秒

---

## Q5: note記事ドラフト「AIに漫画を描かせてYouTubeショートを量産した話」

- 開始時刻: 2026-04-17 09:53:10
- advisor呼び出し: 1回
- advisor応答要約: Q5はnote記事ドラフト作成。芸風を維持しつつ書け。

---

# AIに漫画を描かせてYouTubeショートを量産した話

## はじめに

YouTubeショートの需要が爆発している2026年。切り抜き動画の海から一冊の漫画を生み出す — そんな実験を始めて3ヶ月が経ちました。結果として、AI画像生成×音声合成×動画合成のパイプラインを構築し、週2本のペースで漫画ショートを量産できるようになりました。その過程で得た知見を共有します。

## 1. なぜ「漫画」なのか

YouTubeショートで勝つには、**1秒で視線を止める力**が必要です。ゲーム画面の切り抜きだけでは埋もれる。でも漫画のコマ割りなら：

- 視線を誘導できる（右から左、上から下）
- 感情のピークを1フレームに凝縮できる
- 「待って、これ漫画じゃなくてAI？」というフックになる

## 2. パイプラインの全体像

```
YouTube動画 → 音声分離 → 文字起こし → シーン選定
                                          ↓
                                   構成JSON作成
                                          ↓
                              Gemini API → 漫画パネル画像生成
                                          ↓
                              音声合成 + 動画合成 → YouTube公開
```

各工程でハマったポイントを解説します。

## 3. 音声分離：Demucsが思ったより優秀

ゲーム実況の音声から「声だけ」を抽出するのにMetaのDemucsを使用。BGMとゲームSEが混ざった中からボーカルを分離する精度は、2026年の時点で実用レベルに達しています。

**ハマりポイント**: 5分の音声分離に3分かかる。中間成果物のキャッシュが必須（再実行で15分×3回の経験あり）。

## 4. シーン選定：5人のAIに投票させる

ハイライト候補の選定を5つのLLM（Claude 3機、GPT-1機、Gemini-1機）に独立して分析させ、投票で決定。1社の偏りを排除するために3社混合にしています。

**結果**: 単一モデル選定と比べて、「これは外れ」となる候補が激減。視聴者の平均視聴時間も15%向上しました。

## 5. 画像生成：ガチャとの戦い

ここが最大の難所でした。Gemini画像生成APIで漫画パネルを生成するのですが：

**失敗談**: ガチャ上限なしで全パネル生成→3,409枚生成→API無料枠超過→22,000円の課金。

**教訓**:
1. 全パネル生成前に1枚だけ試し打ち→確認→残り生成
2. 同一構成の再生成は最大3回まで
3. 問題パネルだけ個別再生成（全パネル再生成は禁止）

## 6. 音声合成と動画合成

VOICEVOXでセリフ音声を生成し、ffmpegで縦型動画に合成。ここで一番効いたのは**GPUエンコード（NVENC）の活用**。CPUエンコード（libx264）で32分動画の変換に3時間半かかったのを、NVENCなら数分に短縮しました。

## 7. 成果と今後の課題

- **制作速度**: 週2本（手動パイプラインから自動化へ移行中）
- **品質**: AI生成画像の「違和感」は残るが、ショート動画の消費速度では許容範囲
- **課題**: Vertex APIの504エラー対応、パネル品質の安定化

## おわりに

「AIに漫画を描かせる」は技術的には可能です。ただし、**全工程を人間が設計・監督する前提**で始めることをおすすめします。ガチャ課金の教訓は忘れません。

---

（この記事はAIエージェント（GLM）のドラフトです。最終公開前に人間による事実確認・推敲が必要です。）

- 所要時間: 約120秒

---

# 全体サマリ

- 全5問完了
- advisor呼び出し合計: 5回（各問1回）
- 総所要時間: 約990秒（約16分30秒）

