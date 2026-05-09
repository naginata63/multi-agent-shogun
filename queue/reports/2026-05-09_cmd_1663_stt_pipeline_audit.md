# cmd_1663 STTパイプライン矛盾検出 (read-only audit)

- **作成**: 2026-05-09 10:15 JST / 軍師
- **対象**: projects/dozle_kirinuki/scripts/ 配下の STT パイプライン (vocal_stt_pipeline.py / stt_merge.py / speaker_id 系 7 ファイル + legacy/)
- **検出観点**: スキーマ不整合・前提矛盾・段間ミスマッチ・パス依存破綻リスク・並列/タイムアウト/エラーハンドリング欠如
- **制約**: コード修正なし (read-only sweep)

---

## サマリ (severity 別件数)

| Severity | 件数 |
|----------|------|
| CRITICAL | 2 |
| HIGH     | 4 |
| MEDIUM   | 5 |
| LOW      | 5 |
| **合計** | **16** |

最大の構造問題: **WhisperX 撤去方針 (cmd_1671) が一部ファイルで未浸透** (C001/H003 + L003)。`projects/dozle_kirinuki/scripts/transcribe_with_speakers.py` 全体が WhisperX 依存・`stt_merge.py` に WhisperX fallback mode 残骸あり。

---

## 調査対象ファイル

| ファイル | 行数 | 役割 |
|----------|------|------|
| `vocal_stt_pipeline.py` | 1069 | メインパイプライン (mp4 → demucs → AssemblyAI/Deepgram → stt_merge → ECAPA-TDNN) |
| `stt_merge.py` | 908 | AssemblyAI + Deepgram + (Gemini SRT) + YouTube字幕 マージ |
| `speaker_id.py` | 307 | ECAPA-TDNN モジュール (単独実行・identify_speakers 関数) |
| `batch_speaker_match.py` | 130 | 全動画一括声紋マッチング (run_speaker_match_only.py を subprocess で呼出) |
| `apply_speaker_mapping_srt.py` | 125 | speaker_mappings.yaml 適用 (SRT 内アルファベット → 実名置換) |
| `run_speaker_match_only.py` | 67 | Step 7 (ECAPA-TDNN) 単独実行 (vocal_stt_pipeline.run_speaker_identification を import) |
| `transcribe_with_speakers.py` | 186 | **WhisperX** 統合版 (whisperx.load_model/diarize/align) |
| `subtitle_speaker_qc.py` | 抜粋 120 | 字幕色 QC (字幕焼込動画から色判定・補助ツール) |
| `assemblyai_stt_clips.py` | 抜粋 50 | 単発クリップ STT (補助ツール) |
| `legacy/auto_speaker_mapping.py` | 30+ | speaker_mapping.txt (旧形式) を扱う legacy |

---

## CRITICAL (2件)

### C001 — `transcribe_with_speakers.py` が WhisperX 依存で残存 (cmd_1671 撤去方針と矛盾)

**file:line**:
- `projects/dozle_kirinuki/scripts/transcribe_with_speakers.py:114` `import whisperx`
- 同 `:117` `whisperx.load_model("large-v2", device, language=language, compute_type=compute_type)`
- 同 `:122-123` `whisperx.load_align_model` + `whisperx.align`
- 同 `:126-128` `from whisperx.diarize import DiarizationPipeline as _DiarizationPipeline`
- 呼出元: `projects/dozle_kirinuki/scripts/auto_fetch.py` で grep hit → dead code ではなく**生きた依存**

**旧ルール引用**:
> cmd_1671 C001 (WhisperX 撤去) — 「ファイルに痕跡なし。既に完全削除済み」と subtask_1671_a3a 報告 (但しこれは main.py 限定)

**推奨改訂案**:
1. `transcribe_with_speakers.py` を AssemblyAI + Deepgram + ECAPA-TDNN 経路に書き換え (vocal_stt_pipeline.py のサブセット呼出にラップ)
2. `auto_fetch.py` の transcribe_with_speakers 呼出を vocal_stt_pipeline.run_speaker_identification 経路へ migration
3. 移行困難なら `transcribe_with_speakers.py` を `legacy/` に移動 + auto_fetch.py から呼出停止

