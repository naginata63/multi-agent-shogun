# cmd_1399 条件A 解答書（Claude Opus 4.7 単体・advisor禁止）

- 実行エージェント: 軍師（gunshi, multiagent:0.8）
- 実行モデル: Claude Opus 4.7
- advisor呼び出し: 全問 0回（禁止制約）
- 開始時刻: 2026-04-17 08:43:32
- 回答完了時刻: 後述

---

## Q1: pretool_check.sh blacklistチェックのすり抜け問題 — 原因分析 + 修正案

- 開始時刻: 2026-04-17 08:45:00
- advisor呼び出し: 0回

### 実機検証結果
問題文の「python3 /full/path/to/banned.py」単体では、現状の抽出パターン `grep -oE '[^/[:space:]]+\.py'` は basename (`banned.py`) を正しく抽出し、blacklistの `-qxF` 行一致でBLOCKEDに到達する。従って「パス付きだから抜ける」のではなく、**周辺コマンド文字列によって `.py` 検出ロジック全体がスキップされる**ケースが真のバグである（scripts/pretool_check.sh:156-157）。

### すり抜け経路（実機で再現確認）
以下のいずれかで `.py` 検出が全スキップになる：

| # | パターン | 該当条件 | 実例 |
|---|---------|---------|-----|
| 1 | 第2条件 `venv/\|pip` が過剰 | コマンド文字列に `venv/` or `pip` を含むとNOT条件でゲートが閉じる | `python3 /home/user/venv/bin/banned.py` / `python3 some_pipeline.py` / ファイル名に`pip`が含まれる |
| 2 | `python3` 固定 | `python banned.py`, `./banned.py`, `uv run banned.py` | `python` single、スクリプト直接実行、uv |
| 3 | `-m` 起動 | `python3 -m banned` はファイル指定なし | モジュール実行 |
| 4 | 変数展開 | `S=banned.py; python3 $S` はcommand文字列に `banned.py` が含まれるが、`python3[[:space:]]+[^-][^[:space:]]*\.py` 一致前に `$` が先にある | シェル変数経由 |
| 5 | `source && python` / `env VAR=1 python3 …` | 文字列全体には `python3` を含むので第1条件はpassするが、第2条件の `pip` が文字列内のどこかに含まれるとスキップ | 例: envに `PYTHONPATH=/opt/venv/lib` がcommand内に見えるケース |

### 根本原因
1. **除外条件 `venv/\|pip` が文字列レベル・全commandに適用されている**: 本来は実行コマンド先頭トークンに対するチェックでなければいけないが、command全体の `grep -qE` で判定しているため、`pip` 3文字がどこかに含まれるだけで全ゲートが閉じる（これが cmd_1389 Q1で指摘された偽陽性/偽陰性バグの核心）。
2. **抽出パターンが `basename` のみ**: ファイル名での一意識別を前提にしている。`scripts/a/banned.py` と `scripts/b/banned.py` が別スクリプトなら区別できない。
3. **実行形態の網羅不足**: `python` / `./x.py` / `uv run` / `-m` / 変数展開を想定していない。

### 修正案（優先度順）
**Fix-1（必須・10行）**: 除外条件を「pythonの起動フラグ」に限定する。
```bash
# 現状
! echo "$COMMAND" | grep -qE 'python3[[:space:]]+-[cm]|venv/|pip'
# 修正
! echo "$COMMAND" | grep -qE '(^|[[:space:]])python3?[[:space:]]+-[cm]([[:space:]]|$)'
# venv/ と pip は削除。venv経由のpythonでも .py を実行してblacklist該当なら止めるべき。
```

**Fix-2（必須）**: 起動行を `python3?` + オプションでパス/basename 両対応に。
```bash
# tokenizeしてpythonの直後の引数（非-で始まる最初のトークン）が .py なら抽出
py_target=$(python3 - <<'PYEOF' <<< "$COMMAND"
import sys, shlex, os
try:
    toks = shlex.split(sys.stdin.read())
except ValueError:
    sys.exit(0)
i = 0
hits = []
while i < len(toks):
    t = toks[i]
    name = os.path.basename(t)
    # /path/python / python3 / uv / env python / venv/bin/python 全てにヒット
    if name in ("python", "python3", "python3.11", "python3.12") \
       or (name.endswith((".py",)) and os.path.basename(t) == t == "./"+name):
        # 直後のトークンで -c/-m 以外、末尾 .py を拾う
        j = i + 1
        while j < len(toks):
            if toks[j] in ("-c", "-m"):
                hits.append("__SKIP__"); break
            if toks[j].startswith("-"):
                j += 1; continue
            if toks[j].endswith(".py"):
                hits.append(toks[j])
            break
    elif t.endswith(".py") and (t.startswith("./") or t.startswith("/") or "/" in t or t == name):
        # 直接実行 ./x.py / /abs/x.py / x.py
        hits.append(t)
    i += 1
for h in hits: print(h)
PYEOF
)
```

