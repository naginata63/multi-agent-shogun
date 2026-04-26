# 夜間監査修正: 動画制作パイプライン（cmd_1415a）

## 対象
projects/dozle_kirinuki/scripts/

## 参照レポート
queue/reports/gunshi_report_nightly_audit_20260417_video.yaml

## 修正内容

### CRITICAL: main.py L1156 logger未定義
- `logger.warning(...)` → `print(f"[main] WARNING: ...")` に置換
- `import logging` / `logger = logging.getLogger(...)` は追加しない（remedy選択肢A）
- 置換後: `grep 'logger\.' projects/dozle_kirinuki/scripts/main.py` で未定義参照残存なし確認

### HIGH: vertical_convert.py L174 /tmp使用
- `tempfile.mkstemp()` の出力先を `/tmp` → `work_dir` 配下に変更
- `work_dir` は既存変数または関数引数から取得

## テスト手順
```bash
cd /home/murakami/multi-agent-shogun
python3 -c "import ast; ast.parse(open('projects/dozle_kirinuki/scripts/main.py').read())"
python3 -c "import ast; ast.parse(open('projects/dozle_kirinuki/scripts/vertical_convert.py').read())"
grep -n 'logger\.' projects/dozle_kirinuki/scripts/main.py  # 0件であること
```

## Git
```bash
git add projects/dozle_kirinuki/scripts/main.py projects/dozle_kirinuki/scripts/vertical_convert.py
git commit -m "fix(cmd_1415a): 動画パイプラインlogger未定義+tmp使用修正"
```

## advisor()必須
実装前と完了前の2回呼ぶこと。