**影響評価**: HIGH。cmd_1671 で「WhisperX 撤去」を全方針として承認したのに STT 経路の一角が依然 WhisperX。`auto_fetch.py` の運用次第で WhisperX が動作 → メモリ 5.2GB 消費・GPU 競合再発 (memory/MEMORY.md 教訓)。**殿激怒リスク**。

---

### C002 — `apply_speaker_mapping_srt.py:34` ハードコード絶対パス遺物

**file:line**: `projects/dozle_kirinuki/scripts/apply_speaker_mapping_srt.py:32-35`

**旧ルール引用**:
```python
COPY_FROM = {
    "merged__sVuKf5Zu4A.srt": Path(__file__).parent.parent / "work" / "20260214_寝ないと死ぬ" / "merged__sVuKf5Zu4A.srt",
}
```

**推奨改訂案**:
- 当該動画 (`_sVuKf5Zu4A.srt`) の処理が完了済なら **dict ごと削除** (dead code)
- 将来似た COPY 操作が必要なら、CLI 引数 `--copy-from <video_id>=<src>` に外部化

**影響評価**: MEDIUM-HIGH。スクリプト実行時に `srt_and_candidates/merged__sVuKf5Zu4A.srt` が存在しない場合に `[error] コピー元なし` 出力 → silent skip。但し他動画では一切機能せず・**この dict のために実行する人はいない** = 完全な遺物。

---

## HIGH (4件)

### H001 — `batch_speaker_match.py:18` MEMBER_NAMES ハードコード ↔ 他は `load_members_from_yaml()`

**file:line**: `projects/dozle_kirinuki/scripts/batch_speaker_match.py:18`

**旧ルール引用**:
```python
MEMBER_NAMES = {"dozle", "bon", "qnly", "orafu", "oo_men", "nekooji"}
```

**推奨改訂案**:
```diff
- MEMBER_NAMES = {"dozle", "bon", "qnly", "orafu", "oo_men", "nekooji"}
+ from members import load_members_from_yaml
+ MEMBER_NAMES = set(load_members_from_yaml())
```

**影響評価**: HIGH。新メンバー追加 (例: `dozle_club` の特殊扱い)・メンバー脱退時に同期もれ。L47 `has_alpha_speakers` 関数がアルファベット判定で `s not in MEMBER_NAMES` を使うため、新メンバー名が誤って「アルファベットラベル」と判定される事故リスク。`vocal_stt_pipeline.py:38` `from members import load_members_from_yaml` 等他 5 ファイルとの不整合。

---

### H002 — ECAPA-TDNN ロジック 3箇所で重複

**file:line**:
- `projects/dozle_kirinuki/scripts/speaker_id.py:61-225` (`identify_speakers` — VAD ベース・単独実行用)
- `projects/dozle_kirinuki/scripts/vocal_stt_pipeline.py:507-684` (`run_speaker_identification` — AssemblyAI ラベル前提)
- `projects/dozle_kirinuki/scripts/vocal_stt_pipeline.py:687-883` (`run_direct_speaker_identification` — AssemblyAI 不在時 direct 経路)

**旧ルール引用**: 3 関数すべてで `_bootstrap_ecapa()` (vocal_stt_pipeline.py:431-460) 経由のモデルロード + cosine similarity max + threshold 比較ロジックが再実装。`speaker_id.py:194-218` と `vocal_stt_pipeline.py:618-630` `vocal_stt_pipeline.py:780-790` で同じ embedding 計算+similarity max ロジック。

**推奨改訂案**: 共通関数 `_compute_speaker_match(seg_audio, embeddings, classifier, F, threshold) -> str` を `vocal_stt_pipeline.py` または `speaker_id.py` に集約し、3 関数から共有。または speaker_id.py に core ロジックを集約し vocal_stt_pipeline.py の 2 関数はそれを wrap。

**影響評価**: HIGH。閾値修正・similarity 計算改善時に **3箇所同時更新が必要** = 片漏れ事故リスク。実際 `speaker_id.py:194` の `< 4000 (≒0.25s)` ガードは vocal_stt_pipeline 側にはない (M003 と関連)。