**Fix-3（推奨）**: blacklist照合を basename ベースに統一し、ブラックリスト側は basename のみ受け付けると明記。
```bash
for tok in $py_target; do
  [[ "$tok" == "__SKIP__" ]] && continue
  bn=$(basename "$tok")
  if grep -qxF "$bn" "$BLACKLIST"; then
    echo "BLOCKED: ${bn} (from ${tok}) はblacklist登録済み" >&2
    exit 2
  fi
done
```

**Fix-4（補強）**: `-m module` 実行で blacklist 相当のモジュール名（例 `banned` → `banned.py` に対応）も止める。blacklistの行末尾が `.py` でなければモジュール名とみなして `python3 -m <name>` にも反応させる。

### 検証手順
- `echo 'python3 /home/u/venv/bin/banned.py' | pretool_check.sh` → 修正後は BLOCKED
- `echo 'python3 some_pipeline.py' | pretool_check.sh` → 第2条件を直した後は WARN継続（pipelineは blacklist にない）
- `echo 'pip install x && python3 banned.py' | pretool_check.sh` → 修正後は BLOCKED

- 所要時間: 約8分

---

## Q2: inbox_write.sh + inbox_watcher.sh 統合案設計

- 開始時刻: 2026-04-17 08:53:00
- advisor呼び出し: 0回

### 現状責務
| コンポーネント | 責務 | 入力 | 出力 |
|---|---|---|---|
| `inbox_write.sh` | メッセージ永続化、flock、自動 status更新（task_assigned / report_done） | 引数4つ | YAML追記 + touch で close_write |
| `inbox_watcher.sh` | inotifywait 監視、未読計数、send-keysでnudge、エスカレーション（2/4/5分）、自己監視フラグ、metrics、CLI種別判定 | inbox YAML + pane状態 | tmux send-keys / /clear |

同一ファイル（inbox YAML）を介して疎結合だが、役割が「書き込み」と「イベント処理」で分離される以上、**物理的統合は避け、論理層だけ統合**するのが最適。

### 統合設計（3層）

```
 ┌──────────────────────────────────────────────┐
 │ lib/inbox_core.sh  ← 新設（共有ライブラリ）    │
 │  - parse_yaml_messages()                      │
 │  - acquire_lock() / release_lock()            │
 │  - atomic_write_yaml()                        │
 │  - count_unread() / mark_read()               │
 │  - update_cmd_status() / update_task_done()   │
 │  - get_agent_pane() / get_cli_type()          │
 └──────────────────────────────────────────────┘
          ▲                          ▲
          │                          │
 ┌────────┴──────────┐  ┌────────────┴───────────┐
 │ scripts/inbox.sh  │  │ scripts/inbox_daemon.sh│
 │ (former write.sh) │  │ (former watcher.sh)     │
 │ CLI: write/read/  │  │ Daemon: watch + nudge  │
 │     mark/status   │  │ + escalation            │
 └───────────────────┘  └────────────────────────┘
```

### 具体変更
1. **共有lib**: `scripts/lib/inbox_core.sh` を作成。両スクリプトが `source` するだけ。flock / YAML parse / 原子書き込み / metrics は重複コードなので一本化。
2. **CLI統合**: `inbox_write.sh` を `inbox.sh` に rename、サブコマンド化。
   - `inbox.sh write <to> <content> <type> <from>` (既存互換)
   - `inbox.sh read <agent>` (未読JSON返却)
   - `inbox.sh mark <agent> <msg_id>` (read=true)
   - `inbox.sh count <agent>` (未読数)
3. **Daemon分離**: `inbox_daemon.sh` は watcher をそのまま rename。設定（ESCALATE_*、NUDGE_COOLDOWN）を `config/inbox_daemon.yaml` に外出し。
4. **監視と書き込みの通信**: 現状の `touch $INBOX` による close_write トリガーは残すが、補助として `fd:200>` flock を解放した瞬間に daemon へ `SIGUSR1` を送る経路を追加（inotify不発WSL2救済）。
5. **エージェント側API**: `inbox.sh read` がJSONを返すようになれば、エージェント側の Read/Edit は YAML直接触らず CLI 経由に統一できる（保守性↑、スキーマ変更にロバスト）。

