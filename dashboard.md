# 📊 戦況報告
最終更新: 2026-04-12 16:26

## 💰 DingTalk音声QC（9万円案件）
🟢 稼働中 | 処理済み: **228件** / 10,000件 | 報酬見込み: **¥2,052**
| 指標 | 値 |
|------|-----|
| 確認済み | 220件 |
| スキップ（類似度低） | 7件 |
| エラー（無効音声） | 1件 |
| 平均類似度 | 90.4% |
| 最低類似度 | 32.9% |
| 平均音量 | -23.3 dB |

## 📱 ntfy通知
トピック: `shogun-962f817f20fadb36`

## 🚨 要対応 - 殿のご判断をお待ちしております



### 🔴 cmd_1326 Vision分析完了・殿確認要（判定不能58件）
- **結果**: 無音区間118件中
  - PC見ている: **34件（113.8秒）** → カット対象
  - カメラ目線: 23件 → 残す
  - その他: 3件
  - ⚠️ **判定不能: 58件**（バッチ2のJSONパース失敗）→ 118件中半数が未判定
- `projects/crowdworks_video_edit/work/pc_looking_analysis.json`
- **→ 判定不能58件を再実行するか（バッチ2のみ）、34件カット対象のみで進めるか、殿のご判断を**

### 🔴 cmd_1327 cut_edited_v5.mp4完成・殿確認待ち
- **軽量版（480p）** duration: **31.6s** / 4.5MB
- LLMリテイク判定: 採用61件 + 英語リピート6件 = 67件採用
- PC視線カット: pc74件 + other3件 = **77件カット**
- カメラ目線保持: 41件
- ファイル: `projects/crowdworks_video_edit/work/cut_edited_v5.mp4`
- **→ 殿ご確認ください。OKならPhase2（本番1080p）へ**

### 🔴 cmd_1320 Phase2完了・殿確認待ち
- Phase1 ✅ 殿OK済み（採用54+英語リピート8で進行。seg59/63/64は採用扱い）
- Phase2 ✅ **cut_edited_v4.mp4 完成** duration:352.7s / 660MB / loudnorm 2pass + h264_nvenc
- **→ 殿OK後にPhase3（テロップ+Bロール+YouTube限定公開）へ**

### ⛔ cmd_1322 P2〜P7生成中止（殿指示）
- P1 殿OK済み ✅
- P2〜P7: 殿指示により中止。再開しない。

### 🔬 cmd_1318 Geminiデバッグ結果（殿ご確認）
- **ギャラリー**: http://192.168.2.7:8770/work/20260407_%E4%BD%93%E5%8A%9B%E3%81%A8%E6%89%8B%E6%8C%81%E3%81%A1%E3%81%8C%E5%85%B1%E6%9C%89%E3%81%AE%E3%80%8E%E5%9C%B0%E4%B8%8B%E4%B8%96%E7%95%8C%E3%80%8F%E3%81%A7%E5%85%A8%E5%93%A1%E5%90%88%E6%B5%81%E3%81%99%E3%82%8B%E3%81%BE%E3%81%A7%E7%B5%82%E3%82%8F%E3%82%8C%E3%81%BE%E3%81%9B%E3%82%93%EF%BC%81%E3%83%9E%E3%82%A4%E3%82%AF%E3%83%A9/manga_qnly_agree/output/gallery_p1.html
- **モデル**: gemini-3.1-flash-image-preview ✅
- **finish_reason**: STOP ✅（正常完了）
- **⚠️ 出力解像度**: **768×1376px / 1392KB** ← 品質しょぼい原因の可能性。以前は別の解像度？
- **髪色修正**: green hair認識済み ✅（「green hair, glasses, vest, waist scarf」）
- → 殿OKなら残りP2〜P7へ。解像度が問題なら解像度指定方法を調査して次cmdへ

### 📋 CrowdWorks動画カット確認待ち
- **cut_edited_v3_fixed.mp4**: `projects/crowdworks_video_edit/work/cut_edited_v3_fixed.mp4`（loudnorm 2pass -16dBFS正規化済み / h264 cq16 / 380s 569MB）
  - ✅ 殿OKなら → テロップ(telop.ass)+Bロール合成+YouTube限定公開アップ開始
  - ❌ NGなら → 再修正指示

