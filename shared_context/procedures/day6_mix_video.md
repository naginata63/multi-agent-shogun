# Day6 4視点 MIX 動画生成 手順 (cmd_1464)

## 概要

Day6 ボス1戦目(142秒) + 8戦目(2150秒) の4視点MIX動画をseg独立方式で生成し、
wipeleft+SE境界トランジションで1本に結合。YouTube非公開アップ。

## 入力ファイル

```
DAY6="/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/20260416_【#DoZ】6日目 腹から声が出ないヒーラーに命を任せれられるとでも？【ドズル社／おおはらMEN視点】"
WORK="/home/murakami/multi-agent-shogun/work/cmd_1464"

# 1戦目 4本
$DAY6/multi_h264_1sen/oo_men_1sen.mp4      # 142.0s  h264/aac
$DAY6/multi_h264_1sen/charlotte_1sen.mp4   # 142.05s h264/opus
$DAY6/multi_h264_1sen/hendy_1sen.mp4       # 142.08s h264/aac
$DAY6/multi_h264_1sen/tsurugi_1sen.mp4     # 142.08s h264/aac

# 8戦目 4本
$DAY6/multi_h264_8sen/oo_men_8sen.mp4      # 2150.0s  h264/aac
$DAY6/multi_h264_8sen/charlotte_8sen.mp4   # 2150.0s  h264/opus ★opusに注意
$DAY6/multi_h264_8sen/hendy_8sen.mp4       # 2150.08s h264/aac
$DAY6/multi_h264_8sen/tsurugi_8sen.mp4     # 2150.08s h264/aac

# SE
SE="/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/assets/bgm/sfx/sceneswitch1.mp3"
```

**charlotte audio=opus**: filter_complex内でaac変換が自動実施される。opus入力をffmpegが自動デコードする。

## Step 1: advisor() 呼び出し（実装前）

## Step 2: 視点同期調整

multi_view_sync.md に従い、4視点の開始タイムオフセットを計算せよ。

```bash
cat /home/murakami/multi-agent-shogun/shared_context/procedures/multi_view_sync.md
```

oo_men をアンカー(offset=0)として charlotte/hendy/tsurugi の同期ずれを測定する。
測定結果を `$WORK/sync_offsets.json` に記録せよ。

## Step 3: 視点切替タイムライン設計

1戦目(142秒)と8戦目(2150秒)それぞれについて、視点切替タイムラインを設計せよ。

**ルール**:
- 最初: MEN視点 (oo_men)
- 最後: MEN視点 (oo_men)
- 中間: charlotte / hendy / tsurugi にバリエーション切替
- 30-60秒ごとに切替（足軽判断）
- 盛り上がりシーン: 4画面 grid (2x2) を挟む（足軽判断で数回）
- 4画面 grid 時の音声: MEN音声

タイムラインを `$WORK/timeline_1sen.json` と `$WORK/timeline_8sen.json` に記録せよ。
例:
```json
[
  {"start": 0, "end": 40, "view": "oo_men"},
  {"start": 40, "end": 80, "view": "charlotte"},
  {"start": 80, "end": 100, "view": "grid4"},
  {"start": 100, "end": 142, "view": "oo_men"}
]
```

## Step 4: seg1戦目.mp4 生成

参考: `work/zephyrus_v3.sh` のfilter_complexパターン

**ffmpeg filter_complex 要件**:
- 映像: タイムライン通りに視点切替 (trim/setpts + concat or select)
- 音声: 表示視点の音声追従 (4画面 grid 時は oo_men 音声)
- テロップ: 右上に「エキドナ(初戦)」を全期間表示
  `drawtext=fontfile=/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc:text='エキドナ(初戦)':x=w-tw-30:y=30:fontsize=36:fontcolor=white:box=1:boxcolor=black@0.5`
- 出力: h264_nvenc / aac 192k / 1080p / bitrate 14Mbps

```bash
ffmpeg [inputs] -filter_complex "[filter_complex]" \
  -c:v h264_nvenc -preset p4 -b:v 14M \
  -c:a aac -b:a 192k \
  "$WORK/seg1sen.mp4"
```

## Step 5: seg8戦目.mp4 生成

同様に 8戦目用のfilter_complexを構築。テロップ「エキドナ(8戦目)」を全期間表示。

```bash
ffmpeg [inputs] -filter_complex "[filter_complex]" \
  -c:v h264_nvenc -preset p4 -b:v 14M \
  -c:a aac -b:a 192k \
  "$WORK/seg8sen.mp4"
```

## Step 6: 境界 transition.mp4 生成 (wipeleft + sceneswitch1 SE)

