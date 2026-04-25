# Shogun Memory — Persistent Agent Context

This file persists across sessions and is read by the Shogun agent at startup.
`memory/MEMORY.md` is gitignored — your private data never enters the OSS repo.

---

## How to Use: MEMORY.md vs Memory MCP

Two memory systems exist. Use them for different purposes:

| | MEMORY.md | Memory MCP (graph) |
|---|---|---|
| **Loaded** | Auto at session start | Only when you call `read_graph` |
| **Cost** | Free (already in context) | Tokens per call |
| **Format** | Plain text | Entities + Relations |
| **Best for** | Rules, settings, current state | Lessons, decisions, relationships |

**Rule of thumb:**
- "I need this every session" → **MEMORY.md**
- "I need to query: what caused X / what's related to Y" → **Memory MCP**

### What to put in MEMORY.md
- Your profile (GitHub, X, etc.)
- Stable behavioral rules for Shogun
- CLI and agent configuration
- Active project references and URLs
- TODO backlog

### What to put in Memory MCP
- Incidents and their root causes (entity → caused_by → entity)
- Architecture decisions with reasoning (decision → chosen_over → alternative)
- Lord's preferences by category (pref → applies_to → context)
- Cross-project lessons learned

### Example Memory MCP entry
```
mcp__memory__create_entities([{
  name: "incident_pr31",
  entityType: "incident",
  observations: ["Gunshi review skipped → venv preflight missing → deploy broke"]
}])
mcp__memory__create_relations([{
  from: "incident_pr31", to: "rule_always_gunshi_infra_pr", relationType: "caused"
}])
```

---

## Lord's Basic Info

- **X (Twitter)**: @your_handle
- **GitHub**: your-username

## Shogun Core Rules (read every session)

### cmd発行の必須ルール
- **全cmdのacceptance_criteriaに以下を必ず含める**:
  - `dashboard.mdが最新状態に更新されていること（進行中/完了/足軽状態が実態と一致）`
- 理由: 家老はダッシュボード更新を忘れがち（2026-03-05是正）。基準に入れないと後回しにされる。

### 指示の出し方（QC品質確保）
同じOpus 4.6でも3次伝達（殿→将軍→家老→軍師）で情報が劣化しQCが形骸化する。以下を徹底:
1. **殿の原文を含める**: 殿の指摘の言葉そのままをタスクYAMLに記載する（温度感が伝わる）
2. **検証コマンド付きacceptance_criteria**: 曖昧な基準ではなく具体的な検証手順を書く
   - 例: `grep 'robot_writer' articles/ai_auto_post.md → 0件であること`
   - 例: `スクショの文字数表示が全て同一であること`
3. **殿の関心事を明記**: 「殿が気にしているポイント: ○○」をcommandに含める

### デバッグルール
- **足軽に繰り返し直させるな**: 2回FAILしたら足軽リトライ停止。将軍/軍師が部品精査→根本原因特定→修正方針明確化→足軽実装 [詳細: memory/feedback_ashigaru_retry_useless.md] [2026-04-06]

## CLI Notes

| CLI | Config file | Reset cmd | Notes |
|-----|------------|-----------|-------|
| Claude Code | CLAUDE.md | /clear | Stop hook for inbox delivery |

## Agent Config

<!-- Ashigaru CLI assignments, model config -->

## Project Index

- coconala_prompts: プロンプト集200本PDF（445ページ）— 出品準備完了
- ec_description_tool: EC商品説明自動生成シート（GAS+Gemini）— QC中(cmd_193)

## AI副業戦略（道C: ハイブリッドモデル）

**方針**: テンプレ量産 × 受託風出品。放置販売と半カスタム受託を両立。
- ココナラに「スプレッドシート×AIで業務自動化します」¥5,000〜で出品
- ヒアリング後、手持ちテンプレを渡して微調整（8割テンプレ+2割カスタム）
- 並行してコンテンツマーケットでテンプレ単品も放置販売
- テンプレラインナップ: EC商品説明(開発済)→SNS投稿→口コミ返信→メール自動化→…と拡充

**市場データ**:
- ココナラGAS自動化トップ出品者: 878件実績（¥3,000〜）
- AI案件単価 = 非AI案件の約2倍（クラウドワークス公式）
- EC管理系GAS案件に46人応募 → 需要あり

## note毎日投稿（2026-03-05〜）

