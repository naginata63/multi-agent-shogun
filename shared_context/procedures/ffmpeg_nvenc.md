# ffmpeg NVENC Encoding Rule

ffmpeg で映像エンコードする際は **必ず GPU (NVENC) を使え**。CPU エンコード (libx264) は禁止。

| 用途 | 使うべきコーデック | 禁止 |
|------|-------------------|------|
| H.264エンコード | `-c:v h264_nvenc -preset p4` | `-c:v libx264` |
| コピー (無変換) | `-c:v copy` | — |

- マシン: RTX 4060 Ti 8GB 搭載・NVENC 常時利用可
- 推奨: `-c:v h264_nvenc -preset p4 -rc vbr -b:v 6000k -maxrate 8000k -bufsize 12000k`
- 音声: `-c:a aac -b:a 192k` で問題なし (CPU処理で十分速い)
- 注意: VP9 → h264 変換時は bitrate 劣化に注意 (デフォルト 2000kb/s で-44% 劣化)

## 教訓
- cmd_761: libx264 で 32分動画 webm→mp4 変換に 3時間半以上かかった (NVENC なら数分)
- cmd_1487: VP9 (4Mbps級) → h264 デフォルト で 2255kb/s に劣化・charlotte (4347kb/s) と同等以上を維持せよ

詳細手順: `shared_context/procedures/multi_view_sync.md` 鉄則6 (VP9→h264 bitrate 維持)