### 📋 漫画レビュー待ち
- **争わないでパネルv2（6枚）**: `manga_odai_arasowanaide/` P1〜P6 768x1376px 殿レビュー待ち
- **お待たせしましたv2（7枚）**: `manga_odai_03_omataseshimashita_v2/` P1〜P7 殿レビュー待ち（v1も保持中）
- **qnly_death v4**: https://youtu.be/Y7tm26PLPb0（P3リテイク済み）
- **お題漫画「あちらのお客様からです」v2**: https://www.youtube.com/watch?v=gSEJIglR_ME（音声同期版47秒・殿レビュー待ち）
- **お題漫画「私のために争わないで」v2**: http://192.168.2.7:8785/gallery_cmd1270.html（ゴーグル目装着+NGワード修正版・殿レビュー待ち）
- **bon_trick 動画v1**: https://www.youtube.com/watch?v=CPpwjO2BuyA（72秒・7パネル・殿レビュー待ち）
- **原始人ドズル漫画「仲直りの歌」v7**: http://192.168.2.7:8770/work/gallery_cmd1285.html（P7再生成済み・吹き出しあり・セリフ正常・ぼん絶望ポーズ・P6も補完済み・全7パネル・殿レビュー待ち）
- **tono_edit3.mp4 YouTube非公開アップ済み**: https://www.youtube.com/watch?v=n9I1xCOWCKo（殿レビュー待ち）
- **英語学習動画 自動カット+テロップ+Bロール（最終版）**: https://www.youtube.com/watch?v=XXVzw0tBBi4（非公開・殿レビュー待ち）
- **英語学習動画 自動カット編集テスト（Chirp3+LLM版）**: https://www.youtube.com/watch?v=2f4hLWamREc（非公開・殿レビュー待ち）
- **おんりー合流漫画ショート（縦型）YouTube非公開アップ済み**: https://www.youtube.com/watch?v=0SBiIU74yvc（1078x1918 h264_nvenc・殿レビュー待ち）
- **ピンク羊総集編動画**: https://www.youtube.com/watch?v=bqSQQcN1izM（7:46・25件・殿レビュー待ち）
- **ピンク羊完全版（25件・STTカット再設計）**: https://www.youtube.com/watch?v=_FsFx67be24（13:36・全25件・xfadeトランジション・clip_22復活・殿レビュー待ち）
- **ピンク羊拡張版（前5秒・後10秒）**: https://www.youtube.com/watch?v=IQ5nRJVrsmg（13:17・24件・xfadeトランジション・旧版）
- **原始人ドズル立ち絵v3**: refs/ref_dozle_genshijin_illust.png（1202KB・843x1264px・ワンショルダー豹柄+金髪ポニーテール・殿レビュー待ち）
- **ぼん平安貴族立ち絵v1**: refs/ref_bon_heian_illust.png（1635KB・843x1264px・smug_r2ベース紫束帯版・殿レビュー待ち）

### 📋 総集編 — 殿の選定待ち
- 🐑 ピンク羊25件(15+10): https://youtu.be/obNdc44lqc0 追加候補: `work/cmd_1268_pink_sheep_additional.md` ⚠️合計475秒≈7分55秒（目標8分まで5秒差）
- 🎤 MEN迷言18件: https://youtu.be/MMh3Djlf8dE
- 🧊 おらふ名場面16件: https://youtu.be/LV4pY2O1tXs

### ✅ 夜間監査 cmd_1333 — 全CRITICAL/HIGH修正完了（2026-04-12）
- **CRITICAL/HIGH 10件を3並列で修正完了** (subtask_1333a/b/c)
- **1333a (ashigaru1)**: OAuth 4スコープ統一・privacy引数反映・delete確認追加・CLIパスshutil.which化
- **1333b (ashigaru2)**: LLMスキーマバリデ追加・clip_timestamps_raw境界チェック・h264_nvencハードコード除去
- **1333c (ashigaru3)**: IDLE_FLAG_DIR→queue/.flags/・awk→mawk化・generate_illustration.py Part.from_bytesフォールバック除去
- ⚠️ **未着手(MEDIUM)**: note_visual_qc.py Part.from_bytes / Playwrightプロファイル不一致 / download.sh yt-dlp不整合等（スコープ外）

