# 📊 戦況報告
最終更新: 2026-04-07 14:01

## 📱 ntfy通知
トピック: `shogun-962f817f20fadb36`

## 🚨 要対応 - 殿のご判断をお待ちしております

### ⚠️ cmd_952 ナレーション動画受託案件 — 殿方針確認待ち

### 🔧 夜間監査 2026-04-05 残項目
- CRITICAL: OAuth token.jsonがリポジトリ内格納
- HIGH: ハードコードパス15+ファイル

### 📋 漫画フォント・吹き出し調査完了
**フォント・吹き出し調査完了** (gunshi_report_font_bubble_v2.yaml):
- 今回追加: F910新コミック体(Apache 2.0)・しっぽりアンチック・やさしさアンチック
- 全候補: 源暎アンチック/F910新コミック/しっぽりアンチック/やさしさアンチック/ラノベPOP/けいふぉんと/Noto Sans/Noto Serif/M+/源柔ゴシック（計10種）
- 吹き出し最有力: フキダシデザイン（1000+素材・SVG・商用可・wget DL可）
- **フォント比較シートv2**: `work/font_compare/manga_font_comparison_v2.png`（7種類・171KB）⚠️源暎アンチックのみDL失敗（公式サイト要手動DL）
- **吹き出しオーバーレイ設計書完成**: `bubble_overlay/DESIGN.md`（19KB）— アーキテクチャ・bubble_overlays JSON仕様・4Phase実装計画・フォント/素材DL手順 網羅

**吹き出し** (gunshi_report_manga_bubbles.yaml / gunshi_report_bubble_deep.yaml):
- 既存: `svg_bubbles.py`(Bezier高品質) + `bubble_samples.py`(Pillow軽量) がプロジェクト内に存在
- 深掘り結果: **フキダシデザイン**(1000種超・SVG・商用可)が最高品質だがCLI自動DL不可（JS制限）
- 推奨方式: フキダシデザインから手動10〜15種DL → assets/bubbles/配置 → Python自動合成
- CLIP STUDIO ASSETS: .clip形式でLinux利用不可（除外）
- `pip install cairosvg` + 源暎アンチックDLで実装可能（約1〜2時間）

### 🔧 夜間監査 2026-04-07 — 動画制作スクリプト群（CRITICAL 0 / HIGH 2 / MEDIUM 3）
- HIGH: generate_outro.py — moviepy中間出力にlibx264使用（最終出力はNVENC済み、中間ファイルが遅い）
- HIGH: make_shorts_complex_v17.py — 絶対パスハードコード（アーカイブ版のため優先度低）
- MEDIUM: types.ts — speaker型にnekooji欠落（10000m線路等でTS型エラーの可能性）
- MEDIUM: main.py — selected_check_hook.shの絶対パス2箇所
- MEDIUM: ShortsComposition.tsx — subHookText描画が無効化（Remotion版とffmpeg版で挙動差異）


## 🔄 進行中

| cmd | 内容 | 担当 | 開始 |
|-----|------|------|------|
| cmd_1239 | 仲間の気持ちチート 全12お題クリップ集 YouTube非公開アップ完了 → 殿の選定待ち https://www.youtube.com/watch?v=zrWtkDcLPrA | 4/7 |
| cmd_1238 | 仲間の気持ちチート batch1（お題04ママゲーム）完了 → 殿QC待ち http://100.66.15.93:8785/gallery_cmd1238_odai04.html | 4/7 |
| cmd_1237 | 重機漫画P1/P3/P4リテイク round3完了 → 殿レビュー待ち http://100.66.15.93:8779/gallery_cmd1237.html | 4/7 |
| cmd_1231 | 重機漫画（一粒の種）round1完了 WARNING0件 → 殿レビュー待ち http://192.168.2.7:8777/gallery_cmd1231.html | 4/6 |
| cmd_1236 | AI NEWS Discord配信修正完了（--flush実装+genai_daily統合+pending配信済み） | 4/7 |
| cmd_1235 | 重機漫画v2 round2完了 WARNING0件 → 殿レビュー待ち http://192.168.2.7:8774/gallery_cmd1235.html | 4/7 |
| cmd_1234 | 9bK6yDYwHng お題12箇所クリップ集 YouTube非公開アップ完了 → 殿の選定待ち https://www.youtube.com/watch?v=ilZeaH5M3xc | 4/6 |
| cmd_1233 | 9bK6yDYwHng HL/SH集合知完了 HL6件・SH4件・漫画ショート5件 → 殿の選定待ち | 4/6 |