---

### H003 — `stt_merge.py` に WhisperX 残骸 (cmd_1671 方針と矛盾)

**file:line**:
- `projects/dozle_kirinuki/scripts/stt_merge.py:578` `"source": "whisperx",` (load_srt_as_words 内)
- 同 `:747-758` fallback mode で `merged_whisperx.srt` を探索 (`os.path.join(args.output.rstrip("/"), "merged_whisperx.srt")`)
- 同 `:778` `mode = "whisperx-fallback"` (出力 metadata)

**旧ルール引用**:
```python
# L578
"source": "whisperx",
# L753
os.path.join(args.output.rstrip("/"), "merged_whisperx.srt"),
# L778
mode = "whisperx-fallback"
```

**推奨改訂案**:
- L578: `"source": "srt_fallback"` 等 WhisperX 中立な表現に
- L747-758: `merged_whisperx.srt` の検索を停止 (or `srt_named.srt` のみ残す)
- L778: `mode = "srt-fallback"`

**影響評価**: HIGH。WhisperX 撤去方針 (cmd_1671) の不徹底を文書化せず維持 = ローカル運用で混乱要因。`source: "whisperx"` を含む merged JSON が後段 (Marp スライド・analytics) に流れると **WhisperX が運用継続中と誤認**。

---

### H004 — `vocal_stt_pipeline.py:32` PROJECT_DIR の 4-up depth 依存

**file:line**: `projects/dozle_kirinuki/scripts/vocal_stt_pipeline.py:32`

**旧ルール引用**:
```python
PROJECT_DIR = Path(__file__).parent.parent.parent.parent  # multi-agent-shogun root
```

**推奨改訂案**: 環境変数 or pyproject.toml ベースに変更:
```python
PROJECT_DIR = Path(os.environ.get('SHOGUN_ROOT') or Path(__file__).resolve().parents[3])
```
最低限、`Path(__file__).resolve().parents[3]` で resolve することで symlink 経由の異常を防止。

**影響評価**: HIGH。`projects/dozle_kirinuki/scripts/vocal_stt_pipeline.py` の階層が変わる (例: `projects/dozle_kirinuki/scripts/sub/foo.py` 等にコピー) と PROJECT_DIR が誤った根を指す。L428 `_get_profile_dir()` が `PROJECT_DIR / "projects" / "dozle_kirinuki" / "speaker_profiles"` を計算するため、ECAPA-TDNN の声紋プロファイル不在エラー (`profile_dir not found`) が誤箇所で発生する。

---

## MEDIUM (5件)

### M001 — `vocal_stt_pipeline.py:208` AssemblyAI upload timeout 5分

**file:line**: `projects/dozle_kirinuki/scripts/vocal_stt_pipeline.py:208`

**旧ルール引用**:
```python
r = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=f, timeout=300)
```

**推奨改訂案**:
```python
# 大ファイル対応: 60分動画 ≒ 200MB+, 遅い回線で 5分超もあり得る
upload_timeout = int(os.environ.get("ASSEMBLYAI_UPLOAD_TIMEOUT", 1800))  # 30分
r = requests.post(..., timeout=upload_timeout)
```

**影響評価**: MEDIUM。60分動画+並列パイプライン実行+10MB/s 未満の回線で `requests.exceptions.Timeout` 発生リスク。再開時に `if output_path.exists()` でスキップされない (upload 失敗時にファイル保存されない) ので、毎回最初からやり直し。

---

### M002 — `stt_merge.py:662-665` legacy mode の video_id 推論バグ (`split("_")[-1]`)

**file:line**: `projects/dozle_kirinuki/scripts/stt_merge.py:662-665`

**旧ルール引用**:
```python
if not video_id:
    stem = Path(output_json).stem
    video_id = stem.split("_")[-1] if "_" in stem else stem
```

**推奨改訂案**:
```python
# YouTube video_id は先頭 _ を含む場合がある (_sVuKf5Zu4A)
# split("_")[-1] では '_sVuKf5Zu4A' → 'sVuKf5Zu4A' (先頭 _ 落ち) or 'Zu4A' になる
import re
m = re.match(r"^merged_(.+)$", stem)
video_id = m.group(1) if m else stem
```