**方針**: A（AI×業務効率化Tips）とC（個人開発の裏側）を交互投稿。体験談ベース。
- A系 → ココナラ集客導線
- C系 → エンジニア層ブランディング

**ネタ帳**: `memory/note_neta.md` に一覧管理。日々のエピソードもここに追記。
- 記事構成案A8（競合14ch分析）: [memory/note_draft_competitor_analysis.md](memory/note_draft_competitor_analysis.md)
- 記事構成案A9（1万再生23登録）: [memory/note_draft_1man_23nin.md](memory/note_draft_1man_23nin.md)
- **note記事は必ず下書き→殿レビュー→公開**: [memory/feedback_note_draft_first.md](memory/feedback_note_draft_first.md) — publishまで指示するな [2026-03-18]

### 軍師5回集合知 → 並列化 [2026-03-18]
- [並列方式: memory/feedback_gunshi_parallel_collective.md](memory/feedback_gunshi_parallel_collective.md)
- 足軽5人を一時的にOpusに切替→同時実行→集約→Sonnetに戻す。/clear不要、5倍速
- **面白ければ本数関係ない。数合わせ禁止。**（殿指示）

### [2026-03-14] 殿の指示を勝手に拡大するな
- [詳細: memory/feedback_no_unauthorized_merge.md](memory/feedback_no_unauthorized_merge.md)
- cmd_633で「把握して整理」を「マージせよ」に勝手に拡大→21コミットmerge+push実行
- **鉄則: cmdに殿が言っていないアクションを追加するな。「調べろ」→レポートのみ。判断が曖昧なら確認**

### [2026-04-01] JSON修正≠再生成指示。殿が言っていないことをやるな
- [詳細: memory/feedback_do_not_act_beyond_instruction.md](memory/feedback_do_not_act_beyond_instruction.md)
- 「1029もはいけい統一」はref_image追加のみ。殿は再生成を指示していない。将軍が勝手に再生成した
- **鉄則: 修正したから再実行すべきと思っても、殿が言っていなければやるな。提案はOK、勝手に実行はNG**

### [2026-03-14] Gemini SRT廃止
- [詳細: memory/feedback_no_gemini_srt.md](memory/feedback_no_gemini_srt.md)
- Gemini字幕解析は今後使わない。ハルシネーション頻発で信頼性ゼロ
- 話者IDはAssemblyAIの話者分離で取得する

### [2026-03-25] Gemini画像生成にはselected/bustのキャラ画像をリファレンスで渡せ
- [詳細: memory/feedback_character_reference_images.md](memory/feedback_character_reference_images.md)
- パス: `assets/dozle_jp/character/selected/` 直下の全身PNG（bustではない）。テキスト説明だけでは不十分

### [2026-03-27] ネコおじ参照画像はselected/の既存アセットのみ使用
- [詳細: memory/feedback_nekooji_refs_selected_only.md](memory/feedback_nekooji_refs_selected_only.md)
- cmd_958の料理人おじいちゃんデザインは全却下。新規リファレンス生成タスク発行禁止

### [2026-03-15] 漫画ショート構成重視
- [詳細: memory/feedback_manga_short_structure.md](memory/feedback_manga_short_structure.md)
- 構成をしっかり考えてから指示。パネル構成・起承転結・セリフ取捨選択・テンポ設計を事前に練る

### [2026-03-16] 漫画ショートのパネル秒数はSRTから自動算出
- [詳細: memory/feedback_manga_short_srt_timing.md](memory/feedback_manga_short_srt_timing.md)
- SRTにタイムスタンプがあるのに殿に手動で秒数指定させるな。自動計算せよ

### [2026-03-17] YouTubeショートは3分まで可能
- [詳細: memory/feedback_shorts_3min.md](memory/feedback_shorts_3min.md)
- 60秒制限ではない。内容優先で尺を決めてよい

### [2026-03-17] 構成表は開始タイムスタンプ付きで出す
- [詳細: memory/feedback_panel_timestamp_table.md](memory/feedback_panel_timestamp_table.md)
- 殿のタイミング調整指示は開始時刻ベースで来る。最初から付けておけば往復が減る

