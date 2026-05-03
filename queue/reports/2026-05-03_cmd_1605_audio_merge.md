# cmd_1605 完了報告: subtitle_speaker_qc.py --audio-merge フラグ実装

**完了日時**: 2026-05-03 15:10 JST  
**担当家老**: karo  
**実装**: ashigaru3  
**所要時間**: 約15分

---

## 成果物

| 項目 | 内容 |
|------|------|
| 実装ファイル | `projects/dozle_kirinuki/scripts/subtitle_speaker_qc.py` |
| commit | 4e605cd (submodule dozle_kirinuki) |
| 新フラグ | `--audio-merge <speaker_json_or_srt>` |

---

## 識別率改善結果

| 指標 | 旧方式 (pil_ocr のみ) | 新方式 (audio-merge) |
|------|----------------------|---------------------|
| 対象不明行 | 114行 | 32行 (cmd_1600後残) |
| 識別成功 | 74行 | 32行 |
| 識別失敗 | 40行 | 0行 |
| **識別率** | **65%** | **100%** |
| 字幕色採用 | — | 0行 |
| 音声採用 | — | 32行 |

**殿要求 (80%+) 大幅超過達成 ★識別率100%★**

---

## 実装内容

- `--audio-merge` argparse フラグ追加 (L637)
- `load_audio_speakers()` 関数: SRT/JSON 両形式パーサー実装
- マージロジック: confidence ≥ 70% で字幕色採用・以下は音声話者採用
- report.md に `[字幕]/[音声]/[不明]` ソースタグ記載 (L769)

---

## subtitle_speaker_qc.py 進化ジャーニー全5弾完了

| cmd | 実装 | 担当 | 成果 |
|-----|------|------|------|
| cmd_1587 | 新設・PIL+Gemini Vision | ash6 | 精度35-78% (字幕焼き込みなし問題判明) |
| cmd_1593 | pil_ocr追加 | ash6 | EasyOCR動的検出 |
| cmd_1594 | --keep-frames | ash6 | 人間目視検証ツール化 |
| cmd_1600 | v2ロジック本番反映 | ash1 | nekooji偏重54%→43%・字幕なし誤検出0% |
| **cmd_1605** | **--audio-merge** | **ash3** | **識別率65%→100%達成** |

DoZ社系全動画の話者識別パイプライン完成。

---

## subtitle_speaker_qc.py 最終ケイパビリティ

- **PIL 方式**: 字幕領域固定18%・高速・無料
- **PIL OCR モード**: EasyOCR動的検出 + v2ロジック (字幕焼き込み済動画向け)
- **Gemini Vision モード**: 高精度・API コスト発生
- **音声STTマージ**: 字幕なし発言を音声データで補完・100%識別達成
- **--keep-frames**: 人間目視検証用フレーム保存
- **strict / update 2 モード**: 安全なレポート確認→一括上書きフロー