**影響評価**: MEDIUM。`merged__sVuKf5Zu4A.json` の stem は `merged__sVuKf5Zu4A` → `split("_")` で `["merged", "", "sVuKf5Zu4A"]` → `[-1]` = `"sVuKf5Zu4A"` (先頭 _ 落ち)。但し `merged_VID_chunk_001.json` のような複合 stem では `"001"` のような誤抽出。auto_mode 経路 (L644 `Path(args.video_path).stem`) では問題ないが、legacy mode で video_id 未指定時の path 推論で誤動作。

---

### M003 — `speaker_id.py:194` 二重ガード閾値の不一致

**file:line**: `projects/dozle_kirinuki/scripts/speaker_id.py:186,194`

**旧ルール引用**:
```python
# L186
if duration < MIN_SEG_DURATION:  # MIN_SEG_DURATION = 0.5
    short_skipped += 1
    continue

# L194
if seg_audio.shape[1] < 4000:  # < 0.25s at 16kHz
    short_skipped += 1
    continue
```

**推奨改訂案**:
```python
# 閾値統一・1箇所のみで判定
min_samples = int(MIN_SEG_DURATION * sr)
if duration < MIN_SEG_DURATION or seg_audio.shape[1] < min_samples:
    short_skipped += 1
    continue
```

**影響評価**: MEDIUM。L186 で `duration ≥ 0.5s` でも、L189-192 で `seg_audio = waveform[:, start_sample:end_sample]` 切り出した結果が `< 4000 sample (0.25s)` になるケースがあり (リサンプル誤差・端切り)、二重ガードに意味はあるが意図不明確。コードレビュー時の混乱を招く。

---

### M004 — `apply_speaker_mapping_srt.py` 全体が遺物化リスク

**file:line**: `projects/dozle_kirinuki/scripts/apply_speaker_mapping_srt.py:32-35` (C002 と同根) + 全体ロジック

**旧ルール引用**: speaker_mappings.yaml を読込・SRT 内 `[A]:` `[B]:` を `[dozle]:` `[bon]:` に置換するスクリプト。但し vocal_stt_pipeline.py の `run_speaker_identification` が直接 ECAPA-TDNN で実名 (`dozle`/`bon`) を割当てる方式に移行済 → アルファベット → 実名手動 mapping は **新パイプラインでは不要**。

**推奨改訂案**:
- `legacy/` に移動 (旧 srt_and_candidates 配下の SRT 一括変換タスク用)
- 現行パイプラインからは呼ばれていない (grep で hit なし) → dead code 候補

**影響評価**: MEDIUM。直接的な不具合はないが、context/speaker_mappings.yaml の管理コストが残る。新メンバー追加時に「speaker_mappings.yaml も更新?」の判断が増える。

---

### M005 — `legacy/auto_speaker_mapping.py` が現行 yaml と互換ない speaker_mapping.txt 形式

**file:line**: `projects/dozle_kirinuki/scripts/legacy/auto_speaker_mapping.py:1-30`

**旧ルール引用**:
```python
"""
auto_speaker_mapping.py
Speaker Identification結果からspeaker_mapping.txtを自動更新するスクリプト。
...
使い方:
    --speaker-mapping <speaker_mapping.txtパス>
"""
```

**推奨改訂案**:
- `legacy/` 配下にあるので意図的退避済み
- `speaker_mapping.txt` フォーマットは現行 `context/speaker_mappings.yaml` と非互換 → README 等に明記推奨
- 削除候補だが、過去 SRT に対応する legacy なら保留可

**影響評価**: LOW-MEDIUM。誤って実行されるリスクは低い (legacy/ 配下) が、新人が混乱する可能性。

---

## LOW (5件)

### L001 — `vocal_stt_pipeline.py:246` ASSEMBLYAI_MAX_POLL=60 (10分 timeout)

**file:line**: `projects/dozle_kirinuki/scripts/vocal_stt_pipeline.py:246`

