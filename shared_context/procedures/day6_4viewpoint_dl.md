# Day6 4視点 h264 DL・切出 手順 (cmd_1463)

## 対象シーン

| シーン | MEN視点タイムスタンプ | 秒数 |
|--------|----------------------|------|
| ボス1戦目 | 1:39:28 ~ 1:41:50 | 142秒 |
| ボス8戦目 | 3:55:10 ~ 4:31:00 | 2150秒 (約35分50秒) |

## 4視点 URL

| 視点 | プラットフォーム | ID / URL |
|------|----------------|----------|
| oo_men | YouTube (ローカル) | t7JJlTDACyc |
| charlotte | YouTube | v19JAnVjZ_c |
| hendy | Twitch VOD | 2749323185 |
| tsurugi | Twitch VOD | 2749326446 |

## 作業パス定義

```bash
DAY6="/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/20260416_【#DoZ】6日目 腹から声が出ないヒーラーに命を任せれられるとでも？【ドズル社／おおはらMEN視点】"
WORK="/home/murakami/multi-agent-shogun/work/cmd_1463"
mkdir -p "$DAY6/multi_h264_1sen" "$DAY6/multi_h264_8sen" "$WORK"
```

## Step 1: advisor() 呼び出し（実装前）

## Step 2: oo_men codec 確認

oo_men ローカルパーツは既にh264か確認（h264ならffmpegで直接切り出せる）:

```bash
ffprobe -v quiet -show_streams "$DAY6/t7JJlTDACyc_part_01.mp4" | grep codec_name | head -2
```

期待値: `codec_name=h264`（h264なら `-c copy` で再エンコード不要）

## Step 3: charlotte DL (YouTube, h264強制)

```bash
# 1戦目 (142秒)
yt-dlp -f "bestvideo[vcodec^=avc1][height<=1080]+bestaudio/bestvideo[vcodec^=avc1]+bestaudio" \
  --download-sections "*1:39:28-1:41:50" \
  --merge-output-format mp4 \
  -o "$DAY6/multi_h264_1sen/charlotte_1sen.mp4" \
  "https://www.youtube.com/watch?v=v19JAnVjZ_c"

# 8戦目 (2150秒)
yt-dlp -f "bestvideo[vcodec^=avc1][height<=1080]+bestaudio/bestvideo[vcodec^=avc1]+bestaudio" \
  --download-sections "*3:55:10-4:31:00" \
  --merge-output-format mp4 \
  -o "$DAY6/multi_h264_8sen/charlotte_8sen.mp4" \
  "https://www.youtube.com/watch?v=v19JAnVjZ_c"
```

## Step 4: hendy DL (Twitch)

```bash
# 1戦目
yt-dlp -f "best[vcodec^=avc1]/best" \
  --download-sections "*1:39:28-1:41:50" \
  --merge-output-format mp4 \
  -o "$DAY6/multi_h264_1sen/hendy_1sen.mp4" \
  "https://www.twitch.tv/videos/2749323185"

# 8戦目
yt-dlp -f "best[vcodec^=avc1]/best" \
  --download-sections "*3:55:10-4:31:00" \
  --merge-output-format mp4 \
  -o "$DAY6/multi_h264_8sen/hendy_8sen.mp4" \
  "https://www.twitch.tv/videos/2749323185"
```

## Step 5: tsurugi DL (Twitch)

```bash
# 1戦目
yt-dlp -f "best[vcodec^=avc1]/best" \
  --download-sections "*1:39:28-1:41:50" \
  --merge-output-format mp4 \
  -o "$DAY6/multi_h264_1sen/tsurugi_1sen.mp4" \
  "https://www.twitch.tv/videos/2749326446"

# 8戦目
yt-dlp -f "best[vcodec^=avc1]/best" \
  --download-sections "*3:55:10-4:31:00" \
  --merge-output-format mp4 \
  -o "$DAY6/multi_h264_8sen/tsurugi_8sen.mp4" \
  "https://www.twitch.tv/videos/2749326446"
```

## Step 6: oo_men 切出 (ローカル parts)

oo_men は既存ローカルパーツから ffmpeg で切り出す。パーツは各 3600s (1時間) ごと。