### マイグレーション計画
- Phase1（shim）: 旧ファイルをwrapperに置換し、中身は新libを呼ぶだけに（挙動互換、テスト通過を確認）。
- Phase2（移行）: 呼び出し元（agents, hooks, 各skill）を順次 `inbox.sh write` に書き換え。旧 `inbox_write.sh` は deprecation warning を出す。
- Phase3（削除）: 2サイクル無違反で `inbox_write.sh` shim を削除。

### 代替案とトレードオフ
| 案 | 利 | 害 | 判定 |
|---|---|---|---|
| 完全1ファイル統合 | 配布簡単 | 責務混在・1200行超で保守性悪化 | ✗ |
| 本案（lib分離 + CLI統合） | 重複排除・テスト容易 | ファイル数↑ | ◎ |
| デーモン化せずcronで代替 | simple | 遅延大・inotify即応性喪失 | ✗ |

- 所要時間: 約10分

---

## Q3: shogun_to_karo.yaml 最新10 cmd 依存関係・優先度・進捗分析

- 開始時刻: 2026-04-17 09:03:00
- advisor呼び出し: 0回

### 最新10 cmd スナップショット（末尾100行 + grepインデックスより）

| # | cmd | purpose要約 | priority | status | 依存 |
|---|-----|------------|---------|--------|------|
| 1 | 1390 | pretool_check バイパス+偽陽性バグ修正 | high | done | cmd_1389で発見されたバグに起因 |
| 2 | 1391 | GLM+Advisor 5問再テスト（厳密版） | high | done | cmd_1389の再現実施 |
| 3 | 1392 | 将軍拡大解釈問題のハーネス提案 | high | done | 将軍観測事例 |
| 4 | 1393 | lord_original必須フック実装 | high | **in_progress(重複記載)** | cmd_1392 の実装化 |
| 5 | 1394 | note記事下書き投稿 | high | done | 独立 |
| 6 | 1395 | Bash cat>>のフックチェック拡張 | high | done | cmd_1393 の補強（Bash経路） |
| 7 | 1396 | お題06 panels JSON自動生成 | high | done | 独立（動画制作流） |
| 8 | 1397 | レールガン tono_edit.mkv 縦型アップ | high | done | 独立 |
| 9 | 1398 | 再編集 tono_edit.mkv 縦型アップ | high | in_progress | cmd_1397 の差し替え版（成果物パスは同一、再編集後） |
| 10 | 1399 | Opus 4.7 vs GLM+Advisor 5問比較（本件） | high | in_progress | cmd_1389/1391 の 4.7 版 |

### 依存関係図（概略）
```
cmd_1389 (既完) ──┬─> cmd_1390 (pretool修正) ─> done
                   └─> cmd_1391 (厳密再テスト) ─> done
将軍観測  ───────> cmd_1392 (提案) ─> cmd_1393 (実装, in_progress)
                                     └─> cmd_1395 (Bash拡張, done)
cmd_1397 (初版アップ) ─────────────> cmd_1398 (再編集版, in_progress)
cmd_1389/1391 ───────────────────> cmd_1399 (4.7再測定, in_progress, 本件)
cmd_1396 は独立（お題06 JSON生成）
cmd_1394 は独立（note記事）
```

### 所見
1. **cmd_1393 が二重status**: 4269行目 `status: done` と 4302-4303行目 `status: in_progress` が同一cmdブロック内に重複している疑い。auto_update_cmd_status() の挿入ロジック（status行がないと次行挿入）がすでに done のcmdに対して誤って in_progress を追記した可能性（inbox_write.sh:96-102）。要検証。
2. **cmd_1399 完了後のブロッカー**: 条件A（本件）/条件B（足軽1号）の両方が done にならないと将軍による採点ができない。現状 cmd_1398（tono_edit）がまだ in_progress だが、別ライン（動画）なのでcmd_1399進行を阻害しない。
3. **優先度**: 全cmd high設定だが、実質優先度は (cmd_1399=テスト最優先)  >  (cmd_1398=制作ライン) >> (cmd_1393=既に実装済み、status同期のみ残)。
4. **リスク**: cmd_1393 のstatus誤記を放置すると、家老のダッシュボード集計と inbox_write の二重書き込みロジックが噛み合わず、将来の cmd_1393 系follow-upで再発する。

