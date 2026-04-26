# subtask_1429a: 夜間監査動画制作系HIGH×4修正

対象ファイル:
- `projects/dozle_kirinuki/scripts/vocal_stt_pipeline.py`
- `projects/dozle_kirinuki/scripts/auto_fetch.py`
- `projects/dozle_kirinuki/scripts/pipeline.sh`
- `skills/video-pipeline/SKILL.md`
- `projects/dozle_kirinuki/scripts/generate_outro.py`

## 手順

1. `advisor()` — 実装前確認
2. 対象5ファイルを全てRead
3. **Item6**: `vocal_stt_pipeline.py` に `--disable-speaker-id` フラグ追加
   - argparse に `--disable-speaker-id` フラグ追加（action="store_true"）
   - フラグTrueの時はECAPA-TDNN識別ステップをスキップし、全話者ラベルをunknown
4. **Item7-a**: `pipeline.sh` を削除（呼び出し元ゼロ確認済み）
   - `git rm /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/scripts/pipeline.sh`
5. **Item7-b**: `auto_fetch.py` 冒頭に廃止警告追加
   - ファイル最初の実行コードの前に `print("[auto_fetch] WARNING: このスクリプトは廃止済み。STTはvocal_stt_pipeline.pyとstt_merge.pyを使用せよ。", flush=True)` を追加
6. **Item7-c**: `skills/video-pipeline/SKILL.md` Phase3-5記述を更新
   - WhisperX → AssemblyAI (vocal_stt_pipeline.py + stt_merge.py) に置換
   - auto_fetch.pyへの参照を `(Deprecated)` 表記に変更
7. **Item8**: `vocal_stt_pipeline.py` L44 SPEAKER_ID_THRESHOLD を環境変数化
   - `SPEAKER_ID_THRESHOLD = 0.25` を `SPEAKER_ID_THRESHOLD = float(os.environ.get("ECAPA_THRESHOLD", "0.25"))` に変更
   - `import os` が既存になければ追加
8. **Item9**: `generate_outro.py` libx264中間処理を除去
   - L202-208付近: `clip.write_videofile(tmp_path, codec="libx264", ...)` のmoviepy書き出しを削除
   - tmp_pathへの書き出しをffmpeg直接パイプに置換（または、moviepyでフレーム取得→rawパイプでffmpegに渡す）
   - 最終出力のffmpegコマンド（L209-215: h264_nvenc）はそのまま維持
   - 変更後の出力確認: libx264が一切使われないこと
9. `advisor()` — 完了前確認
10. `git add /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/scripts/ /home/murakami/multi-agent-shogun/skills/`
11. `git commit -m "fix(cmd_1429a): 夜間監査動画制作HIGH×4修正 (--disable-speaker-id/pipeline.sh削除/ECAPA_THRESHOLD env化/generate_outro nvenc直接)"`
12. 完了報告: `bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo "足軽1号、subtask_1429a完了。Item6/7/8/9修正・commit済み。" report_completed ashigaru1`

## 注意事項

- **git push禁止**: 家老がcmd完了時に実施
- **git add .禁止**: `git add <dir>` のみ
- `pipeline.sh` の呼び出し元はゼロ（grep確認済み）。安全に削除可
- `generate_outro.py` でmoviepy → ffmpeg 2段階になっているのはlibx264中間が問題。moviepy書き出し箇所を丸ごとffmpegコマンドに置き換えるか、moviepy→pipe→ffmpegにして中間ファイルを作らない設計に変更
- ECAPA_THRESHOLD: デフォルト0.25を維持しつつenv変数で上書き可能
- advisor()はstep1(実装前)とstep9(完了前)の2回必須