## ✅ 最近の完了
| cmd | 内容 | 完了日 |
|-----|------|--------|
| cmd_1244 | note「AIにテストコードを書かせるな」Gist版+挿絵3枚+キャプション3件 完了 → 殿レビュー待ち https://note.com/n/ncdfbdfeeadd4 | 4/7 |
| cmd_1246 | 吹き出し顔検出+自動配置完了 — face_detector.py+顔3回避+QC C1-C6 PASS → 殿確認待ち http://100.66.15.93:8783/work/test_compose_p4_v3.png | 4/7 |
| cmd_1241 | 吹き出しPhase3完了 — fukidesign12SVG加工+svg_bubbles拡張+render_bubble fukidesign対応 | 4/7 |
| cmd_1240 | 吹き出しオーバーレイシステム実装完了（font_config/render_bubble_html/bubble_overlay_compose）Phase1+2テスト成功 | 4/7 |
| cmd_1232 | yEtn5xGWVK4 HL/SH集合知完了 — HL6件・SH4件 → 殿の選定待ち | 4/7 |
| cmd_1222 | -F9M99oe7fY HL/SH集合知完了 — HL6件・SH3件→殿の選定待ち | 4/6 |
| cmd_1230 | 一粒の種tono_edit STTマージ完了（8856words・実名6名）⚠️YouTube URL未確認→要確認 | 4/6 |
| cmd_1229 | _whtyCALBBI候補8区間クリップ集 YouTube非公開アップ完了 → 殿の選定待ち https://www.youtube.com/watch?v=gV38OnfB8mk | 4/6 |
| cmd_1228 | TNT P6再生成完了 → 殿レビュー待ち http://192.168.2.7:8774/gallery_cmd1228.html ⚠️FileAPIフォールバック発生→成功 | 4/6 |
| cmd_1227 | TNT P1P2P6再生成完了 WARNING0件 → 殿レビュー待ち http://192.168.2.7:8774/gallery_cmd1227.html | 4/6 |
| cmd_1226 | note下書き更新完了（有料ゾーン追加・挿絵3枚維持）→ 殿レビュー待ち https://note.com/n/ncdfbdfeeadd4 | 4/6 |
| cmd_1225 | note下書き投稿完了「AIにテストコードを書かせるな」挿絵3枚+カバー+ハッシュタグ | 4/6 |
| cmd_1224 | note記事「AIにテストコードを書かせるな」挿絵3枚生成完了 → 殿レビュー待ち http://192.168.2.7:8775/naginata_illustrations/gallery_cmd1224.html | 4/6 |
| cmd_1223 | 枯れ木漫画縦型 YouTube非公開アップ+概要欄設定完了 https://www.youtube.com/watch?v=-BKIQ0PzFT8 | 4/6 |
| cmd_1221 | IKu8Dad0YyY HL/SH集合知完了 — HL6件・SH4件→殿の選定待ち | 4/6 |
| cmd_1218 | _whtyCALBBI HL/SH集合知完了 — HL6件・SH4件→殿の選定待ち | 4/6 |
| cmd_1220 | note記事 role_table.png挿入済み（QCエラーあり・要確認） | 4/6 |
| cmd_1219 | note記事（nedb886542772）挿絵4枚+カバー挿入 QC PASS（Gemini Vision） | 4/6 |
| cmd_1211 | note_visual_qc.py作成（Gemini Vision 3分割QC）commit aca3302 | 4/6 |
| cmd_1217 | 桜漫画round4生成 — 6枚 WARNING 0件 GCS URI正常 | 4/6 |
| cmd_1216 | ref画像パス解決修正テスト — 全5項目PASS（prompt_tokens 4237） | 4/6 |
| cmd_1215 | 桜漫画2周回し生成完了（round2/round3各6枚+比較ギャラリーHTML） | 4/6 |
| nightly_audit | STTパイプライン矛盾検出 — 矛盾なし（INFO1件: symlink残存のみ） | 4/6 |
| cmd_1214 | generate_manga_short.py リトライ+skip-existing実装完了 | 4/6 |
| cmd_1213 | YAMLバリデーション+cron設定（PostToolUseフック+slim_yaml毎日3時） | 4/6 |
| cmd_1212 | TNT漫画429分析完了 — リトライ不在+複数同時実行が根本原因 → gunshi_report_cmd1212.yaml | 4/6 |
| cmd_1210 | sasuuノート全記事PDF化96件（note API v2 16ページ×6件）→ work/sasuu_articles/ | 4/5 |
| cmd_1209 | note投稿パイプライン整備 — 殿指示により中断（note再投入うまくいかず） | 4/6 |
| cmd_1207 | note記事挿絵4枚挿入（CDP方式・insert_images_shogun_article.js・下書き保存済） | 4/5 |
| cmd_1208 | 漫画パイプライン5項目改善（selfcheck_rules・S1-S8・is_climax・char_prohibitions・テンプレ画像3枚） | 4/5 |
| cmd_1206 | sasuuノート全記事PDF化18件 → work/sasuu_articles/ | 4/5 |
| cmd_1205 | cdp_image_gen.py作成（CDP汎用・--prompt/--output/--ref-image/--size対応・テスト確認済） | 4/5 |