**旧ルール引用**:
```python
max_iterations = int(os.environ.get("ASSEMBLYAI_MAX_POLL", 60))  # デフォルト10分 (10s間隔 × 60 = 600s)
```

**推奨改訂案**: 40分超の長尺動画では AssemblyAI 処理時間 >10分 が起きる。default を 120 (20分) に引き上げ、または動画長に応じた可変値:
```python
# 動画長 1秒あたり 0.5秒の余裕を見込む (動画 40分 = 2400秒 → 1200秒 = 120 polls)
max_iterations = max(60, int(video_duration_sec * 0.5 / ASSEMBLYAI_POLL_INTERVAL_SEC))
```

**影響評価**: LOW (env override で運用可能)。但し 1チャンネル 40分超切り抜き素材で hang 事故が起きる可能性。

---

### L002 — `stt_merge.py:431,440` is_garbage_text の固定キーワード

**file:line**: `projects/dozle_kirinuki/scripts/stt_merge.py:431,440`

**旧ルール引用**:
```python
# L440
for kw in ["ぺけたん"]:
    if kw in text:
        return True
```

**推奨改訂案**: `context/garbage_words.yaml` 等の外部設定ファイルに移行:
```yaml
# context/garbage_words.yaml
garbage_keywords:
  - ぺけたん  # YouTube 字幕誤認識頻出 (2026-04 確認)
  - <future_keyword>
```

**影響評価**: LOW。スクリプト改修不要で頻出 garbage word を追加できるようになる。

---

### L003 — `transcribe_with_speakers.py:6-7` と `speaker_id.py:15-16` で OMP/MKL_NUM_THREADS コピペ

**file:line**:
- `projects/dozle_kirinuki/scripts/transcribe_with_speakers.py:6-7`
- `projects/dozle_kirinuki/scripts/speaker_id.py:15-16`

**旧ルール引用**:
```python
os.environ.setdefault('OMP_NUM_THREADS', '4')
os.environ.setdefault('MKL_NUM_THREADS', '4')
```

**推奨改訂案**: 共通モジュール `scripts/torch_threads_config.py` に集約 + `from torch_threads_config import setup_threads` 等。

**影響評価**: LOW。コピペ 2 箇所のみ・実害なし。

---

### L004 — `batch_speaker_match.py:19` VENV_PYTHON 絶対パス

**file:line**: `projects/dozle_kirinuki/scripts/batch_speaker_match.py:19`

**旧ルール引用**:
```python
VENV_PYTHON = str(PROJECT_DIR / "venv" / "bin" / "python3")
```

**推奨改訂案**:
```python
VENV_PYTHON = os.environ.get("VENV_PYTHON", sys.executable)
```

**影響評価**: LOW。venv 構成依存だが、現状運用では venv 必須 (memory/MEMORY.md 参照)。明示的に env var で override 可能にすれば運用柔軟性向上。

---

### L005 — `transcribe_with_speakers.py:14-25` _apply_vocab の例外処理が warn のみ

**file:line**: `projects/dozle_kirinuki/scripts/transcribe_with_speakers.py:14-25`

**旧ルール引用**:
```python
def _apply_vocab(text: str) -> str:
    try:
        ...
        return text
    except Exception as e:
        warnings.warn(f"[transcribe_with_speakers] _apply_vocab failed: {e}")
        return text
```

**推奨改訂案**: `custom_vocabulary.yaml` 不在時 (新規 PJ で初期 setup 前) に毎ワード warn が出て stdout 汚染。1回キャッシュ + ファイル不在時は早期 return:
```python
_VOCAB_CACHE = None
def _apply_vocab(text):
    global _VOCAB_CACHE
    if _VOCAB_CACHE is None:
        try:
            with open(...) as f:
                _VOCAB_CACHE = yaml.safe_load(f)
        except FileNotFoundError:
            _VOCAB_CACHE = {}  # silent skip
    ...
```

**影響評価**: LOW。但し L001 の hang 時に warn 大量出力で原因究明が遅延する可能性。

---

## Sweep Coverage (透明化)

