---
name: video-qc-llm-mode
description: |
  LLM軍師が動画系cmdをQCする際の4点セット必須チェック (ffprobe + sync_record + drawtext_params_diff + bitrate分析)。
  動画再生不可なLLMでもQC形骸化を防ぐ最低限の数値検証。CONDITIONAL_PASS判定基準と殿への選択肢提示フォーマットを含む。
  「動画QC」「video QC」「LLM動画チェック」「ffprobe検証」「軍師動画QC」「動画QC形骸化対策」で起動。
  Do NOT use for: 漫画ショートQC (→panels整合チェック)。サムネQC (→画像比較)。音声QC (→waveform検証)。
argument-hint: "[cmd_id] [work_dir]"
allowed-tools: Bash, Read
---

# /video-qc-llm-mode — LLM軍師 動画QC 4点セット

## North Star

LLM軍師が動画再生不可でもQCを形骸化させない。ffprobe数値 + sync_record整合 + drawtext params過去比較 + bitrate分析の4点を必須実行し、CONDITIONAL_PASS判定の責任所在を明確にする。

## 背景 (cmd_1485 教訓)

cmd_1485 軍師QCで CONDITIONAL_PASS → 殿「B) スキップでOK」選択 → 殿実視聴NG (画質劣化+時間ズレ) 発覚 → cmd_1487 redo発令。
原因: LLM軍師は動画再生不可ゆえ視覚検証スキップ、ffprobe+sync_recordだけでPASS判定。本スキルで再発防止。

## 起動条件

- 動画系cmd (4視点MIX / ハイライト / ショート等) のQC実施時
- LLM軍師がQCを担当する場合 (人間軍師なら mpv 視聴で完結)
- トリガー: タスクYAMLに「QC」+ 動画成果物が含まれる場合

## 前提: shared_context/qc_template.md 参照

本スキルは `shared_context/qc_template.md` の絶対ルール（全タイプ共通1-8項）を前提とする。重複定義せず、qc_template.mdのルール（実ファイル必読・3箇所目視・証拠報告等）を本スキルでも遵守する。

## 4点チェックリスト (全項目必須実行)

### チェック1: ffprobe 数値検証

元素材 / 中間ファイル / 最終ファイルの全階層に ffprobe を実行し、比較表を出力。

```bash
# テンプレ: 各ファイルに実行
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate,bit_rate -show_entries format=duration,bit_rate -of default=noprint_wrappers=1 <FILE>
```

確認項目:
- [ ] codec: 期待値と一致 (h264/h265/vp9等)
- [ ] resolution: 全ファイルで一致 (1920x1080等)
- [ ] fps: 全ファイルで一致 (30/60等)
- [ ] bitrate: 中間→最終で50%以上の劣化なし
- [ ] duration: 全ファイルで一致 (±0.5秒以内)

異常検知基準:
- bitrate劣化50%超 → ⚠️ WARNING (即FAILではないが要記載)
- resolution不一致 → ❌ FAIL
- fps変動 → ❌ FAIL

### チェック2: sync_record.yaml 整合

```bash
cat <work_dir>/sync_record.yaml
```

確認項目:
- [ ] `measurements` 全項目 (primary/check2/check3) の `confidence` 値確認
- [ ] `adopted_offsets` が全check で一致 (max_diff ≤ 設定threshold)
- [ ] `visual_verification.result` の値が `pass` であること (`pending` は条件付き)
- [ ] seg数・切り替え点が実際のMIX指示と整合

### チェック3: drawtext_params 過去比較

過去動画 (Day5 zephyrus等の参照フォーマット) と drawtext パラメータを比較。

```bash
# 過去drawtext_params_diff.mdがあれば参照
cat <work_dir>/drawtext_params_diff.md
```

確認項目 (各パラメータのdiff出力):
- [ ] fontfile: 同一パス
- [ ] fontsize: 同一値 (例: 48)
- [ ] fontcolor: 同一色 (例: white)
- [ ] bordercolor: 同一色 (例: 0xFF69B4)
- [ ] borderw: 同一値 (例: 3)
- [ ] x/y: 同一位置 (例: w-text_w-20 / 20)

差分が1項目でもあれば ⚠️ WARNING。意図的変更か誤差か判断して記載。

### チェック4: bitrate分析 (元素材 vs 中間 vs 最終)

元素材のbitrateを基準とし、変換段階ごとのbitrate推移を分析。

```bash
# 各ファイルのbitrate取得
for f in <original> <intermediate> <final>; do
  echo "=== $(basename $f) ==="
  ffprobe -v error -select_streams v:0 -show_entries format=bit_rate -of default=nokey=1 "$f"
done
```

確認項目:
- [ ] 元素材 (VP9等) のbitrate基準確認 (例: 4Mbps級)
- [ ] 中間ファイル (h264変換等) で劣化していないか
- [ ] 最終ファイルの見かけbitrateと実質画質の乖離検知
  - 再エンコでbitrate膨らんでも実質劣化済の罠あり
  - bitrateが上がっても画質が向上したとは限らない

分析フォーマット:
```
| ファイル | bitrate | codec | 備考 |
|---------|---------|-------|------|
| 元素材  | X Mbps | VP9   | 基準 |
| 中間    | Y Mbps | H264  | Δ% |
| 最終    | Z Mbps | H264  | Δ% |
```

## CONDITIONAL_PASS 判定基準

4点チェックリスト全PASS だが視覚検証 (mpv) ができない場合のみ CONDITIONAL_PASS とする。

### 判定フロー

```
4点セット全PASS + mpv視聴可能 → PASS
4点セット全PASS + mpv視聴不可 → CONDITIONAL_PASS
4点セット1項目でもFAIL → FAIL
```

### CONDITIONAL_PASS 時の出力フォーマット

QC結果に以下フォーマットで殿への選択肢を必ず含める:

```yaml
qc_result: CONDITIONAL_PASS
reason: "4点セット数値全PASS・LLM視覚検証不可"
lord_options:
  A:
    description: "殿が mpv で視覚確認 → PASS昇格"
    risk: "なし"
  B:
    description: "スキップでPASS → 殿責任で完遂"
    risk: "画質・時間ズレ等の問題を見逃す可能性あり (cmd_1485教訓)"
note: "cmd_1485ではB選択後に殿実視聴NGが発覚。A推奨。"
```

### FAIL 時の必須項目

- どのチェック項目がFAILか
- 実測値 vs 期待値
- 修正指示 (具体的)

## 出力

- `queue/reports/gunshi_report_qc_cmdXXXX.yaml`
- 上記4点の検証結果 + CONDITIONAL_PASS判定 + 殿への選択肢提示

## Do NOT use for

- 漫画ショートQC → panels JSON整合チェック (manga-shortスキル)
- サムネQC → 画像比較・Gemini Vision検証 (thumbnailスキル)
- 音声QC → waveform検証・Demucs品質チェック

## 実行例

```
/video-qc-llm-mode cmd_1487 projects/dozle_kirinuki/work/cmd_1487
```

$ARGUMENTS から cmd_id と work_dir を抽出し、該当ディレクトリの成果物に対して4点チェックを実行。