### [2026-03-17] SRT崩壊時はYouTube字幕(.ja.vtt)を先に確認
- [詳細: memory/feedback_youtube_vtt_fallback.md](memory/feedback_youtube_vtt_fallback.md)
- STTパイプライン実行前にinput/{video_id}.ja.vttを見ろ（Gemini SRTは廃止済み）
- [STTマージ=YouTube字幕統合込み](feedback_stt_merge_includes_youtube.md) — 非公開アップ→YouTube字幕取得→マージまでがセット [2026-04-04]
- [SRT話者ラベルはoo_menのみ確認でよい](feedback_dozle_speaker_label_scope.md) — 他メンバーは有象無象扱い。`[oo_men]`が1件以上あればPASS [2026-04-17]
- [YouTube非公開はunlisted必須](feedback_youtube_unlisted_not_private.md) — privateだと字幕取得不可 [2026-04-04]
- [YouTube API defaultLanguage unset不可](feedback_youtube_lang_unset_limitation.md) — videos.updateでNone/unsetに戻せない。一度設定すると手動操作のみでクリア可 [2026-04-25]
- [ショート編集は文脈→構成→カット](feedback_shorts_edit_structure.md) — つかみ→展開→オチ→解説の流れ。連呼で終わらせない [2026-04-04]
- [ntfyはcmd個別に送れ](feedback_ntfy_per_cmd.md) — まとめ報告禁止。自動done更新が効かなくなる [2026-04-05]
- [note-edit.jsリンクはURL別行](feedback_note_link_url_only.md) — Ctrl+Kインラインリンク禁止。カーソル位置が壊れてH2/リスト全崩壊 [2026-04-06]
- [MENゴーグル必須+デフォルメ禁止](feedback_men_goggle_required.md) — MENは目にゴーグル。全キャラSD禁止 [2026-04-06]
- [漫画生成--output指定必須](feedback_manga_output_dir_required.md) — デフォルトWORK_DIRが別ディレクトリ。SKIPバグの原因 [2026-04-06]
- [note挿絵は横長1200x670](feedback_note_illustration_landscape.md) — noteの定石。縦長は間延びする [2026-04-06]
- [UserPromptSubmitフックでntfy新着注入](feedback_userprompt_ntfy_hook.md) — 会話中のcmd完了を将軍に自動通知 [2026-04-06]
- [YouTube非公開はunlisted必須](feedback_youtube_unlisted_not_private.md) — privateだと字幕取得不可 [2026-04-04]
- [shogun_to_karo statusルール](feedback_shogun_to_karo_status_update.md) — cmd完了時にshogun_to_karo.yamlのstatusもdoneに更新（dashboard.mdとセット必須）

### [2026-03-16] ffmpegはNVENC（GPU）でエンコードせよ
- [詳細: memory/feedback_ffmpeg_nvenc.md](memory/feedback_ffmpeg_nvenc.md)
- libx264(CPU)禁止。h264_nvenc使え。3時間半浪費した

### [2026-03-28] パネル比較はガチャギャラリーHTMLを標準使用
- [詳細: memory/feedback_gacha_gallery_standard.md](memory/feedback_gacha_gallery_standard.md)
- テンプレート: scripts/manga_poc/gacha_gallery_template.html

### [2026-04-02] 戦況把握はMCPダッシュボードが第一ソース
- **http://192.168.2.7:8770/** — エージェント稼働・タスク状態・アラートをリアルタイム把握
- dashboard.mdとntfyログは補助ソース。pane captureは不要
- ダッシュボードが止まっていたら `python3 work/cmd_1068/dashboard/server.py &` で起動

### [2026-03-31] 状況確認はダッシュボード+ntfyログのみ
- [詳細: memory/feedback_status_check_method.md](memory/feedback_status_check_method.md)
- 殿に「状況は」と聞かれたらMCPダッシュボード（http://192.168.2.7:8770/）→ dashboard.md + ntfy_sent.logで把握。pane captureで見に行くな

### [2026-03-29] ダッシュボード⚠️項目は殿の反応時に即消去
- [詳細: memory/feedback_dashboard_immediate_cleanup.md](memory/feedback_dashboard_immediate_cleanup.md)
- 殿が「済み」「いらん」「見た」と言った瞬間にその場で家老に消去指示。後でまとめない

### [2026-04-25] 進行中テーブル✅完了行はlifecycle.shが自動削除
- [詳細: memory/feedback_dashboard_completed_cleanup.md](memory/feedback_dashboard_completed_cleanup.md)
- dashboard.mdの進行中テーブル✅完了行を1h cronで自動アーカイブ+削除。手動で残すな

