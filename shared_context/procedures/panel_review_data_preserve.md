# panel_review.html データ保全バグ修正手順（cmd_1352）

## 問題
「JSON生成」ボタンが rows から新規 JSON を作り直すため、
元の panels JSON（Gemini生成の director_notes・scene_desc・ref_images 等）が上書きされて消える。

## 対象ファイル
- `projects/dozle_kirinuki/scripts/panel_review_gen.py`

## 修正方針: 「新規JSON生成」→「既存JSON編集」モードに変える

### Step1: panel_review_gen.py を Read して現状把握
- `panelsToRows()` と JSON生成ボタンのJS実装を確認
- 現在どこでパネルデータを捨てているか特定

### Step2: パネルデータをメモリ保持する仕組みに変更

#### JS側の変更
1. panels JSON 読み込み時、全パネルオブジェクト（director_notes 等含む）を `PANELS_DATA` 配列として保持
2. `panelsToRows()` は rows 表示用に変換するだけ。元の `PANELS_DATA` は破棄しない
3. rows と PANELS_DATA の対応を `row.panel_index` で管理（並び替え時にも追従）

#### 保存時の処理（「JSON保存」ボタン）
```
旧: rows から新規パネルを組み立てて保存
新: PANELS_DATA[panel_index] を更新（話者・セリフのみ上書き）して保存
```

具体的には:
- `characters` → rows の speaker から更新
- `lines` → rows の text から更新（配列の場合は `[text]` に置き換え）
- `ref_images` → 話者変更ロジックで更新（既存の流用）
- `director_notes`, `scene_desc`, `shot_type`, `start_sec` 等 → **変更しない**

#### 行操作時の処理
- **行追加**: 新規パネルオブジェクトを PANELS_DATA に追加（`director_notes: ""` 等の空値）
- **行削除**: PANELS_DATA から該当インデックスを削除
- **行並び替え**: PANELS_DATA の順序を rows の順序に追従して並び替え

### Step3: _raw.json形式（rows配列のみ）の場合
- `rows` フィールドのみの場合は従来通り新規パネル生成でOK（元々 director_notes がないため）
- panels JSON形式（`panels` フィールドあり）のみ上記の保持モードを適用

## テスト
1. `panel_review_gen.py` を既存 panels JSON で実行 → HTML生成確認
2. HTML内に `PANELS_DATA` の保持ロジックが含まれること確認: `grep -c 'PANELS_DATA' panel_review.html`
3. git commit & push

## 報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽1号、subtask_1352a完了。panel_review.htmlデータ保全バグ修正報告。" \
  report_completed ashigaru1
```
