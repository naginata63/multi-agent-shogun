# cmd_1613 STT Audit 20件修正 完了報告書

- **日時**: 2026-05-04
- **対象**: STTパイプライン 8ファイル（vocal_stt_pipeline.py / stt_merge.py / speaker_id.py / transcribe_with_speakers.py / assemblyai_stt_clips.py / apply_speaker_mapping_srt.py / batch_speaker_match.py / subtitle_speaker_qc.py）
- **監査**: 軍師夜間矛盾監査（gunshi_stt_contradiction_20260504.yaml）
- **成果**: CRITICAL 2 / HIGH 6 / MEDIUM 7 / LOW 5 = 計20件 全修正完了

## 修正対応表

### Phase-A（ashigaru2担当）— commit `0004818`

| # | Finding ID | Severity | File | 修正概要 |
|---|-----------|----------|------|----------|
| 1 | STT_C001 | CRITICAL | speaker_id.py | `_REPO_SCRIPTS_DIR` を `str(_SCRIPT_DIR)` に変更（存在しないディレクトリ指参照解消） |
| 2 | STT_C002 | CRITICAL | transcribe_with_speakers.py | whisperx を関数内 lazy import 化 + 重複 import os 削除 |
| 3 | STT_M004 | MEDIUM | speaker_id.py | コメント「以下なら unknown」→「閾値未満なら unknown」に統一 |
| 4 | STT_M005 | MEDIUM | transcribe_with_speakers.py | `_apply_vocab` の content_selector import 除去 → yaml 直読みに独立化 |
| 5 | STT_M006 | MEDIUM | run_speaker_match_only.py | 未使用 PROJECT_DIR 変数削除 |
| 6 | STT_L002 | LOW | transcribe_with_speakers.py | PUNCTUATION set に「日本語+英語切れ目を最大公約で網羅」コメント追加 |

### Phase-B（ashigaru5担当）— commit `d8ed8bc`

| # | Finding ID | Severity | File | 修正概要 |
|---|-----------|----------|------|----------|
| 7 | STT_H001 | HIGH | vocal_stt_pipeline.py | concat_vocals の `-c copy` → `-c:a pcm_s16le -ar 16000` 再エンコード結合 |
| 8 | STT_H002 | HIGH | vocal_stt_pipeline.py | AssemblyAI 400 fallback 時 `assemblyai_fallback: true` を metadata に明記 |
| 9 | STT_H004 | HIGH | vocal_stt_pipeline.py | `speaker_label_mode` を metadata に書き込み、use_direct 判定を metadata 参照に |
| 10 | STT_M001 | MEDIUM | vocal_stt_pipeline.py | `_bootstrap_ecapa` / `_load_ecapa_classifier` / `_load_voice_profiles` / `_update_merge_report` / `_mark_ecapa_skipped` / `_get_profile_dir` ヘルパー関数切出し |
| 11 | STT_M002 | MEDIUM | vocal_stt_pipeline.py | DIRECT_* モジュール定数化 + env var 上書き対応 |
| 12 | STT_L001 | LOW | vocal_stt_pipeline.py | `--gemini` help → `[DEPRECATED — 無視されます]` 明示化 |

### Phase-C（ashigaru7担当）— commit `9a0ebeb`

| # | Finding ID | Severity | File | 修正概要 |
|---|-----------|----------|------|----------|
| 13 | STT_H003 | HIGH | stt_merge.py | detect_timestamp_unit ヒューリスティック廃止 → load_assemblyai() ms固定 / load_deepgram() s固定の明示変換 |
| 14 | STT_H005 | HIGH | stt_merge.py | `gap_threshold_ms = gap_threshold_ms` 自己代入 no-op 行削除 |
| 15 | STT_H006 | HIGH | apply_speaker_mapping_srt.py | MAPPINGS dict → `context/speaker_mappings.yaml` 外部化 + `load_mappings()` 実装 |
| 16 | STT_M003 | MEDIUM | stt_merge.py | legacy mode でも output_json 同ディレクトリから YouTube字幕自動検索分岐追加 |
| 17 | STT_L003 | LOW | stt_merge.py | ぺけたん ガベージキーワードに出典コメント追加 |

### Phase-D（ashigaru7担当）— commit `9a0ebeb`

| # | Finding ID | Severity | File | 修正概要 |
|---|-----------|----------|------|----------|
| 18 | STT_M007 | MEDIUM | subtitle_speaker_qc.py | `--method gemini` → RuntimeError('Part.from_bytes 廃止。--method pil_ocr を使用') に deprecated 化 |
| 19 | STT_L004 | LOW | batch_speaker_match.py | no-op `if video_id.startswith('_'): video_id = video_id` 削除 → コメントに置換 |
| 20 | STT_L005 | LOW | subtitle_speaker_qc.py | generate_report の audio_merge_path → `args.merge_stt_json or args.audio_merge` + ラベル分岐表示 |

## Regression Test

```
$ python3 -c 'import sys; sys.path.insert(0,"scripts"); import vocal_stt_pipeline; import speaker_id; import stt_merge; print("ALL IMPORTS OK")'
ALL IMPORTS OK
```

## Commit Hash 一覧

| Phase | Commit Hash | 担当 | Finding IDs |
|-------|------------|------|-------------|
| A | `0004818` | ashigaru2 | C001, C002, M004, M005, M006, L002 |
| B | `d8ed8bc` | ashigaru5 | H001, H002, H004, M001, M002, L001 |
| C+D | `9a0ebeb` | ashigaru7 | H003, H005, H006, M003, L003, M007, L004, L005 |

## 備考

- Phase-C と Phase-D は同一 commit (`9a0ebeb`) に含まれている（ashigaru7 が両方担当）
- Submodule dirty 状態は cmd_1613 と無関係（yukigassen 画像削除・analytics 更新等）
- 全20件の gunshi interim QC PASS 済み