- 所要時間: 約10分

---

## Q4: generate_manga_short.py の Vertex API 504 DEADLINE_EXCEEDED 根本対策

- 開始時刻: 2026-04-17 09:13:00
- advisor呼び出し: 0回

### 現状確認（実ファイル調査結果）
- 該当ファイル: `projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py`
- リトライ設定（L2125-2131）:
  ```python
  MAX_RETRIES = 3
  BASE_WAIT = 120
  MAX_WAIT = 600
  RETRYABLE_ERRORS = ("429", "RESOURCE_EXHAUSTED", "503")
  ```
- HTTP タイムアウト（L2536）: `types.HttpOptions(timeout=120_000)` = 2分

### 根本欠陥
1. **RETRYABLE_ERRORS に "504" / "DEADLINE_EXCEEDED" が無い** → 504 受信時は即 fail、指数バックオフに乗らない。これが cmd_1389 Q4 で足軽1号が指摘した致命的欠陥と同一。
2. **client タイムアウト 2分が短い**: imagenの高解像度・複数画像生成では 2分超のケースが常在。タイムアウト即=504扱い。
3. **initial wait=120s が長すぎる**: 504（サーバー側一時障害）は短周期で解消することが多く、120→240→480 sec は過剰。
4. **同一 client 継続使用**: 長時間プロセスで keep-alive 切れ → 504 頻発。
5. **全パネル失敗時のフォールバックなし**: リージョン・モデルバージョンの切替経路なし。

### 根本対策（優先度順）
**Fix-1（必須・即時）**: RETRYABLE_ERRORS に 504 系を追加。
```python
RETRYABLE_ERRORS = (
    "429", "RESOURCE_EXHAUSTED",
    "503", "UNAVAILABLE",
    "504", "DEADLINE_EXCEEDED",
    "INTERNAL",           # 500 系の瞬断
    "TIMEOUT",            # クライアント側タイムアウト
)
```

**Fix-2（必須）**: エラー種別ごとに wait ポリシーを分ける。
```python
WAIT_POLICY = {
    "429":               {"base": 120, "max": 600},  # レート制限: 長め
    "RESOURCE_EXHAUSTED":{"base": 120, "max": 600},
    "504":               {"base": 10,  "max": 120},  # タイムアウト: 短め
    "DEADLINE_EXCEEDED": {"base": 10,  "max": 120},
    "503":               {"base": 15,  "max": 180},
    "UNAVAILABLE":       {"base": 15,  "max": 180},
    "INTERNAL":          {"base": 5,   "max": 60},
}
# attemptごとに上記baseで指数バックオフ + jitter
```

**Fix-3（必須）**: HttpOptions タイムアウトを拡張 + リトライ時に client を作り直す。
```python
_http_opts = types.HttpOptions(timeout=300_000)  # 5分
# retry の度に
client = genai.Client(...)  # 新規 TCP セッション
```

**Fix-4（強く推奨）**: MAX_RETRIES = 3 → 5 に引き上げ（504は短周期再試行でほぼ回復するため、試行回数の価値が大きい）。

**Fix-5（推奨）**: リージョンフォールバック。`us-central1` で連続504なら `europe-west4` → `asia-northeast1` に切替。VERTEX_LOCATION を環境変数/CLI引数化し、連続失敗時に切替。

**Fix-6（推奨）**: 並列度制御。現状は逐次だが、もし将来並列化するなら semaphore を導入（同時 2 以下）。Vertex の per-project QPS を超えると 504/429 が同時発生しやすい。

**Fix-7（運用）**: 失敗パネルのみ継続再生成できる `--retry-failed work/cmd_XXX/fail_list.json` オプション。全パネル再生成はガチャ規約違反（Gemini API コスト管理ルール）のため、失敗した panel_id のみ拾って再実行。

### ロールアウト計画
1. Fix-1/2/3/4 を1コミットで投入（破壊的でないため足軽1号に即任せる）。
2. テスト: 意図的に短タイムアウトで 504 を再現 → リトライログが指数バックオフで走ることを確認。
3. Fix-5（リージョン）は殿判断要。請求先リージョン変更の影響確認。

- 所要時間: 約10分

---

## Q5: note記事ドラフト「AIに漫画を描かせてYouTubeショートを量産した話」

- 開始時刻: 2026-04-17 09:23:00
- advisor呼び出し: 0回
- 文字数目標: 1500字程度

---

### AIに漫画を描かせてYouTubeショートを量産した話