### 🔧 夜間監査 2026-04-09 — STTパイプライン修正状況
- ~~CRITICAL/HIGH3件~~ → ✅ 全修正済み（subtask_1272a + 0ef982a3）
- MEDIUM: --gemini廃止コード残存 他 → 優先度低・未着手
- ⚠️ **xlDFsyNm_eE STT再実行の要否**: subtask_1272aでCRITICAL修正後に全尺完走済み（00:35:45・6名実名確認）。再実行不要であれば作業継続。再実行が必要な場合はご指示を。

### 🔧 技術的残項目（優先度低）
- 漫画フォント30書体ギャラリー未選定: http://100.66.15.93:8783/work/font_comparison/
- **⚠️ dozle_kirinukiサブモジュール push不可**: d4baa9c5でgcloud SDK（194MB）がコミット済み→GitHub 100MB制限でreject。scripts/の変更はローカルのみ保存中。git-lfs移行 or 履歴書換が必要

## 🚨 要対応

### 🚨 cmd_1347: panel_candidate_prompt.txt 未提供
- generate_panel_candidates.py実装に必要な「構成表生成プロンプト」が未提供
- **殿の対応**: 殿がGemini AI Studioで使っているプロンプト全文を `projects/dozle_kirinuki/context/panel_candidate_prompt.txt` に保存いただくか、将軍経由でお伝えください
- （スクリプト本体の実装は足軽1号が並行して進行中）

### お題4「早く寝なさい」P7 武器混入
- **cmd_1346**: P7にナイフ状の武器が混入。P7のみ再生成が推奨。
- **殿の判断**: P7再生成するか否かをご指示ください。OKなら家老が足軽3号に再生成指示。

### server.py再起動
- **cmd_1344追加: `/api/list_panels_json`（JSON選択UI）も再起動後に有効** commit 223efc6
- panels_check.html の全機能が再起動後に有効: `/api/save_panels_json`・`/api/load_panels_json`・`/api/list_panels_json`・`POST /api/suggest_director_notes`
- 実行コマンド: `kill $(pgrep -f "server.py") && nohup python3 /home/murakami/multi-agent-shogun/scripts/dashboard/server.py >> /tmp/dashboard.log 2>&1 &`

## 🔄 進行中（実行中のタスク）

| cmd | 内容 | 状態 |
|-----|------|------|
| cmd_1347 | generate_panel_candidates.py実装中（動画→panels JSON全自動化）⚠️プロンプトファイル未提供 | 足軽1実行中 |
| cmd_1346 | お題4「早く寝なさい」v1全7枚生成完了（MENゴーグルOK・⚠️P7に武器混入）✅ 殿判断待ち |
| cmd_1345 | お待たせしましたv5完成（P1/P6新規生成+P2-P5/P7はv4コピー）✅ 殿レビュー待ち |
| cmd_1344 | panels_check.html JSON選択UI追加完了（/api/list_panels_json+ドロップダウン）✅ ⚠️サーバー再起動必要 |
| cmd_1343 | お待たせしましたパネルv4全7枚生成完了（MENゴーグル全P確認・P7パスタ確認）✅ 殿レビュー待ち |
| cmd_1342 | お待たせしましたパネルv3全7枚生成完了（7/7・ガチャ1回・372s）✅ 殿レビュー待ち |
| cmd_1334 | FINAL_COMPOSED.mp4 破損（moov atom not found）⛔ 殿指示により中止 |
| cmd_1327 | cut_edited_v5.mp4完成（480p軽量版）31.6s/4.5MB → **殿確認待ち** ⛔ |
| cmd_1320 Phase2 | cut_edited_v4.mp4完成 352.7s/660MB → **殿確認待ち** ⛔ |
| cmd_1305d | CrowdWorks 最終合成+YouTube限定公開アップ | ⛔ 殿確認後に開始 |