seg1戦目末尾2秒 + seg8戦目冒頭2秒 を xfade=wipeleft でトランジション。
sceneswitch1.mp3 SE を重ねる。出力は約3-4秒。

```bash
# seg1末尾2秒抽出
TAIL_DUR=2
SEG1_DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$WORK/seg1sen.mp4")
SEG1_TAIL_START=$(python3 -c "print($SEG1_DUR - $TAIL_DUR)")

ffmpeg -ss "$SEG1_TAIL_START" -t "$TAIL_DUR" -i "$WORK/seg1sen.mp4" "$WORK/tail_seg1.mp4"
ffmpeg -ss 0 -t "$TAIL_DUR" -i "$WORK/seg8sen.mp4" "$WORK/head_seg8.mp4"

# xfade wipeleft + SE overlay
ffmpeg \
  -i "$WORK/tail_seg1.mp4" \
  -i "$WORK/head_seg8.mp4" \
  -i "$SE" \
  -filter_complex "
    [0:v][1:v]xfade=transition=wipeleft:duration=1.0:offset=1.0[vout];
    [0:a][1:a]acrossfade=d=1.0[across];
    [2:a]volume=1.5[se];
    [across][se]amix=inputs=2:normalize=0[aout]
  " \
  -map "[vout]" -map "[aout]" \
  -c:v h264_nvenc -preset p4 -c:a aac -b:a 192k \
  "$WORK/transition.mp4"
```

## Step 7: concat → final.mp4

seg1(末尾2秒切除) + transition + seg8(冒頭2秒切除) を concat。

```bash
# seg1 本体 (末尾 TAIL_DUR 秒を除く)
SEG1_BODY_DUR=$(python3 -c "print($SEG1_DUR - $TAIL_DUR)")
ffmpeg -t "$SEG1_BODY_DUR" -i "$WORK/seg1sen.mp4" -c copy "$WORK/seg1_body.mp4"

# seg8 本体 (冒頭 TAIL_DUR 秒を除く)
SEG8_DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$WORK/seg8sen.mp4")
ffmpeg -ss "$TAIL_DUR" -i "$WORK/seg8sen.mp4" -c copy "$WORK/seg8_body.mp4"

# concat list
printf "file '%s'\nfile '%s'\nfile '%s'\n" \
  "$WORK/seg1_body.mp4" \
  "$WORK/transition.mp4" \
  "$WORK/seg8_body.mp4" \
  > "$WORK/final_concat.txt"

ffmpeg -f concat -safe 0 -i "$WORK/final_concat.txt" -c copy \
  "$WORK/final.mp4"
```

## Step 8: 品質確認

```bash
ffprobe -v quiet -show_entries stream=codec_name,duration,width,height -of csv=p=0 "$WORK/final.mp4"
```

確認項目:
- video codec: h264 ✓
- audio codec: aac ✓
- duration ≈ 2292秒 (142 + 2150 + transition)
- resolution: 1920x1080 ✓

## Step 9: YouTube 非公開アップ

```bash
cat /home/murakami/multi-agent-shogun/shared_context/procedures/youtube_upload.md
```

手順書に従い非公開アップ。パラメータ:
- title: (description.md の案を参考に足軽が判断)
- defaultLanguage: ja
- defaultAudioLanguage: ja
- privacyStatus: private

URL を報告に記録。

## Step 10: advisor() 呼び出し（完了前）

## Step 11: git commit + push

```bash
cd /home/murakami/multi-agent-shogun
git add shared_context/procedures/day6_mix_video.md
git add -f queue/tasks/ashigaru1.yaml  # 自分のタスクは不要だが念のため
git diff --cached --name-only
git commit -m "feat(cmd_1464): Day6 4視点MIX動画 final.mp4 生成完了"
git push origin main
```

## Step 12: report + inbox

`queue/reports/ashigaru1_report_subtask_1464a.yaml` を作成:

```yaml
worker_id: ashigaru1
task_id: subtask_1464a
parent_cmd: cmd_1464
timestamp: "<ISO8601>"
status: done
result:
  summary: "..."
  youtube_url: "https://youtu.be/..."
  files_created:
    - "work/cmd_1464/seg1sen.mp4"
    - "work/cmd_1464/seg8sen.mp4"
    - "work/cmd_1464/transition.mp4"
    - "work/cmd_1464/final.mp4"
  verification:
    final_duration_sec: ~2292
    codec: h264/aac
    resolution: 1920x1080
skill_candidate:
  found: false
hotfix_notes: null
```

完了後: `bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh gunshi '足軽1号、subtask_1464a完了(Day6 4視点MIX final.mp4+YouTube非公開URL)。QC依頼。' report_completed ashigaru1`