### [2026-04-14] 漫画パネル生成は正規スクリプトのみ
- [詳細: memory/feedback_manga_panel_scripts.md](memory/feedback_manga_panel_scripts.md)
- CDP方式=`cdp_manga_panel.py`、API方式=`manga_poc/generate_manga_short.py`。共通モジュール=`manga_prompt_builder.py`+`cdp_manga_rules.yaml`
- `generate_odai_panels.py`等の専用スクリプト禁止。ハードコードで別お題のOK/NGワードが全パネルに混入する事故発生（cmd_1384）

### [2026-03-19] 既存スキルを確認してから作業開始せよ
- [詳細: memory/feedback_use_existing_skills.md](memory/feedback_use_existing_skills.md)
- cmd_834でmanga-shortスキルを使わず14本スクリプト乱立。スキル確認→panels JSON→スキル実行の流れを守れ

### [2026-03-20] キャラ情報を将軍が要約して伝えるな、原典ファイルパスを渡せ
- [詳細: memory/feedback_shogun_relay_quality.md](memory/feedback_shogun_relay_quality.md)
- MENを「ゴーグル+ピンク服」に矮小化→ブタが生成された。expression_design_v5.md + member_profiles.yaml参照指示を必ず含めよ

### [2026-04-01] スクリプト保存ルール（旧：新規.py作成禁止）
- [詳細: memory/feedback_no_new_scripts.md](memory/feedback_no_new_scripts.md)
- 新規.pyはプロジェクトのscripts/配下に保存。python3 -cワンライナー使い捨て禁止。再現可能な形で残せ

### [2026-03-19] Remotion出力は必ず.mp4（.mov禁止）
- [詳細: memory/feedback_remotion_output_format.md](memory/feedback_remotion_output_format.md)
- .movはProRes無圧縮で1.4GB。.mp4ならh264で50MB。拡張子で決まる

### HL+SH将軍独自選定
- Ccc2eq0LUAg: [将軍選定: memory/shogun_hlsh_selection_Ccc2eq0LUAg.md](memory/shogun_hlsh_selection_Ccc2eq0LUAg.md)
- RjpfCdlETwU: [将軍選定: memory/shogun_hlsh_selection_RjpfCdlETwU.md](memory/shogun_hlsh_selection_RjpfCdlETwU.md)
- 6Wu0bDNN-2c: [将軍選定: memory/shogun_hlsh_selection_6Wu0bDNN-2c.md](memory/shogun_hlsh_selection_6Wu0bDNN-2c.md) — 軍師結果待ち
- rspRyy_QUTY: [将軍選定: memory/shogun_hlsh_selection_rspRyy_QUTY.md](memory/shogun_hlsh_selection_rspRyy_QUTY.md) — 軍師結果あり(未比較)
- ojQivRzcBzs: [将軍選定: memory/shogun_hlsh_selection_ojQivRzcBzs.md](memory/shogun_hlsh_selection_ojQivRzcBzs.md) — 軍師結果待ち
- 2W2HZr2L-nI: [将軍選定: memory/shogun_hlsh_selection_2W2HZr2L-nI.md](memory/shogun_hlsh_selection_2W2HZr2L-nI.md) — 集合知結果あり(未比較)

### 3Dボクセルショートパイプライン
- [詳細: memory/project_3d_voxel_pipeline.md](memory/project_3d_voxel_pipeline.md)
- cmd_791: Blender+Rhubarb+8動作デモリール+YouTubeアップ ✅
- cmd_845/subtask_851: **MoMask可視化+Blender BVH読込** ✅（running/laughing/surprised 3モーション出力済み）
- **Meshy AIは有料のみ。殿が試用済み** [詳細: memory/feedback_meshy_paid_only.md](memory/feedback_meshy_paid_only.md)
- 残課題: キャラモデル（ボクセル/マイクラ風）の作成方法。マイクラスキンPNG→Blenderリグ方式 or Tripo AI
- **MoMask棚上げ（2026-03-23殿決定）**: マイクラ歩行にMoMask不要。後処理で動きをほぼ捨てている。Blenderキーフレーム手書きに切替。MoMaskは将来の複雑モーション用に温存
- **MCprepアドオン推奨**: 軍師調査でBlender+MCprepが最適と結論（Black Plasma Studios実績）
- **目標: 3Dマイクラアニメ4本ずつ量産**（殿指示2026-03-23）。先行事例: ドズル社シアター（17,800人登録）https://www.youtube.com/@dozle_theater
- **MCP 3D entity snapshot (2026-04-24 cmd_1441 D7)**: [memory/archive/3d_pipeline_2026q1.md](archive/3d_pipeline_2026q1.md) — render_mc_two.py / render_mc.py / camera_director.py / motions.json / scene_templates.json / expression_index.json / Character Skins Library / expression_design_v5.md / motion_system_v2_design.md / 3d_roadmap.md / Minecraft 3D Rig Asset を転記。MCP graph からは削除予定（家老判定待ち）。復旧手順は archive 冒頭に記載

