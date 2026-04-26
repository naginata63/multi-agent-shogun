# panels_check_gen.py 作成手順（cmd_1310）

## 作業ディレクトリ
cd /home/murakami/multi-agent-shogun

## 成果物1: panels_check_gen.py
保存先: projects/dozle_kirinuki/scripts/panels_check_gen.py

### 使い方
```bash
python3 projects/dozle_kirinuki/scripts/panels_check_gen.py <panels_json_path>
```
→ 同ディレクトリに panels_check.html を出力

### HTMLレイアウト（1パネルあたり）
- ヘッダ: P番号・タイトル・shot_type・is_climax（赤バッジ）
- 3列レイアウト:
  [左] コマ割りプルダウン + サムネ（150px）
  [中] 表情（キャラ）プルダウン + サムネ（120px）、背景プルダウン + サムネ（150px）
  [右] director_notes・scene_desc・situation・lines・characters（テキストエリア編集可）
- フッタ: audio_start〜audio_end

### ページ上部（meta）
- title, scene, video_id, total_sec, panel_count
- common_rules全文・common_ref_images（サムネ）・character_positions（存在すれば）

### インタラクティブ機能（★重要）

① コマ割りプルダウン:
   - komawari_templates/ 配下の全テンプレ画像をスキャンして選択肢に
   - 変更するとコマ割りサムネがリアルタイム切り替わり

② 表情プルダウン（キャラごとに1つ）:
   - assets/dozle_jp/character/selected/ の全ファイルをスキャン
   - panelのcharactersに応じてキャラ名フィルタ（dozle→dozle_*のみ等）
   - 変更するとキャラRefサムネがリアルタイム切り替わり

③ 背景プルダウン:
   - panels JSONと同ディレクトリのref_*.pngをスキャンして選択肢に
   - 変更すると背景Refサムネがリアルタイム切り替わり

テキスト編集（全てテキストエリア）:
- director_notes・lines・scene_desc・situation

JSON出力（2ボタン）:
- 「JSONダウンロード」: 変更を反映したJSONをブラウザダウンロード（JS側で処理）
- 「JSON保存」: POST /api/save_panels_json でファイル書き戻し（サーバー側変更必要）

### 技術仕様
- 単一HTMLファイル（CSS+JS埋め込み、外部依存なし）
- 画像パス: os.path.relpath(abs_image_path, html_output_dir) で相対パス変換
- ref_images分類:
  - 'komawari_templates/' in path → コマ割り列
  - 'character/selected/' in path → キャラ列
  - それ以外 → 背景列
- is_climax=true → 赤バッジ「★CLIMAX」
- ファイル一覧はPythonでスキャンしてJS変数としてHTML内に埋め込む

## 成果物2: server.py に POST エンドポイント追加
ファイル: scripts/dashboard/server.py

追加するエンドポイント:
```
POST /api/save_panels_json
- body: {"path": "プロジェクトルートからの相対パス", "data": {...JSON...}}
- pathがプロジェクトディレクトリ外なら403エラー（セキュリティ）
- 成功したら {"status": "ok"} を返す
```

server.py変更後はgit commitすること。

## テスト手順
1. スクリプト実行:
```bash
python3 projects/dozle_kirinuki/scripts/panels_check_gen.py \
  "projects/dozle_kirinuki/work/20260407_体力と手持ちが共有の『地下世界』で全員合流するまで終われません！【マイクラ】/manga_qnly_agree/panels_qnly_agree.json"
```
2. ブラウザで panels_check.html にアクセス
3. 目視確認:
   - 全7パネル表示
   - プルダウン変更→サムネ切り替わり
   - テキストエリア編集可能
   - 「JSONダウンロード」でJSONがダウンロードされる
   - 「JSON保存」でファイルに書き戻せる（server.py再起動後）
4. ブラウザ確認必須（目視テストなしはNGとみなす）

## 報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽3号、subtask_1310a完了。panels_check_gen.py+server.py拡張完了。確認URL: {URL}" \
  report_completed ashigaru3
```
