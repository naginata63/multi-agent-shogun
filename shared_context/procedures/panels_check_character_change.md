# panels_check.html 話者変更機能追加手順（cmd_1349）

## 対象ファイル
- `projects/dozle_kirinuki/scripts/panels_check_gen.py`

## 作業前確認
1. `panels_check_gen.py` を Read し、各パネルの characters フィールドの現在の表示UIを確認する
2. 既存のドロップダウン実装（komawari / ref_images）パターンを参考にする

## 実装仕様

### 話者変更ドロップダウン
- 各パネルの右列（director_notes等があるエリア）に「話者変更」セクションを追加
- メンバーキー一覧: `dozle`, `bon`, `qnly`, `orafu`, `oo_men`, `nekooji`
- 1人パネル（characters に1件）: 話者1 のドロップダウン1つ
- 2人パネル（characters に2件）: 話者1・話者2 のドロップダウンをそれぞれ独立表示

### ref_images 自動連動
- ドロップダウン変更時、そのキャラの ref_images パスを自動更新
- パス置き換えルール: `assets/dozle_jp/character/selected/{旧キャラ}_{表情}.png` → `assets/dozle_jp/character/selected/{新キャラ}_{表情}.png`
- 表情コード（smile_r1 等）は保持したままキャラ名部分のみ差し替え
- 対応する表情ファイルが存在しない場合は `{新キャラ}_smile_r1_rgba.png` にフォールバック

### スマホ対応
- ドロップダウンの `min-height: 44px`、フォントサイズ `1rem` 以上
- タッチ操作しやすいよう十分な余白を確保

### buildJSON() の修正
- 話者変更ドロップダウンの値を characters 配列に正しく反映させる
- ref_images の更新内容も JSON に反映

## テスト手順
1. `python3 projects/dozle_kirinuki/scripts/panels_check_gen.py` を既存のpanels JSONで実行
2. HTML生成確認（構文エラーなし）
3. git commit & push

## 報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽2号、subtask_1349a完了。話者変更機能実装報告。" \
  report_completed ashigaru2
```