## ✅ 本日の完了
| cmd | 内容 |
|-----|------|
| cmd_1341 | お待たせしましたパネルv2全7枚生成完了（7/7・ガチャ2回・P2 499リトライ）→ manga_odai_03_omataseshimashita_v2/ 殿レビュー待ち |
| cmd_1340 | お待たせしましたパネルv1全7枚生成完了（7/7・ガチャ1回）→ manga_odai_03_omataseshimashita/ |
| cmd_1339 | KOMAWARI_DESC全35エントリ修正完了（S2/T1-T6/D4-D8等）commit 1ce0aeb7 |
| cmd_1338 | panels_check.html shot_type表示・編集・保存先連動バグ修正完了 commit 49e87d27 |
| cmd_1337 | 争わないでパネルv2全6枚生成完了（6/6成功・768x1376px）殿レビュー待ち |
| cmd_1336 | panels_check.html JSON読み込み機能追加完了（パス入力欄+/api/load_panels_json動的再描画）|
| cmd_1335 | panels_check.html生成完了（45KB・6パネル）http://192.168.2.7:8770/work/output/manga_odai/panels_check.html |
| cmd_1333 | 夜間監査CRITICAL/HIGH 10件修正完了（3並列 1333a/b/c）|
| cmd_1332 | FINAL_COMPOSED.mp4 YouTube非公開アップ完了 → https://www.youtube.com/watch?v=XXVzw0tBBi4 |
| cmd_1331 | 英語学習動画 自動カット編集テスト YouTube非公開アップ完了 → https://www.youtube.com/watch?v=2f4hLWamREc |
| cmd_1330 | tono_edit.mkv 縦型クロップ+YouTube非公開アップ完了 → https://www.youtube.com/watch?v=0SBiIU74yvc |
| cmd_1329 | AI分析最新化完了 analysis_history:2026-04-11（04-06〜04-11の6日分追加・計20エントリー）|
| cmd_1328 | analytics data.json再構築完了 generated_at:2026-04-11 / dates:03-01〜04-08（39件）|
| cmd_1325 | 参考動画Vision分析完了 reference_vision_analysis.md(70KB/11チャンク) |
| cmd_1305a | CrowdWorks カット編集完了 cut_edited.mp4(529.7s/647MB) |
| cmd_1305b | CrowdWorks テロップASS生成完了 telop.ass(48件) |
| cmd_1305c | CrowdWorks Bロール画像生成完了 5枚(broll_001〜005.png) |
| cmd_1286 | ピンク羊総集編25件連結+YouTube非公開アップ完了（7:46・466s）→ https://www.youtube.com/watch?v=bqSQQcN1izM |
| cmd_1304 | ピンク羊完全版25件完了（13:36・clip_22復活）→ https://www.youtube.com/watch?v=_FsFx67be24 |
| cmd_1303 | ピンク羊25件STTカット再設計完了（24件変更・clip_22元範囲維持・clips_redesigned.json） |
| cmd_1293 | ピンク羊サムネ5人版完了（thumbnail_energetic_1.png既存・完成確認） |
| cmd_1302 | ピンク羊拡張版完了（13:17・24件・xfade・⚠️clip_22破損除外）→ https://www.youtube.com/watch?v=IQ5nRJVrsmg |
| cmd_1301 | 原始人漫画P1/P6/P7再生成完了（吹き出し禁止強化版・v5） |
| cmd_1300 | 原始人漫画P1/P6再生成完了（ナレーション枠+縦書き筆文字版・v4） |
| cmd_1299 | 原始人漫画7パネル再生成完了（ドズル豹柄ワンショルダー+ぼん紫束帯・v3） |
| cmd_1298 | 原始人ドズル立ち絵v3生成完了（ワンショルダー豹柄+金髪ポニーテール・1202KB） |
| cmd_1317 | fix_panes.sh + shutsujin_departure.sh に /advisor opus 自動送信追加完了（git 01c3c48）|
| cmd_1314 | panels_check_gen.py 複数表情プルダウン実装完了（同一キャラ複数ref→上段/下段個別選択）git 3e852da2 |
| cmd_1312 | panels_check_gen.py dozleプルダウンバグ修正完了（絶対パス含むdirname誤マッチ修正）git commit済み |
| cmd_1311 | panels_check_gen.py修正完了（絶対パス+director_notes追従・git 8f5b4e37）⚠️push不可（gcloud SDK 194MB問題） |
| cmd_1310 | panels_check_gen.py インタラクティブエディター完成（git 34c13c1） |
| cmd_1320 Phase2 | ⚠️ libx264違反→緊急停止指示済み。h264_nvencに切り替えて再実行中 | 足軽1対処中 |
| cmd_1322d | ⛔ P2〜P7生成中止（殿指示・再開なし） | 足軽2停止 |
| cmd_1322a | P1初回生成完了→ 殿JSON更新のため再生成へ |
| cmd_1324 | generate_manga_short.py GCS URI全面統一+デフォルト軽量モード完了 git 93427ca3 ✅ | 足軽3完了 |
| cmd_1321 | LLMプロンプト提案機能実装完了（POST /api/suggest_director_notes）server.py再起動待ち ✅ |
| cmd_1319 | panels_check.html fetch方式化完了（GET /api/load_panels_json追加）git commit済み ✅ |
| cmd_1318 | Geminiデバッグ完了 モデル正常/finish_reason=STOP ⚠️解像度768x1376px（品質原因か）| 完了 ✅ |
| cmd_1316a | おんりー合流漫画P1生成完了（殿確定JSON版）→ cmd_1318でデバッグ調査中 |
| cmd_1313a | CrowdWorksカット編集やり直し完了 cut_edited_v3.mp4（381.5s/462MB）品質修正中 |
| cmd_1309a | おんりー合流漫画P1生成完了 → 殿確認待ち（P2〜P7は確認後） |
| cmd_1308 | tono_edit3.mp4 YouTube非公開アップ完了 → https://www.youtube.com/watch?v=n9I1xCOWCKo |
| cmd_1307 | 原始人漫画P7再生成完了（吹き出しあり・セリフ正常・ぼん絶望ポーズ・director_notes修復済み） |
| cmd_1306 | 原始人漫画P7再生成（吹き出しなし版・将軍ミスのため cmd_1307 で是正済み） |
| cmd_1294/1297 | 原始人ドズル漫画7パネル再生成完了（全7枚・P6ドズル追加版） |
| cmd_1296 | ぼん平安貴族立ち絵v1生成完了（smug_r2ベース紫束帯・1635KB・843x1264px） |
| cmd_1295 | 原始人ドズル立ち絵v2生成完了（smile_r2ベース腰巻き変換・1400KB・843x1264px） |
| cmd_1288 | 原始人ドズル立ち絵リファレンス生成完了（ref_dozle_genshijin_illust.png・1049KB） |
| cmd_1287 | ピンク羊サムネ3パターン生成完了（pink_sheep_clips/thumbnail_energetic*.png） |
| cmd_1285 | 原始人ドズル漫画「仲直りの歌」7パネル生成完了 → http://192.168.2.7:8785/gallery_cmd1285.html |
| cmd_1284 | bon_trick動画化+YouTube非公開アップ完了（72秒・7パネル）→ https://www.youtube.com/watch?v=CPpwjO2BuyA |
| cmd_1283 | bon_trick P3/P5再生成完了（smile_r2適用・MEN吹き出し修正・R4版） |
| cmd_1282 | お題1 P6再生成完了（NGワード「かしこまりました」誤描画修正・1枚） |
| cmd_1281 | MENゴーグル目装着版4枚v9方式生成完了（成功4/0・commits: 417992c4+afadcdeb） |
| cmd_1279 | MENゴーグル目装着版ref_image生成完了（842x1264px・1発成功） |
| cmd_1278 | ショート全リスト4月分作成完了（13件・shorts_full_list_202604.md） |
| cmd_1277 | speaker_id_srt_based.py HIGH修正完了（MEMBERSハードコード→動的ロード） |
| cmd_1276 | お題1「あちらのお客様」動画やり直し完了（音声同期版47秒） |
| cmd_1275 | bon_trick P3/P4/P5再生成完了（R3版） |
| cmd_1274 | お題2「私のために争わないで」6枚再生成完了（ゴーグル目装着+NGワード修正版） |
| cmd_1273 | お題1「あちらのお客様からです」初回動画（40秒・旧版） |
| cmd_1272 | xlDFsyNm_eE STT全尺やり直し完了（PROJECT_DIRバグ修正込み・00:35:45） |
| cmd_1271 | srt_hotspot.py新規作成 + integrate_replay_hotspot.py Layer4統合完了 |
| cmd_1270 | お題2「私のために争わないで」6枚新規生成完了 |
| cmd_1269 | 夜間監査修正: pretool_check.shパス修正/inbox_write dead code削除 |
| cmd_1268 | ピンク羊追加候補10件発掘（合計25件・7分55秒） |
| cmd_1267 | qnly_death漫画ショートv4 YouTube非公開アップ |
| cmd_1266_b | お題1「あちらのお客様」6枚再生成完了（OK/NGテロップ修正版） |
| cmd_1265 | 3総集編クリップ→YouTube非公開アップ |
| cmd_1264_b | xlDFsyNm_eE 36分版merged SRT完成（523ブロック） |
| cmd_1263 | qnly_death+bon_trick 漫画パネル14枚生成 |
| cmd_1280 | MENゴーグル目装着版4枚 v9方式（白黒差分→RG | 4/9 |
| cmd_1201 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1204 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1209 | お題2「私のために争わないで」6枚再生成（� | 4/9 |
| cmd_1212 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1218 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1221 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1222 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1232 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1233 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1255 | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| nightly_audit | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| shogun_direct | ...\n    files: [...]
    detail: |
      ...
    recom | 4/9 |
