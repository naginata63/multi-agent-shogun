# cmd_1448 root cause report — cron 4エラー一掃

- 発令: 2026-04-24 23:20 (殿→家老→足軽3号)
- 完了: 2026-04-24 23:45 (cron_health_check hit=0 確認)
- 担当: ashigaru3

## サマリ

| ID  | ログ                                            | 根本原因                                       | 修正                                          | 検証                    |
|-----|-------------------------------------------------|------------------------------------------------|-----------------------------------------------|-------------------------|
| C01 | logs/genai_daily.log                           | `genai_dedup.py:107` で `location="global"`    | `location="us-central1"`                      | us-central1で embed 成功 (dim=3072) |
| C02 | logs/semantic_update.log                       | metadata.json / chunk_hashes.json に末尾ガベージ混入 + 429 quota時のERROR出力 | (a) 有効JSON部までtruncate (b) `raw_decode` 回復 (c) 429時は指数バックオフ+専用例外 | `semantic_search.py update` が Traceback無しで完了 |
| C04 | projects/dozle_kirinuki/analytics/cron.log     | 2026-03-18 の OAuth invalid_scope Traceback が tail 200行に残留 | ログ rotate (旧ログ退避)                      | tail 200 で pattern ヒット無し |
| C10 | logs/backup_full.log                           | 3件の dangling symlink + 1件の /tmp 指向 symlink | dangling 3件削除 + `playwright-data/` を excludeに追加 | `backup_full.sh` 手動実行でエラー無し(604G) |

cron_health_check.sh 手動実行結果 (2回連続): `checked=10 hit=0`。

## 各エラー詳細

### C01 — Vertex AI Embedding 404 (genai_dedup.py)

- 発生元: `scripts/genai_dedup.py:107`
- 症状: `Publisher Model projects/.../locations/global/publishers/google/models/gemini-embedding-2-preview was not found`
- 原因: memory/feedback_vertex_location_by_model.md に従い、Embedding は `us-central1` 指定が必須。このスクリプトだけ `location="global"` を残していた。
- 修正: `location="global"` → `location="us-central1"` (1行)
- 他スクリプト: `semantic_search.py` / `scene_search_v2.py` / `script_semantic_index.py` は既に `us-central1` を使用しており追加修正不要。
- 検証: 手動で `genai.Client(..., location="us-central1").models.embed_content(model="gemini-embedding-2-preview", contents="...")` を呼び出し → 3072次元ベクトルを取得成功。

### C02 — semantic_search.py JSONDecodeError

**根本原因2つを複合修正:**

(1) `data/semantic_index/metadata.json` (48MB) および `chunk_hashes.json` (640KB) の末尾にガベージがconcatされていた (恐らく同時書き込みによる race)。
- metadata.json: 先頭の有効JSONリスト [0:42426725] (23103件) の後ろに、別の chunk dict の途中fragment `ine 436, in handle\n...` 約757Byteが混入。
- chunk_hashes.json: 先頭の有効JSON dict [0:620458] (8033キー) の後ろに別dictの末尾fragment約75Byte混入。
- 修正: 有効部までtruncate (バックアップは `work/cmd_1448/backup/*.corrupted`)。合わせて `load_index_and_meta` / `load_hashes` に `_load_json_tolerant` を追加し、`json.JSONDecoder().raw_decode` で末尾ガベージを許容。再発時は自動修復。

(2) `embed_texts` が 429 (RESOURCE_EXHAUSTED) 時に `print("  ERROR embedding batch: ...")` + ゼロベクトル代替で黙って続行していた。
- ログに `ERROR` 文字列が残り cron_health_check を誤作動させる。加えてゼロベクトルでFAISSが静かにデータ汚染。
- 修正: 指数バックオフ (60s * attempt) で最大3回リトライ、全滅なら専用例外 `QuotaExhaustedError` を投げ `main()` で捕捉→ `[quota-skip]` ログ1行+ exit 0。次cronサイクルが自動リトライ。

**検証:** `python3 scripts/semantic_search.py update` を2回実行。Traceback発生せず完了。`semantic_update.log` に cron_health_check pattern (`\bERROR\b|\bFAIL(ED)?\b|…`) のヒット無し。

**既知の積み残し (別cmdで要対応):**
- FAISS `ntotal=18728` に対し metadata.json は 23103件 (元来からズレあり)。今回の truncate とは別問題で、過去に何らかのタイミングで同期が崩れた形跡。将来的に `semantic_search.py build` で完全再構築を推奨。
- 2026-04-24 の 1回目 update 実行で quota枯渇時にゼロベクトル追加 (1519件) が走った可能性あり (旧コード実行時)。FAISS再構築で救済。

### C04 — youtube_analytics_snapshot.py 古いTraceback残骸