```bash
# oo_men codec 確認（Step2）で h264 確認済みなら -c copy。未確認なら -c:v h264_nvenc -preset p4

# 1戦目: part_01 から切出 (1:39:28 = 5968s; part_01 start = ~3600s; offset = 2368s)
ffmpeg -ss 2368 -t 142 -i "$DAY6/t7JJlTDACyc_part_01.mp4" \
  -c:v h264_nvenc -preset p4 -c:a aac -b:a 192k \
  "$DAY6/multi_h264_1sen/oo_men_1sen.mp4"

# 8戦目: part_03(offset 3310s, 290s) + part_04(offset 0s, 1860s) を連結
# 3:55:10 = 14110s; part_03 start = ~10800s; offset = 3310s; end = 14400s → 290s
# 4:31:00 = 16260s; part_04 start = ~14400s; offset = 0s → 1860s

ffmpeg -ss 3310 -t 290 -i "$DAY6/t7JJlTDACyc_part_03.mp4" \
  -c:v h264_nvenc -preset p4 -c:a aac -b:a 192k \
  "$WORK/oo_men_8sen_part03.mp4"

ffmpeg -ss 0 -t 1860 -i "$DAY6/t7JJlTDACyc_part_04.mp4" \
  -c:v h264_nvenc -preset p4 -c:a aac -b:a 192k \
  "$WORK/oo_men_8sen_part04.mp4"

# concat list 作成
printf "file '%s'\nfile '%s'\n" \
  "$WORK/oo_men_8sen_part03.mp4" \
  "$WORK/oo_men_8sen_part04.mp4" \
  > "$WORK/oo_men_8sen_concat.txt"

# 連結 (-c copy: 両セグメント同コーデック)
ffmpeg -f concat -safe 0 -i "$WORK/oo_men_8sen_concat.txt" -c copy \
  "$DAY6/multi_h264_8sen/oo_men_8sen.mp4"
```

**注意**: part_03/04 の正確な開始時刻はパーツ 00〜02 の累積 duration に依存する。ずれが 5秒以上なら:
```bash
# 正確な offset 計算
d0=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$DAY6/t7JJlTDACyc_part_00.mp4")
d1=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$DAY6/t7JJlTDACyc_part_01.mp4")
d2=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$DAY6/t7JJlTDACyc_part_02.mp4")
python3 -c "d0,d1,d2=$d0,$d1,$d2; p3_start=d0+d1+d2; print(f'part_03 start={p3_start:.1f}s'); print(f'8sen offset in part_03={14110-p3_start:.1f}s')"
```

## Step 7: ffprobe 検証

```bash
echo "=== 1戦目 4本 ===" 
for f in "$DAY6/multi_h264_1sen/"*.mp4; do
  echo "[$f]"
  ffprobe -v quiet -show_entries stream=codec_name,duration -of csv=p=0 "$f"
done

echo "=== 8戦目 4本 ==="
for f in "$DAY6/multi_h264_8sen/"*.mp4; do
  echo "[$f]"
  ffprobe -v quiet -show_entries stream=codec_name,duration -of csv=p=0 "$f"
done
```

期待値:
- 全ファイル: codec_name=h264 確認
- 1戦目: duration ≈ 142s (±5s)
- 8戦目: duration ≈ 2150s (±30s)
- oo_men_8sen.mp4: duration ≈ 2150s (290+1860=2150s)

## Step 8: source.json 作成

`"$DAY6/multi_h264_1sen/source.json"` を作成（1戦目・8戦目 両シーン記録）:

