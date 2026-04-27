# Countdown Timer Overlay (動画にカウントダウン重畳)

ボス戦・タイマー演出など、動画の特定区間に「残り M:SS.cc」カウントダウンを重畳する標準手順。
**本番採用 = ffmpeg drawtext 方式**（Remotion はテスト止まり）。

実例: 4/20 ドズル社2日目3層オーディン戦15分タイマー (`day2_3層オーディン_final.mp4` → YouTube `GEyfSBKLBhA`)

## 採用方式: ffmpeg drawtext

### 鉄則
1. **NVENC 必須** (`shared_context/procedures/ffmpeg_nvenc.md` 準拠) — libx264 禁止
2. **5分毎に大きく** — 64px → 96px → 128px の3段階拡大が殿の標準仕様
3. **10ms (0.01秒) 刻み表示** — `M:SS.cc` 形式（小数2桁）でスポーツ実況感
4. **位置は右上固定** — `x=w-text_w-20:y=20`（YouTube UI と被らない）
5. **色は白文字+ピンク縁取り** — `fontcolor=white:bordercolor=0xFF69B4:borderw=3`
6. **フォント** — `/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc`
7. **タイマー終了後はゼロ固定** — `if(lte(t,END),START-t,0)` で負値表示を防ぐ
8. **タイマー本体と同尺の動画にだけ重畳** — ffmpeg `-ss` で範囲限定 or `enable='between(t,A,B)'` で表示制御
9. **音声・他ストリームは `-c:a copy` (再エンコード不要時)** — drawtext は映像のみ

### パラメータ算出

| 変数 | 意味 | 例（15分タイマー）|
|------|------|--------------------|
| `START_T` | 動画内タイマー開始秒 | 3857.04 (=1:04:17.04) |
| `DURATION` | タイマー長 | 900 (15分) |
| `END_T` | タイマー終了秒 = START_T + DURATION | 4757.04 |
| `STAGE1_END` | 64px → 96px切替 (5分後) | START_T + 300 = 4157.04 |
| `STAGE2_END` | 96px → 128px切替 (10分後) | START_T + 600 = 4457.04 |

### 確定コマンド (15分タイマー本番版)

```bash
SRC="$DAY2/mix・.mp4"
DST="$DAY2/mix_with_countdown.mp4"
F="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

START_T=3857.04   # タイマー開始秒
END_T=4757.04     # タイマー終了秒
STAGE1=4157.04    # 64→96切替
STAGE2=4457.04    # 96→128切替

# カウントダウン式: 終了時刻まで残り、それ以降は 0
X="if(lte(t\\,${END_T})\\,${END_T}-t\\,0)"
TXT='%{eif\:'"$X"'/60\:d}\:%{eif\:mod('"$X"'\,60)\:d\:2}.%{eif\:mod('"$X"'*100\,100)\:d\:2}'

ffmpeg -y -i "$SRC" \
  -vf "drawtext=fontfile=$F:text='$TXT':fontsize=64:fontcolor=white:bordercolor=0xFF69B4:borderw=3:x=w-text_w-20:y=20:enable='between(t,${START_T},${STAGE1})',\
       drawtext=fontfile=$F:text='$TXT':fontsize=96:fontcolor=white:bordercolor=0xFF69B4:borderw=3:x=w-text_w-20:y=20:enable='between(t,${STAGE1},${STAGE2})',\
       drawtext=fontfile=$F:text='$TXT':fontsize=128:fontcolor=white:bordercolor=0xFF69B4:borderw=3:x=w-text_w-20:y=20:enable='between(t,${STAGE2},${END_T})'" \
  -c:v h264_nvenc -preset p4 -rc vbr -cq 23 -b:v 6M -maxrate 8M -bufsize 12M \
  -c:a aac -b:a 192k "$DST"
```

### 短尺バリエーション (5分のみ・段階拡大なし)

```bash
ffmpeg -y -i "$SRC" \
  -vf "drawtext=fontfile=$F:text='$TXT':fontsize=64:fontcolor=white:bordercolor=0xFF69B4:borderw=3:x=w-text_w-20:y=20:enable='between(t,${START_T},${END_T})'" \
  -c:v h264_nvenc -preset p4 -rc vbr -cq 23 -b:v 6M -maxrate 8M -bufsize 12M \
  -c:a aac -b:a 192k "$DST"
```

## drawtext 内 escape 注意

- カンマ `,` → `\,`
- コロン `:` → `\:`
- 文字列内 `%{eif:...}` の中も再 escape 必要（上記 `TXT` 参照）
- bash 変数展開と ffmpeg expression のクォート競合に注意（シングル → ダブル切替で対応）

## アウトロ連結 (final 化)

```bash
echo "file 'mix_with_countdown.mp4'" > concat_mix.txt
echo "file 'outro_48k.mp4'" >> concat_mix.txt   # outro は 48kHz/h264_nvenc 統一必須
ffmpeg -y -f concat -safe 0 -i concat_mix.txt -c copy day2_3層オーディン_final.mp4
```

**注**: outro 元素材が 44.1kHz の場合、サンプリングレート不一致で `-c copy` が音切れを起こす。
事前に `-ar 48000 -c:a aac -b:a 192k` で `outro_48k.mp4` を作って統一せよ。

