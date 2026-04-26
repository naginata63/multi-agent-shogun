# 夜間監査修正: YouTube/外部連携+STT（cmd_1415c）

## 対象
projects/dozle_kirinuki/scripts/youtube_uploader.py, scripts/generate_dashboard.py,
projects/note_mcp_server/ (50ファイル), note_visual_qc.py, note-edit.js,
projects/dozle_kirinuki/scripts/compare_speaker_srt.py + 他3ファイル

## 参照レポート
queue/reports/gunshi_report_nightly_audit_20260419_youtube_api.yaml
queue/reports/gunshi_report_nightly_audit_20260416_stt.yaml

## 修正内容

### H1: youtube_uploader.py publishAt+privacy違反
- publish_at指定時: privacyStatus='private'強制 + warning出力
- argparse: --privacy と --publish-at を mutually_exclusive_group に
- または publish_at 指定時に privacy='private' を強制（warning付き）

### H2: generate_dashboard.py SCOPES不一致
- _YOUTUBE_SCOPES に `youtube.force-ssl` を追加
- youtube_uploader.py と analytics の SCOPES と完全一致させる

### H3: note_mcp_server プロファイル二重体制
- note-profile と note-cli-profile の二重体制を統一
- 50ファイル中50を同一プロファイル参照に置換
- どちらを使うか: projects/note_mcp_server/ 内を確認し、正しい方に統一

### H4: note_visual_qc.py Part.from_bytes
- Part.from_bytes() → GCS URI方式（CLAUDE.md鉄則）
- 参考実装: cmd_1333c で generate_illustration.py を修正した際のアプローチ

### H5: note-edit.js 空文字ログイン
- パスワード/メールが空文字の場合に早期return
- アカウントロックリスク回避

### STT: MEMBERSハードコード除去
- 対象: compare_speaker_srt.py + 他3ファイル（speaker_id_srt_based.py等）
- `MEMBERS = ["dozle","bon","qnly","orafu","oo_men"]` → `load_members_from_yaml()` に置換
- 既存実装: projects/dozle_kirinuki/scripts/speaker_id_srt_based.py に load_members_from_yaml() が既にあるか確認
- ない場合は新規実装: projects/dozle_kirinuki/context/member_profiles.yaml から読み込む関数

## テスト手順
```bash
# 構文確認
python3 -c "import ast; ast.parse(open('projects/dozle_kirinuki/scripts/youtube_uploader.py').read())"
python3 -c "import ast; ast.parse(open('scripts/generate_dashboard.py').read())"
python3 -c "import ast; ast.parse(open('projects/dozle_kirinuki/scripts/compare_speaker_srt.py').read())"

# MEMBERSハードコード残存確認
grep -rn 'MEMBERS\s*=\s*\[' projects/dozle_kirinuki/scripts/  # 0件であること

# SCOPES確認
grep 'force-ssl' scripts/generate_dashboard.py  # 存在すること

# youtube_uploader dry-run確認
cd /home/murakami/multi-agent-shogun && source ~/.bashrc
python3 projects/dozle_kirinuki/scripts/youtube_uploader.py --help  # --dry-run オプション確認
```

## Git
```bash
git add projects/dozle_kirinuki/scripts/youtube_uploader.py scripts/generate_dashboard.py projects/note_mcp_server/ projects/dozle_kirinuki/scripts/compare_speaker_srt.py
git commit -m "fix(cmd_1415c): YouTube API+STT+Note HIGH×6修正"
```

## safety: batch_modify
このタスクは50ファイル以上を一括修正するため、instructions/git_safety.mdのプロトコルに従うこと。

## advisor()必須
実装前と完了前の2回呼ぶこと。
