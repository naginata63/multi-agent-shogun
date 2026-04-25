# master/telop 二段生成手順

テロップ修正コストを数時間→数十分に短縮するため、動画生成を二段階に分ける方式。
4視点合成の重い処理は一度だけ実行し、テロップは後付け1passで重ねる。

## 目的

- テロップ修正発生時、4視点合成(sync・concat・transition)を再実行しなくて済むようにする
- master.mp4 (テロップなし) を一度だけ作り、テロップは drawtext 1passで後加工
- 修正コスト: 数時間(4視点再合成) → 数十分(drawtext再実行のみ)

## master.mp4 生成手順

4視点シーン切替MIXの標準手順に従い、**テロップなし**で出力する。

```bash
# 1. 各seg独立MIX (テロップdrawtextフィルタを含めない)
ffmpeg -i seg1_synced.mp4 ... -c:v h264_nvenc -preset p4 seg1_master.mp4
ffmpeg -i seg8_synced.mp4 ... -c:v h264_nvenc -preset p4 seg8_master.mp4

# 2. concat結合
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy master.mp4
```

**注意**: drawtextフィルタはこの段階では使わない。テロップは次段階で後付けする。

## with_telop.mp4 後加工手順

master.mp4 に drawtext 1passでテロップを重ねる。

```bash
# 過去動画と同一のdrawtextパラメータを使用すること (フォーマット参照ルール)
ffmpeg -i master.mp4 \
  -vf "drawtext=fontfile=/path/to/font.ttf:text='<ボス名>(<戦闘番号>)':fontsize=36:fontcolor=white:x=w-tw-20:y=20:box=1:boxcolor=black@0.5" \
  -c:v h264_nvenc -preset p4 -c:a copy with_telop.mp4
```

**エンコード**: h264_nvenc (GPU) のみ。libx264 (CPU) は禁止 (cmd_761教訓)。

## テロップミス時の取り返し手順

1. master.mp4 が存在することを確認
2. drawtextパラメータを修正 (テロップ文言・位置・フォント等)
3. master.mp4 から再 drawtext:
   ```bash
   ffmpeg -i master.mp4 \
     -vf "drawtext=...修正後パラメータ..." \
     -c:v h264_nvenc -preset p4 -c:a copy with_telop_v2.mp4
   ```
4. with_telop_v2.mp4 を確認 → OKならアップロード差替

**禁止**: テロップ修正のために4視点合成を再実行すること。

## 過去テロップフォーマット参照ルール

新規動画作成時、必ず最新のアップ済 with_telop 動画から drawtext パラメータを抽出し統一する。

```bash
# 過去動画のテロップ情報を確認
ffprobe -v error -show_entries frame=pkt_pts_time -select_streams v with_telop_old.mp4 2>&1 | head -5

# サンプルフレーム抽出で目視比較
ffmpeg -ss 5 -i with_telop_old.mp4 -frames:v 1 -q:v 2 sample_old.png
ffmpeg -ss 5 -i with_telop_new.mp4 -frames:v 1 -q:v 2 sample_new.png
```

参照すべき過去資産:
- Day5: `projects/dozle_kirinuki/work/20260415_*/multi/day5_zephyrus_with_telop.mp4`
- その他: 同ディレクトリの `*_with_telop.mp4`

## 元素材チェック

元動画 (YouTube DL等) に既存テロップ・ロゴが焼き込まれていないか確認必須。

```bash
# 複数箇所のフレームを抽出して目視確認
for t in 5 30 60 120 300; do
  ffmpeg -ss $t -i input.mp4 -frames:v 1 -q:v 2 "check_${t}s.png"
done
```

既存テロップが入っている場合は:
- 元素材の選定からやり直し (テロップなしの素材を探す)
- 既存テロップ上に重ね描きは禁止 (cmd_1478で発生した問題の再発防止)

## 保管ルール

- master.mp4 は最低 cmd完了後30日間保管 (テロップ修正可能性のため)
- 保管先: 成果物と同階層 (例: `work/cmd_XXXX/output/master.mp4`)
- master.mp4 の削除は殿の許可が必要
- with_telop.mp4 は YouTube非公開アップ後に削除可 (masterがあるため再生成可能)

## ファイル命名規則

| ファイル | 命名 | 用途 |
|---------|------|------|
| master.mp4 | `{day}_master.mp4` | テロップなし完成品 (永続保管) |
| with_telop.mp4 | `{day}_with_telop.mp4` | テロップ付き (アップロード用) |
| with_telop_v2.mp4 | `{day}_with_telop_v2.mp4` | テロップ修正版 |