## 参考: Remotion 路線（テスト用・本番不採用）

カウントダウンの試行錯誤段階で Remotion を使ったが、レンダ速度・bash統合の都合で drawtext 方式が本番採用された。
Remotion 路線を再開する場合は以下を参照:

- `remotion-project/src/OdinCountdown.tsx` — Component (フェードイン+残り10秒赤脈動の演出付き)
- `remotion-project/src/Root.tsx` — `OdinCountdownTest` Composition
- `remotion-project/public/test_countdown_60s.mp4` — テスト素材

```bash
cd /home/murakami/multi-agent-shogun/remotion-project
npx remotion render OdinCountdownTest out/countdown.mp4 --codec h264 --crf 22 --concurrency 4
```

### 確定コマンド (30分タイマー本番版 — cmd_1500 正式式)

```bash
SRC="day2_3sou_men_only.mp4"
DST="day2_3sou_men_only_with_countdown_v2.mp4"
F="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

START_T=2892.22   # タイマー開始秒
END_T=4687.28     # タイマー終了秒（カウントダウン）
HOLD_END=4697.28  # 表示終了秒（128px段階のenable上限）
STAGE1=3792.22    # 40→64切替 (15分後)
STAGE2=4092.22    # 64→96切替 (20分後)
STAGE3=4392.22    # 96→128切替 (25分後)

# 正式カウントダウン式: DURATION-(t-START_T) = 1800-(t-2892.22)
# t=START_T → 30:00.00 / t=END_T → 0:04.94 / t>END_T → 4.94固定
X="if(lte(t\\,${END_T})\\,1800-(t-${START_T})\\,4.94)"
TXT='%{eif\:'"$X"'/60\:d\:2}\:%{eif\:mod('"$X"'\,60)\:d\:2}.%{eif\:mod('"$X"'*100\,100)\:d\:2}'

ffmpeg -y -i "$SRC" \
  -vf "drawtext=fontfile=$F:text='$TXT':fontsize=40:fontcolor=white:bordercolor=0xFF69B4:borderw=3:x=w-text_w-20:y=20:enable='between(t,${START_T},${STAGE1})',\
       drawtext=fontfile=$F:text='$TXT':fontsize=64:fontcolor=white:bordercolor=0xFF69B4:borderw=3:x=w-text_w-20:y=20:enable='between(t,${STAGE1},${STAGE2})',\
       drawtext=fontfile=$F:text='$TXT':fontsize=96:fontcolor=white:bordercolor=0xFF69B4:borderw=3:x=w-text_w-20:y=20:enable='between(t,${STAGE2},${STAGE3})',\
       drawtext=fontfile=$F:text='$TXT':fontsize=128:fontcolor=white:bordercolor=0xFF69B4:borderw=3:x=w-text_w-20:y=20:enable='between(t,${STAGE3},${HOLD_END})'" \
  -c:v h264_nvenc -preset p4 -rc vbr -cq 23 -b:v 6M -maxrate 8M -bufsize 12M \
  -c:a aac -b:a 192k "$DST"
```

**30分版と15分版の違い**:
- 40px段階追加（最初の15分間）・4段階カウントダウンの4段構成
- MM:SS.cc（2桁分表示）対応
- 128px段階は STAGE3~HOLD_END まで連続表示（式が4.94に収束→HOLD_ENDで消去）
- **cmd_1496 旧式の誤り注記**: 旧式 `X=if(lte(t,END_T),END_T-t,0)` は「4.94秒短い」バグあり（t=START_Tで 1795.06→29:55.06 になるべきが 29:55.06 を表示）。正式式は `X=if(lte(t,END_T),DURATION-(t-START_T),4.94)`

## 教訓

- **Remotion は試作向け・本番は ffmpeg drawtext** — 4視点 mix への重畳など bash パイプライン統合は drawtext が圧倒的に楽
- **5分毎拡大は殿の標準仕様** — 単一サイズで生成すると殿NG（4/20 10:11 指示）
- **タイマー終了後は残余値固定** — 負値表示は減点要素・カウントダウン式は `DURATION-(t-START_T)` で `END_T-t` は不可（cmd_1500教訓: END_T=START_T+DURATION-4.94 なので4.94秒短く計算される）
- **元素材が 44.1kHz だとconcat時に音切れ** — outro は事前に 48kHz 統一せよ（4/21 0:34 NG → 6:15 修正再アップ）

## 関連 cmd・素材

- 4/20 09:18 殿初回指示「カウントダウン表示のみ 残り4:59みたいな」
- 4/20 10:11 殿仕様確定「15分タイマースタート 5分毎に大きく」
- 4/20 15:03 殿本番指示「mix・.mp4 15分タイマーつけて 1:04:17.04~1:19:11.48」
- 4/20 15:30 殿仕上げ指示「アウトロつけて 非公開アップ 説明欄もかけ」
- 4/21 6:15 修正版再アップ（outro 音声統一・YouTube `GEyfSBKLBhA`）
- 4/27 cmd_1496 30分タイマー版（3層MEN視点・5段階drawtext）
- 4/27 cmd_1500 drawtext式バグ修正（正式式採用・旧NG版リネーム・4段構成に統合）
