# panels_railgun.json p6b 吹き出し禁止強化手順

## 概要
p6b_orafu_revive_and_dieパネルのdirector_notesに吹き出し禁止指示を強化追記する。
p6b以外のパネルは一切触らない。

## 対象ファイル
```
projects/dozle_kirinuki/work/20240113_いろんな時代の人になってエンドラ討伐！【マイクラ】/manga_railgun/panels_railgun.json
```

## Step 1: advisor()呼び出し（実装前）

## Step 2: 対象パネル確認
対象ファイルをReadし、`p6b_orafu_revive_and_die`パネルのdirector_notesを確認する。

## Step 3: 2箇所の禁止強化を編集

**追加1**: director_notesの冒頭（「添付画像の説明:」の直前）に以下を追加:
```
【最重要禁止】空の吹き出し・セリフなし吹き出し・テキストなし吹き出しを絶対に描くな。吹き出し形状（楕円・雲型・角丸四角等）そのものを一切画面に入れるな。このコマはセリフなしの無言シーンである。
```

**追加2**: 既存の禁止事項セクションの「セリフ・吹き出し・テキスト一切禁止」を以下に強化:
```
セリフ・吹き出し・テキスト一切禁止。空の吹き出し（中身なしの吹き出し形状）も絶対に描くな。画面内に吹き出しに見える形状が一切存在しないこと。
```

新規.py禁止。Editツールで直接JSON編集のみ。

## Step 4: JSONパース確認
```bash
python3 -c "import json; json.load(open('projects/dozle_kirinuki/work/20240113_いろんな時代の人になってエンドラ討伐！【マイクラ】/manga_railgun/panels_railgun.json')); print('OK')"
```

## Step 5: advisor()呼び出し（完了前）

## Step 6: git commit
```bash
git add "projects/dozle_kirinuki/work/20240113_いろんな時代の人になってエンドラ討伐！【マイクラ】/manga_railgun/panels_railgun.json"
git commit -m "fix(cmd_1377): panels_railgun p6b 空吹き出し禁止を最優先事項として強化追記"
```

## Step 7: 完了報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo "足軽2号、subtask_1377a完了。panels_railgun.json p6b吹き出し禁止強化・JSONパースOK・commit済み。" report_completed ashigaru2
```