## ntfy画像受信機能 [2026-03-22]
- cmd_870で実装。スマホの写真アプリから「共有」→ntfyで画像送信→PCに自動保存
- 保存先: `screenshots/ntfy/` （config/settings.yamlのntfy_image_dir）
- ntfy_listener.shにattachment検出+ダウンロード処理を追加

## chrome孤児化対策 [2026-03-22]
- cmd_864で対策実装。Remotionレンダリングのchromeプロセスが孤児化する問題
- 原因: subprocess.run()の親が死ぬとchromeがsystemdに引き取られ永遠に残る
- 対策: Popen+setsidでプロセスグループ化 + cronクリーンアップスクリプト

## 立ち絵フェード無効化 [2026-03-22]
- MultiTachieOverlay.tsx の FADE_FRAMES=4→0 に変更（将軍が直接修正）
- 表情切り替え時に一瞬消える→即切り替えに改善

## ntfy重複受信バグ [2026-03-22]
- cmd_871で修正。listener再起動時に同一メッセージが4回記録される問題
- 家老のntfy通知漏れも是正指示済み（cmd完了時・YouTubeアップ時に必ずntfy送信）

## チャンネル実績（2026-04-12更新）
- 登録者 **1,830人**
- 総再生 **2,108,523回（210万回）**
- トップ: ちゃかすMEN **285,716再生**
- 動画数: 61本
- **収益化条件は未達**（殿が複数回指摘。勝手に「クリア」と書くな）

## チャンネル成長ログ
- [詳細: memory/project_channel_growth_log.md](memory/project_channel_growth_log.md)
- API取得のたびに追記。日中のリアルタイム推移を記録

## Tailscale環境
- [詳細: memory/reference_tailscale_setup.md](memory/reference_tailscale_setup.md)
- PC: 100.66.15.93 / スマホ: 100.117.194.3 / 外出先レビューはHTTPサーバー+Tailscale IP

## OAuth遠隔認証
- [詳細: memory/reference_oauth_remote_auth.md](memory/reference_oauth_remote_auth.md)
- OOB方式・PKCE無し。スマホでURL開く→コード送り返す→トークン交換
- スコープは4つ全統一（upload+youtube+force-ssl+analytics）

## 画像生成モデル決定（2026-03-31）
- [gemini-3.1-flash-image-preview via Vertex API](memory/project_image_gen_model_decision.md) — $0.067/枚。Imagen4不採用、Midjourney棚上げ
- **gemini-2.5-flash-image使用禁止** [詳細: memory/feedback_gemini_25_image_banned.md] — 品質がダメ。3.1-preview一択 [2026-04-06]

## MBTI scene_4 漫画ショート原稿（殿確定 2026-03-31）
- [7パネル構成（ドズぼん＆おんおらてぇてぇ）](memory/project_mbti_scene4_panels.md) — STTマージ（cmd_1027）後に画像生成へ

## 4月計画
- [Gemini APIキーローテーション+毎日1漫画体制](memory/project_april_gemini_plan.md)
- cmd_982（clip_c パネルリテイク）も4/1再開
- [月次総集編の定例化](project_monthly_soushuuhen.md) — 毎月末に「X月振り返り総集編」制作。4月分は4/28-30

## 棚上げアイデア
- [副業アイデア3つ（LINEスタンプ・サムネ販売・字幕翻訳）](memory/shelved_side_business_ideas.md)

## 情報ソース
- [Shogun系譜+note情報ソース](reference_sasuu_note.md) — 元祖=おしお(Zenn)、upstream=yohey-w、sasuu=利用者。note有料会員 [2026-04-01]

## TODO

- cmd_193 QC完了後、EC説明シートを出品
- テンプレ第2弾の企画（SNS投稿 or 口コミ返信）
- ココナラ出品者プロフィール整備