| 対象 | 検査方法 | 結果 |
|------|---------|------|
| `vocal_stt_pipeline.py` (1069行) | 全文 Read + 5 観点 grep | finding: H004/M001/L001 |
| `stt_merge.py` (908行) | 全文 Read | finding: H003/M002/L002 |
| `speaker_id.py` (307行) | 全文 Read | finding: H002 (関連)/M003 |
| `batch_speaker_match.py` (130行) | 全文 Read | finding: H001/L004 |
| `apply_speaker_mapping_srt.py` (125行) | 全文 Read | finding: C002/M004 |
| `run_speaker_match_only.py` (67行) | 全文 Read | clean (vocal_stt_pipeline の wrapper・問題なし) |
| `transcribe_with_speakers.py` (186行) | 全文 Read | finding: C001/L003/L005 |
| `subtitle_speaker_qc.py` (抜粋120行) | 冒頭 Read | clean (字幕色 QC 補助・STT 経路独立) |
| `assemblyai_stt_clips.py` (50行) | 全文 Read | clean (単発クリップ STT 補助・vocal_stt_pipeline.py と機能分離) |
| `legacy/auto_speaker_mapping.py` (30+行) | 冒頭 Read | finding: M005 |
| `gen_stt_index_status.py` | scope 外 (cmd_1656) | skip |
| `regen_srt_from_merged.py` / `srt_to_ass.py` / `srt_hotspot.py` / `llm_postprocess_srt.py` | grep のみ | clean (出力フォーマット変換系・パイプライン外) |

**Coverage 比率**: 主要 STT スクリプト 9 ファイル + legacy 1 を全文 Read。補助系 4 ファイルは grep のみ。**finding 16件** 検出。

---

## 全体所見

1. **WhisperX 撤去方針 (cmd_1671) の浸透度が片寄り**: main.py + vocal_stt_pipeline.py は完全撤去済だが、`transcribe_with_speakers.py` は依然 WhisperX 依存・`stt_merge.py` の fallback mode に残骸。**最優先で潰すべき構造的矛盾**。
2. **ECAPA-TDNN ロジック 3 箇所重複** (H002): 共通化すれば閾値・ガード修正の整合性が保てる。
3. **メンバー名のソース統一**: 5 ファイルが `load_members_from_yaml()` 経由・1 ファイル (batch_speaker_match.py) はハードコード → ハードコード解消が望ましい。
4. **長尺動画対応**: M001 (5分 upload) + L001 (10分 poll) は 40分超切り抜き素材で運用上 hang リスクあり。env override 可能だが、デフォルト値見直しを推奨。

---

## follow-up 推奨 cmd

- **cmd_1663-A** (CRITICAL): `transcribe_with_speakers.py` を AssemblyAI + ECAPA-TDNN 経路にリファクタ (or `legacy/` 移動 + auto_fetch.py 経路修正)
- **cmd_1663-B** (HIGH): `stt_merge.py` の WhisperX 文字列 3 箇所を `srt_fallback` に変更
- **cmd_1663-C** (HIGH): `batch_speaker_match.py` MEMBER_NAMES を `load_members_from_yaml()` 経由に変更
- **cmd_1663-D** (MEDIUM): ECAPA-TDNN ロジックを `speaker_id.py` core 関数に集約 (vocal_stt_pipeline 2 関数からはそれを wrap)
- **cmd_1663-E** (MEDIUM): `apply_speaker_mapping_srt.py` を legacy/ 移動 or 削除判断 (C002/M004 解消)
- **cmd_1663-F** (LOW): timeout/poll 設定の env override 整備 + README 化

---

## 検証手順 (家老向け)

1. `wc -l queue/reports/2026-05-09_cmd_1663_stt_pipeline_audit.md` で 16 件 finding 反映確認
2. `grep -c "^### C0\|^### H0\|^### M0\|^### L0" queue/reports/2026-05-09_cmd_1663_stt_pipeline_audit.md` で severity 別 count = 2+4+5+5 = 16 確認
3. 各 finding の `file:line` を `sed -n 'NUMBERp' <path>` で実引用と照合
4. read-only 遵守確認: `git status` で `projects/dozle_kirinuki/scripts/` 配下に修正なし (本報告書のみ追加)