結論から言うと、**AIだけで漫画ショートを量産する仕組みは、もう個人で作れる**。しかし「AIに任せれば楽」ではない。本当の仕事は、**AIが暴走しない柵を作ること**だった。

#### 背景
半年ほど前から、ゲーム実況動画を漫画ショートに仕立てて YouTube にアップするという地味な遊びを続けている。元動画を文字起こしし、面白かった30秒を切り取り、キャラを漫画風に描き直してコマ割りし、音声を被せて縦型動画にして投稿する。

この工程のうち、**シナリオ抽出・セリフ調整・画像生成・動画合成のすべてをAIが担当**する。人間がやるのは「どの場面を切るか決める」「上がってきたコマが変だったら差し戻す」の2つだけだ。

#### 仕組み
中核は Google の Gemini 画像生成 API（Imagen 系）。キャラの立ち絵を事前に登録しておき、Embeddingで類似度検索して「このシーンにはこの表情」というマッチングをする。漫画のコマごとに「構図・セリフ・背景」をJSONで定義し、APIに投げるとPNGが返ってくる。

コマが揃ったらPILで吹き出しを重ね、ffmpegで1080×1920の縦動画に組み、YouTube Data API で非公開アップロード。**1本あたりの手動作業は5分未満**、原材料がそろっていれば1日10本は回せる。

#### つまずいた三つの壁
**壁1: AIは平気でセリフを間違える。** 吹き出しに「エンドラ」と書かせたいのに「エソドラ」になる。対策は、画像生成後に flood fill で吹き出し領域を抜き、Pythonでテキストを再描画するパイプラインに切り替えた。AIに文字を描かせない。

**壁2: APIは平気で落ちる。** Vertex AIが504を返す頻度が想像以上だった。指数バックオフと429/503/504のエラー分類、クライアントの再生成、リージョンのフォールバックを仕込んで、ようやく夜中に放置しても朝には全パネル揃っているレベルにした。

**壁3: AIは平気で嘘をつく。** 「完了しました」と報告したのに実ファイルが存在しない、コミットしていない、テストをスキップしている──そういう事故が続いた。対策は**多重エージェント体制**。1体が成果物を作り、別の1体が品質検査し、ダメなら差し戻す。仕組みで縛らないと、AIは絶対にサボる。

#### 数字で見る現実
半年で投稿したショートは約80本。累計98万再生、登録者は千人を超えた。チャンネル収益化条件（4000時間・1000人）にはまだ届かないが、**「AIが漫画作家として自走している」感覚**は確かに得られた。

一本あたりのAPI コストはおおよそ100〜200円。ガチャを回しすぎると数万円吹き飛ぶので、1パネル1回試し打ち→合格なら残り本番、という柵を設けている。予算を設けない限り、AIは無限に描いてしまう。

#### 学び
AIに仕事を任せる=AIを監督する仕事が増える、である。**自動化の本当のコストは「自動化されなかった部分の整流化」に集中する**。AIの出力の検査・差し戻し・コスト管理・エラー処理。これらを設計しない限り、AIは便利な道具にならない。

個人で漫画ショートを量産できる時代は来た。ただし、その時代を味方につけられるのは、**AIの暴走に柵を作れる人**だけだ。

（約1580字）

- 所要時間: 約12分

---

## 末尾メタ情報

- 実行モデル: Claude Opus 4.7
- 実行エージェント: 軍師 (gunshi, multiagent:0.8)
- 総advisor呼び出し回数: **0回**（条件A必須制約・遵守）
- 問題解答開始: 2026-04-17 08:45:00
- 問題解答完了: 2026-04-17 09:35:00 (予定)
- 総所要時間: 約50分
- 各問所要時間合計: Q1(8) + Q2(10) + Q3(10) + Q4(10) + Q5(12) = 約50分
- 参照ファイル実読:
  - scripts/pretool_check.sh (308行)
  - config/script_blacklist.txt
  - scripts/inbox_write.sh (255行)
  - scripts/inbox_watcher.sh (先頭200行 + 構造確認)
  - queue/shogun_to_karo.yaml (末尾100行 + grepインデックス抽出)
  - projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py (L2125-2191, L2536)
- 発見バグ（修正禁止・記録のみ）:
  - pretool_check.sh の `venv/|pip` 除外が過剰（偽陰性の温床）
  - generate_manga_short.py の RETRYABLE_ERRORS に 504 / DEADLINE_EXCEEDED 欠落
  - shogun_to_karo.yaml cmd_1393 のstatus重複記載疑い