```json
{
  "video_title": "【#DoZ】6日目 腹から声が出ないヒーラーに命を任せれられるとでも？【ドズル社／おおはらMEN視点】",
  "day": 6,
  "created_at": "YYYY-MM-DDTHH:MM:SS",
  "range_sections": [
    {
      "section": "ボス1戦目",
      "men_timestamp_start": "1:39:28",
      "men_timestamp_end": "1:41:50",
      "duration_sec": 142,
      "output_dir": "multi_h264_1sen",
      "note": "MEN視点基準タイムスタンプ。他視点sync調整はMIX cmdで実施"
    },
    {
      "section": "ボス8戦目",
      "men_timestamp_start": "3:55:10",
      "men_timestamp_end": "4:31:00",
      "duration_sec": 2150,
      "output_dir": "multi_h264_8sen",
      "note": "MEN視点基準タイムスタンプ。他視点sync調整はMIX cmdで実施"
    }
  ],
  "sources": {
    "oo_men": {
      "platform": "youtube",
      "video_id": "t7JJlTDACyc",
      "url": "https://www.youtube.com/watch?v=t7JJlTDACyc",
      "codec_output": "h264",
      "source_method": "local_ffmpeg_cut",
      "local_parts": "t7JJlTDACyc_part_00-09.mp4"
    },
    "charlotte": {
      "platform": "youtube",
      "video_id": "v19JAnVjZ_c",
      "url": "https://www.youtube.com/watch?v=v19JAnVjZ_c",
      "codec_output": "h264",
      "source_method": "yt-dlp_download_sections"
    },
    "hendy": {
      "platform": "twitch",
      "video_id": "2749323185",
      "url": "https://www.twitch.tv/videos/2749323185",
      "codec_output": "h264",
      "source_method": "yt-dlp_download_sections"
    },
    "tsurugi": {
      "platform": "twitch",
      "video_id": "2749326446",
      "url": "https://www.twitch.tv/videos/2749326446",
      "codec_output": "h264",
      "source_method": "yt-dlp_download_sections"
    }
  }
}
```

## Step 9: description.md draft 作成

`"$DAY6/multi_h264_1sen/description.md"` を作成。4視点MIX動画用の概要欄案:

```markdown
# Day6 ボス戦 4視点MIX 概要欄案

## 1戦目 (1:39:28 - 1:41:50)

**タイトル案**: 【4視点】DoZ Day6 ボス1戦目 — ヒーラー初挑戦！

**概要欄**:
DoZ Day6 のボス1戦目を4視点でお届け！
腹から声が出ないヒーラーとパーティメンバーの緊迫の戦闘を全視点でご覧ください。

出演: ドズル社（おおはらMEN・シャーロット・Hendy・ツルギ）

## 8戦目 (3:55:10 - 4:31:00)

**タイトル案**: 【4視点】DoZ Day6 ボス8戦目 — 35分の死闘！

**概要欄**:
DoZ Day6 のボス8戦目 約35分間を4視点で完全収録！
（詳細は MIX cmd で調整）
```

## Step 10: git commit + push

```bash
cd /home/murakami/multi-agent-shogun
git add shared_context/procedures/day6_4viewpoint_dl.md
git diff --cached  # 意図外ファイル確認
git commit -m "feat(cmd_1463): Day6 4視点DL手順テンプレート追加"
git push origin main
```

※ video ファイル (projects/dozle_kirinuki/work/) は .gitignore 対象のためコミット不要。
※ source.json / description.md も projects/ 配下のため git 管理外でOK。

## Step 11: advisor() 呼び出し（完了前）

## Step 12: report + inbox

`/home/murakami/multi-agent-shogun/queue/reports/ashigaru1_report_subtask_1463a.yaml` を作成:

```yaml
worker_id: ashigaru1
task_id: subtask_1463a
parent_cmd: cmd_1463
timestamp: "<ISO8601>"
status: done
result:
  summary: "..."
  files_created:
    - "<path>/multi_h264_1sen/charlotte_1sen.mp4"
    - "<path>/multi_h264_1sen/hendy_1sen.mp4"
    - "<path>/multi_h264_1sen/tsurugi_1sen.mp4"
    - "<path>/multi_h264_1sen/oo_men_1sen.mp4"
    - "<path>/multi_h264_8sen/charlotte_8sen.mp4"
    - "<path>/multi_h264_8sen/hendy_8sen.mp4"
    - "<path>/multi_h264_8sen/tsurugi_8sen.mp4"
    - "<path>/multi_h264_8sen/oo_men_8sen.mp4"
    - "<path>/multi_h264_1sen/source.json"
    - "<path>/multi_h264_1sen/description.md"
  verification:
    codec_all_h264: true
    dur_1sen_ok: "~142s"
    dur_8sen_ok: "~2150s"
skill_candidate:
  found: false
hotfix_notes: null
```

完了後: `bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh gunshi '足軽1号、subtask_1463a完了(Day6 4視点8本生成+source.json+description.md)。QC依頼。' report_completed ashigaru1`