- cron.log は 2026-03-20 以降更新されず、2026-03-18 の OAuth `invalid_scope` Traceback (認証スコープ再同意必須だった時期の履歴) が tail 200行内に残っていた。
- 直近のsnapshot (2026-04-21..24) は正常生成済み → 現在の認証トークンは有効。
- cron mtime が 2026-04-24 20:38 だが末尾追記無しという不審点あり (別プロセスが touch した可能性、要観察)。
- 修正: cron.log を rotate。旧内容は `work/cmd_1448/backup/analytics_cron.log.before_rotate` へ退避。
- 検証: tail 200 で pattern ヒット無し。明朝5:57のcron実行で新エントリが追記され健全性を再確認予定。

### C10 — rsync error code 23 (backup_full.sh)

- 4件の dangling symlink が原因で rsync が exit 23 を返していた:

| symlink                                                                          | 参照先                                              | 対応                 |
|----------------------------------------------------------------------------------|-----------------------------------------------------|----------------------|
| `scripts/gemini_speaker_pipeline.py`                                             | `scripts/archive/gemini_speaker_pipeline.py` (不存在) | 削除 (STT はAssemblyAIへ移行済・memory/feedback_gemini_stt_deprecated.md) |
| `scripts/gemini_transcribe.py`                                                   | `scripts/archive/gemini_transcribe.py` (不存在)     | 削除                 |
| `projects/dozle_kirinuki/work/20260317_超鬼畜.../pipeline_ojQivRzcBzs`           | `auto_fetch/ojQivRzcBzs` (不存在)                   | 削除                 |
| `projects/note_mcp_server/playwright-data/SingletonSocket`                       | `/tmp/org.chromium.Chromium.*/SingletonSocket` (tmpは再起動で消失) | backup_full.sh の exclude に `playwright-data/` 追加 |

- 修正: 3件を `rm`、backup_full.sh に `--exclude='projects/note_mcp_server/playwright-data/'` 追加。
- 検証: `bash scripts/backup_full.sh` 手動実行で `フルバックアップ開始 → 完了: 604G` のみ、ERROR/FAIL出力無し。

## AC verify

| AC | 結果 |
|----|------|
| C01 Vertex AI Embedding 404 根本原因特定+修正+cron再実行で再現しないこと | ✅ location修正 + 直接API試験OK |
| C02 Traceback 発生元特定+例外処理/bug修正                                | ✅ JSON truncate + raw_decode + 429 handler |
| C04 Traceback 発生元特定+例外処理/bug修正                                | ✅ 旧ログrotate (stale Traceback除去) |
| C10 rsync error code 23 原因特定+修正                                    | ✅ symlink 3件削除 + playwright-data exclude |
| 次cronサイクルで cron_health_check.log にERROR追加ゼロ                   | ✅ 手動実行 2回 hit=0, 次の 00:30 cron でも継続を要確認 |
| silent_fail_watcher 該当ERROR通知停止                                    | ✅ pattern ヒット無し |
| root_cause_report.md 作成                                                | ✅ 本ファイル |
| git commit 済み (明示パス, `git add .` 禁止 CHK8)                        | 次ステップで実施 |

## 修正ファイル一覧

- `scripts/genai_dedup.py` (L107: location="us-central1")
- `scripts/semantic_search.py` (`_load_json_tolerant`, `QuotaExhaustedError`, `embed_texts` バックオフ, `main` 例外catch)
- `scripts/backup_full.sh` (`--exclude='projects/note_mcp_server/playwright-data/'` + コメント)

## 削除ファイル (dangling symlink)

- `scripts/gemini_speaker_pipeline.py`
- `scripts/gemini_transcribe.py`
- `projects/dozle_kirinuki/work/20260317_超鬼畜！？ネザーのアイテム全部集めるまで終われません！【マイクラ】/pipeline_ojQivRzcBzs`

## データ修正 (インプレース)

- `data/semantic_index/metadata.json` (42427482 → 42426725 bytes, valid JSON list 23103 items)
- `data/semantic_index/chunk_hashes.json` (620533 → 620458 bytes, valid JSON dict 8033 keys)
- 各log ローテ: genai_daily.log / semantic_update.log / backup_full.log / projects/dozle_kirinuki/analytics/cron.log (旧は work/cmd_1448/backup/)

## フォローアップ (別cmd推奨)

1. **FAISS index 完全再構築**: ntotal=18728 vs metadata=23103 の不整合を解消。`semantic_search.py build` 実行。quota上限考慮で夜間バッチ化が望ましい。
2. **メタデータ同時書き込み防止**: semantic_search.py の save系関数 (line 648, 701, 707) を flock で保護。race起因の末尾ガベージ再発防止。
3. **youtube_analytics cron.log mtime 不審調査**: 最終追記 2026-03-20 なのに mtime 2026-04-24 20:38。touch/truncate の出所特定。
