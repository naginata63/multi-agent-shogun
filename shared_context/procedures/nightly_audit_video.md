# nightly_audit 動画制作系 手順

## 対象スクリプト
- `projects/dozle_kirinuki/scripts/main.py`
- `projects/dozle_kirinuki/scripts/make_expression_shorts.py`
- `projects/dozle_kirinuki/scripts/vertical_convert.py`
- `projects/dozle_kirinuki/scripts/generate_outro.py`
- `projects/dozle_kirinuki/scripts/make_shorts_*.py` 系
- `remotion-project/` 配下

## 手順
1. `shared_context/qc_template.md` を参照してQC実施
2. 前回(20260421)指摘の regression 確認を最優先:
   - M1: `generate_outro.py` L204 libx264 → cmd_1429aで修正済み（regression-free確認）
   - M2: `main.py` L658 --diarize WhisperX抜け穴 → cmd_1429aで警告追加（regression-free確認）
   - M3: `/usr/bin/ffmpeg` 絶対パスハードコード多数（継続確認・未修正）
   - M4: Remotion命名ミスマッチ + DoZメンバー色未登録（継続確認・未修正）
3. 新規 CRITICAL/HIGH/MEDIUM/LOW を発見次第記録
4. テスト禁止・修正禁止・読んで報告のみ
5. 出力: `queue/reports/gunshi_report_nightly_audit_20260424_video.yaml`
6. 完了報告: `inbox_write karo`
