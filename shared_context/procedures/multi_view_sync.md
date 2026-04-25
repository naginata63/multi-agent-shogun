# 複数視点動画の音声同期・MIX手順

DoZシリーズ等のチーム配信動画を複数視点でMIXする際の手順と鉄則。

## 対象ツール
- `projects/dozle_kirinuki/scripts/sync_multi_videos.py` — 音声同期・オフセット算出
- ffmpeg filter_complex — 2x2グリッド等のMIX描画

## 前提
- 複数視点の同じイベント（同じ戦闘・同じ場面）が対象
- 全動画に**同じ音声**（戦闘効果音・会話）が含まれていること
- 各動画は1時間単位に分割済（`*_part_NN.mp4`）推奨

## ステップ

### Step 1: 初回音声同期
```bash
python3 projects/dozle_kirinuki/scripts/sync_multi_videos.py \
  --ref   "MEN視点/gszoq-2br2o_part_00.mp4" \
  --views "multi/day5_twitch_part_00.mp4" "multi/day5_youtube_part_00.mp4" \
  --output "multi/sync_offsets.json" \
  --sample-sec 60 \
  --start-sec 1800 \
  --view-search-range 600
```

### Step 2: 二重チェック（必須）
**別の時刻**で同じ計算を実行し、オフセットが一致するか確認する。

```bash
# 別の時刻（例: 600秒地点）で再計算
python3 ... --start-sec 600 --output sync_check1.json
# さらに別時刻（例: 2400秒地点）
python3 ... --start-sec 2400 --output sync_check2.json
```

両者のオフセット差が **±0.5秒以内**なら信頼OK。大きくズレる場合は：
- サンプル尺を延ばす（`--sample-sec 180`）
- 検索範囲を拡大（`--view-search-range 1500`）
- **conf=1.00 でも誤検出はある**ため二重チェック必須

### Step 3: confidence 値の目安
| conf | 判定 |
|------|------|
| **1.00** | 信頼度最高（ただし誤検出ゼロではない）|
| 0.80〜0.99 | 通常運用OK |
| 0.50〜0.79 | **要再試行**（サンプル尺延長 / 検索範囲拡大）|
| < 0.50 | 同期不可・手動同期検討 |

### Step 4: 検索範囲の見積
`--view-search-range` は**想定オフセットの2倍以上**を確保せよ。
- 配信開始が同時でも、ラグ・遅延で ±5〜10分ズレ得る
- **デフォルト 600秒では不足する可能性**（過去事例: twitch が +807秒ズレていた）
- 推奨: **1500秒以上**でまず試す

### Step 5: MIX描画（ffmpeg filter_complex）

#### A: 2x2グリッド（推奨）
```bash
ffmpeg -y \
  -ss REF_START -t 300 -i "ref.mp4" \
  -ss VIEW1_START -t 300 -i "view1.mp4" \
  -ss VIEW2_START -t 300 -i "view2.mp4" \
  -filter_complex "\
    [0:v]scale=960:540,setsar=1[v0];\
    [1:v]scale=960:540,setsar=1[v1];\
    [2:v]scale=960:540,setsar=1[v2];\
    color=black:size=960x540:duration=300[v3];\
    [v0][v1]hstack=inputs=2[top];\
    [v2][v3]hstack=inputs=2[bot];\
    [top][bot]vstack=inputs=2[vout];\
    [0:a][1:a][2:a]amix=inputs=3:duration=longest,volume=2.0[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v h264_nvenc -preset p4 -rc vbr -cq 23 -b:v 8M -maxrate 10M -bufsize 16M \
  -c:a aac -b:a 192k \
  preview.mp4
```

VIEW1_START = REF_START + offset1
VIEW2_START = REF_START + offset2

### Step 6: 同期検証（ピッタリかの確認）
1. 音声を3ch `amix` して出力 → 動画確認
2. **同期OKなら**: 音声が厚く重なる（やや反響感あるが各メンバー発言は一致）
3. **同期ズレなら**: エコー/ダブり/声の遅れが聞き取れる

## トラブルシュート

### twitch側のオフセットが大幅ズレ
- 配信ラグで twitch は YouTube より大幅に遅れることがある（+500秒超）
- 対策: `--view-search-range` を **1500〜2000秒** に拡大

### conf 値が低い
- 静かな区間（無音）でサンプル取得している可能性
- 対策: `--start-sec` を戦闘シーン中央に変更（会話・効果音が確実にある時刻）

### 長尺動画の一部のみ対象
- part分割済みファイルを個別指定（1時間単位）
- オフセットが ±600秒を超える場合、part番号自体がズレる可能性あり

## 既知ケース
| 日 | ref | view | offset(s) | conf |
|----|-----|------|-----------|------|
| 5日目 | gszoq-2br2o_part_00 | day5_twitch_part_00 | **+807.85** | 1.00 |
| 5日目 | gszoq-2br2o_part_00 | day5_youtube_part_00 | **−240.85** | 1.00 |

## Step 7: sync_record.yaml 生成（必須）

MIX完了時、以下のフォーマットで `sync_record.yaml` を必ず生成せよ。
この記録が無い場合、MIXの正確性を事後検証できない（cmd_1464教訓）。

```yaml
# sync_record.yaml フォーマット
video_title: "Day6 エキドナ 1+8戦目"
reference_view: "MEN (gszoq-2br2o)"
sync_method: "sync_multi_videos.py"
created_at: "2026-04-25T19:00:00+09:00"
segments:
  - seg_id: "seg1sen"
    label: "1戦目"
    ref_start: 0.0
    duration: 180.5
    view_switches:
      - time: 0.0
        view: "MEN"
      - time: 30.0
        view: "4grid"
      - time: 150.0
        view: "MEN"
    audio_mode: "main_view_switch"
    transition: "wipeleft+sceneswitch1"
    top_right_telop: "エキドナ(初戦)"
  - seg_id: "seg8sen"
    label: "8戦目"
    ref_start: 180.5
    duration: 2150.0
    view_switches:
      - time: 0.0
        view: "MEN"
      - time: 60.0
        view: "charlotte"
      # ...
    audio_mode: "main_view_switch"
    transition: "wipeleft+sceneswitch1"
    top_right_telop: "エキドナ(8戦目)"
offsets:
  twitch: { offset_sec: 807.85, conf: 1.00, sample_sec: 60, start_sec: 1800 }
  youtube: { offset_sec: -240.85, conf: 1.00, sample_sec: 60, start_sec: 1800 }
visual_verification:
  method: "mpv --speed=2.0"
  result: "pass"
  checked_by: "gunshi"
  checked_at: "2026-04-25T20:00:00+09:00"
```

## 鉄則
1. **二重チェック必須** — 2つの異なる時刻で同期計算し、結果が一致することを確認
2. **検索範囲は広めに** — デフォルト600秒ではなく1500秒以上
3. **conf=1.00でも疑え** — 数値と耳の両方で判断
4. **音声3ch amix 検証** — 最終確認は動画再生で
5. **sync_record.yaml なしの MIX は完了とみなさない** — Step 7 の記録生成が MIX 完了の必須条件。軍師 QC もこの記録の存在と整合性を検証せよ（cmd_1464 QC形骸化対策）