| cmd_1204 | 漫画システム比較分析（斉川ニア記事）→ 高優先3件（セルフチェック2段階・構図パターン・キメゴマ）→ gunshi_report_cmd1204.yaml | 4/5 |
| cmd_1201 | 漫画構図汎用ナレッジ文書作成（15件JSON引用・339行）→ manga_composition_knowledge.md | 4/5 |
| cmd_1200 | note下書き本文投入+カバー画像+ハッシュタグ設定済 → https://note.com/n/nedb886542772 | 4/5 |
| cmd_1199 | GLM-5.1スペック調査（CTX 200K/出力131K/5h1600prompts/画像非対応）→gunshi_report_cmd1199.yaml | 4/5 |
| cmd_1197 | TNTネザー漫画パネル構図分析（5改善点特定→gunshi_report_cmd1197.yaml） | 4/5 |
| cmd_1198 | note下書き投稿（AIエージェント8体記事）→ https://note.com/n/nedb886542772 | 4/5 |
| cmd_1196 | note記事なぎなた挿絵5枚（カバー1+本文4）CDP+記事コメント挿入（commit 2050b00） | 4/5 |
| cmd_1194 | Vertex AI ADC認証一括移行87+箇所+Embedding location hotfix | 4/5 |
| cmd_1188 | PreToolUseフック実装（work/cmd_*防止・テスト4件全PASS） | 4/5 |

## 足軽・軍師 状態

| 足軽 | Pane | CLI | 状態 | 現タスク |
|------|------|-----|------|---------|
| 1号 | 0.1 | GLM-5.1 | idle | — |
| 2号 | 0.2 | GLM-5.1 | idle | — |
| 3号 | 0.3 | GLM-5.1 | idle | — |
| 4号 | 0.4 | GLM-5.1 | idle | — |
| 5号 | 0.5 | GLM-5.1 | stuck | cmd_1180（放置） |
| 6号 | 0.6 | GLM-5.1 | idle | — |
| 7号 | 0.7 | GLM-5.1 | idle | — |
| 軍師 | 0.8 | Opus | idle | — |

## APIキー状況
- **Vertex AI ADC**: ✅ 復旧済み（殿が通常HOME・GLM HOME両方で確認）
- **VERTEX_API_KEY**: 廃止完了（cmd_1194でADC移行済み）
- **GEMINI_API_KEY**: 期限切れ（廃止方針）
- **OPENAI_API_KEY**: 正常

## チャンネル実績（2026-04-01 13:21更新）
- 登録者**1,007人**（1000人突破！）
- 視聴回数**98.4万回** / 総再生時間**5,925時間**
- ちゃかすMEN **210,081再生**（チャンネル最多）
- 極小MEN **131,804再生**（急伸中）

## 🌐 外部公開サービス
- AI NEWS: https://genai-daily.pages.dev
- Discord Bot: discord-news-bot.service（systemd常駐化済み）