| cmd_1289 | bon_trick P3/P5 再生成（ドズルsmile_r2変更・R4版� | 4/9 |
| cmd_1290 | bon_trick P3/P5 再生成（ドズルsmile_r2変更・R4版� | 4/9 |
| cmd_1291 | bon_trick P3/P5 再生成（ドズルsmile_r2変更・R4版� | 4/9 |
| cmd_1294 | お題2「私のために争わないで」6枚再生成（� | 4/10 |
| cmd_1297 | お題2「私のために争わないで」6枚再生成（� | 4/10 |
| cmd_1292 | bon_trick P3/P5 再生成（ドズルsmile_r2変更・R4版� | 4/10 |
| cmd_1316 | お題2「私のために争わないで」6枚再生成（� | 4/11 |
| cmd_1317 | bon_trick P3/P5 再生成（ドズルsmile_r2変更・R4版� | 4/11 |
| gacha45_shogun | お題2「私のために争わないで」6枚再生成（� | 4/11 |
| cmd_1330 | お題2「私のために争わないで」6枚再生成（� | 4/11 |
| nightly_audit_auto | ...\n    files: [...]
    detail: |
      ...
    recom | 4/12 |
| cmd_1332 | お題2「私のために争わないで」6枚再生成（� | 4/12 |
| cmd_1333 | お題1 P6（p6_achira_clear）のみ再生成（NGワード | 4/12 |
| cmd_1335 | お題2「私のために争わないで」6枚再生成（� | 4/12 |

## 足軽・軍師 状態

| 足軽 | CLI | 状態 | 現タスク |
|------|-----|------|---------|
| 1号 | Sonnet | 実行中 | subtask_1347a（generate_panel_candidates.py実装）|
| 2号 | Sonnet | idle | — |
| 3号 | Sonnet | idle | — |
| 4号 | Sonnet | idle | — |
| 5号 | Sonnet | idle | — |
| 6号 | Sonnet | idle | — |
| 7号 | Sonnet | idle | — |
| 軍師 | Opus | idle | nightly_audit_20260412_youtube_api完了（C2/H5/M8）|

## APIキー状況
- **Vertex AI ADC**: ✅ 正常
- **GLM**: ⚠️ レート制限超過（リセット4/11）→ 足軽全員Sonnet切替済み

## チャンネル実績（2026-04-01更新）
- 登録者**1,007人** / 視聴回数**98.4万回** / 総再生時間**5,925時間**
- **収益化条件は未達**

## 🌐 外部公開サービス
- AI NEWS: https://genai-daily.pages.dev
- Discord Bot: discord-news-bot.service（systemd常駐化済み）
