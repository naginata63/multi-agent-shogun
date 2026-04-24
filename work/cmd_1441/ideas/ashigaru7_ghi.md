# 足軽7号アイデア出し（MCN申請 + スキル化候補 + cmem todolist Phase2/3 / g・h・i カテゴリ）

cmd_1441 Phase A 足軽7号担当分。3カテゴリを1ファイルに統合。
作成: 2026-04-24 13:35 / ashigaru7
関連: 将軍 cmd_1436(cmem)・dashboard🚨スキル化候補・work/dozle_application/

---

# (g) MCN申請文 v1 → v2 改善

## g-1. 現状

| 項目 | 値 | 備考 |
|------|----|------|
| v1ドラフト | `work/dozle_application/application_draft_v1.md`（78行） | 2026-04-24 07:32 作成・未送信 |
| v1作成者 | 殿 | 将軍/家老レビュー未実施 |
| チャンネル実績反映 | 登録2,740人・横長4,786h・ショート19,360h・74本 | dashboard記載値と一致 |
| AI画像生成注記 | 「ガイドライン不明につき指示待ち」と記載（独自スタイルのセクション2 + 相談事項3） | 規定なしを正直申告する立場 |
| 送信先 | ドズル社運営チーム（連絡先未記載） | ガイドラインの窓口URL/メール未参照 |
| 申請者情報 | 氏名・Gmail・チャンネルID のみ | SNS/ポートフォリオ/本人確認資料の同封なし |
| ガイドライン遵守表 | 7項目すべて ✅ | 実根拠（動画URL例示）の添付なし |
| ライセンスフィー想定額 | 未記載（「支払う前提」と表明のみ） | 相場・予算感の事前調査なし |

**問題要約**:
- 送信先・送付チャネル（メール/フォーム/X DM）が未確定のまま本文だけ完成している
- ガイドライン遵守✅表が自己申告のみ。実動画URLで裏付けていないため審査側が検証不能
- AI画像生成の扱いが「相談事項」止まり。事前に類似事例調査/業界慣行サーチをすれば v2 で「他MCNではこう扱われている」と提示できる
- v2 フローに「将軍/殿 以外の第三者レビュー」が入っておらず、誤字/敬称漏れ/実績誤記の検出機構なし

## g-2. やれてないこと

| # | 未対応事項 | 放置コスト |
|---|-----------|-----------|
| GN1 | ドズル社ガイドライン原文の v1本文への直接引用（遵守点の照合） | 審査担当者が「この申請者は本当にガイドラインを読んだか」判別できず |
| GN2 | MCN/事務所宛の実送信（v1がドラフト化石化） | YPP判定通知が来た瞬間の初動遅延 |
| GN3 | 他切り抜きチャンネルのMCN加入事例リサーチ | フィー相場・AI許容度が不明のまま交渉スタート |
| GN4 | 実績証跡の URL リスト（代表動画3本・再生数実績ページ・収益化達成スクショ） | 口頭実績のみで説得力不足 |
| GN5 | 送信後 30日無応答時の再送計画 | 音沙汰なしで停滞・1ヶ月ロス |
| GN6 | 軍師 QC（v1本文の日本語校閲・敬語チェック・ビジネス文書体裁） | 誤植・敬称間違いで初手印象悪化 |
| GN7 | AI画像生成の「代替案付き提案」化（ガイドラインNG時の切り替えプラン明記） | 「AIダメ→諦める」と読まれるリスク |

## g-3. アイデア（7案）

軸: 緊急度 = 即送 / 今週 / 来月以降 | コスト = LOW(<30分) / MED(1-2時間) / HIGH(半日超) | 効果 = 信頼獲得 / 交渉優位 / 事故防止

| # | アイデア | 緊急度 | コスト | 効果 | 根拠・具体実装 |
|---|---------|--------|--------|------|---------------|
| G-1 | **送信チャネル確定+窓口特定**: ガイドラインPDFを `projects/dozle_kirinuki/context/dozle_guideline.md` 化し、連絡先URL/メール/フォームを確定してv2の宛先欄に明記 | 即送 | LOW | 事故防止 | そもそも宛先なしでは送信不能。v2 ブロッカー解除最優先 |
| G-2 | **実績証跡リンクブロック追加**: v1「1.チャンネル概要」表の直下に「代表動画3本・YouTube Studio実績ページ・概要欄ガイドライン準拠例スクショ」を箇条書きリンクで付加 | 即送 | LOW | 信頼獲得 | 数字だけでなく視認可能URLで提示すれば審査担当の負担減 |
| G-3 | **ガイドライン遵守表に根拠URL併記**: 「✅」だけでなく「✅（例: [動画タイトル](URL)）」形式に。全7項目に代表動画を1本ずつリンク | 即送 | MED | 信頼獲得 | 自己申告→実証に格上げ。7動画×URL貼付のみで完成 |
| G-4 | **軍師QCゲート新設**: v1→v2移行前に `subtask_1441g_qc` として軍師が日本語校閲・ビジネス文書体裁チェック。QCテンプレに新項目「敬語/敬称/誤字/チャンネル名/URL有効性」を追加 | 即送 | LOW | 事故防止 | 送信後は訂正困難。軍師1パスで漏れ防止 |
| G-5 | **AI画像生成の"3段構え提案"化**: 相談事項3を「A:現行維持(AI漫画パネル) / B:ガイドライン該当なら手動イラスト化 / C:AI生成を明示ラベル強化（既にタイトル・概要欄・動画内3箇所に明記） のいずれにも対応可能」と書換 | 今週 | LOW | 交渉優位 | 「AIダメ→断念」ではなく代替案を事前提示することで可否判断の柔軟性を訴求 |
| G-6 | **他チャンネル事例リサーチ（3件）**: 「ホロライブ切り抜き」「にじさんじ切り抜き」等の既存MCN加入チャンネルをWebSearchで3件調査し、`work/dozle_application/research_peer_mcn.md` にフィー相場・AI扱い・契約体裁をまとめる | 今週 | MED | 交渉優位 | 相場観ゼロで交渉すると不利な条件を飲む。足軽にリサーチ subtask 化可能 |
| G-7 | **30日無応答時の再送スケジュール**: 送信完了時点で `/schedule` により30日後「cmd_mcn_followup」を登録。ステータス未変更なら丁重な再送メール案を自動ドラフト化 | 送信後 | LOW | 運用改善 | schedule skill 既導入。cron 1行で登録可能・忘却防止 |

**最優先3件**（Phase B 推奨）:
- **G-1**（送信チャネル確定）: これがないとv2送信不能・真のブロッカー
- **G-4**（軍師QC）: 送信後の誤字発覚事故を一撃で潰す・最小コスト
- **G-3**（遵守表にURL併記）: 審査側の検証コスト削減に最も直結

---

# (h) スキル化候補 積残

## h-1. 現状

| 項目 | 値 | 備考 |
|------|----|------|
| 現 skills/ 登録数 | **23** | cdp-manga-gen / collective-select / expression-gen / expression-short-workflow / gemini-image-prompt / gemini-video-transcribe / highlight / manga-short / manga-short-workflow / note-article / restore-panes / senkyou / serif-fix / shogun-agent-status / shogun-bloom-config / shogun-model-list / shogun-model-switch / shogun-readme-sync / shogun-screenshot / skill-creator / thumbnail / video-pipeline / youtube-stats |
| dashboard掲載の候補 | **1件** | `yt-dlp-js-runtimes-fix`（cmd_1439 で足軽1号実装中） |
| 過去レポート skill_candidate: found=true 実績 | **10件超** | queue/reports/ 走査結果（h-1.2表） |
| 承認→スキル化まで完遂した件数 | 不明（追跡機構なし） | cmd_1439のみ進行中。過去候補のトラッキング不在 |
| hotfix の横断再発パターン | **pretool_check関連 8件以上** | target_path対応漏れ・status:in_progress認識漏れが繰返し足軽をブロック |

### h-1.2 過去 skill_candidate: found=true 棚卸し（queue/reports/ 走査）

| # | 候補名 | description 要旨 | 出所レポート | 現状 |
|---|--------|------------------|-------------|------|
| C1 | **yt-dlp-js-runtimes-fix** | yt-dlp --js-runtimes node で n-challenge 回避 | gunshi_report_qc_1425c2 / ashigaru4_report_subtask_1425c2 | dashboard掲載・cmd_1439で実装進行中 |
| C2 | **pretool-target-path-fix** | pretool_check.sh の status:in_progress対応 | ashigaru3_report_subtask_1408e ほか多数 | 未スキル化・cmd_1441 Phase A で再発（足軽2/3/4/5全員hotfix） |
| C3 | **minecraft-skin-to-rig** | スキンPNG→Blenderリグ付きキャラ変換（scripts/3d/skin_loader.py） | ashigaru1_report_cmd876 / gunshi_report_cmd876 | スクリプトはあるがskill化されずホコリを被りつつある |
| C4 | **bigquery-embedding-batch** | 大量字幕embedding生成+BQ投入バッチ | ashigaru2_report_subtask_1071c | 未スキル化・再利用実績なし |
| C5 | **narration-video-pipeline** | VOICEVOX+画像スライド+ffmpegの受託ナレーション自動化 | gunshi_report_subtask_952a | 受託案件用・案件継続条件付き |
| C6 | **ai-short-drama-pipeline** | Claude脚本→Gemini画像→Kling動画→ElevenLabs→ffmpeg | gunshi_report_subtask_952b | 実験的・外部API多数 |
| C7 | **note-edit-clipboard-png** | JPEG→PNG変換+Clipboard API+Ctrl+Vでnote画像投稿 | hotfix_notes横断（複数cmd） | note-article skillに吸収可能なはず |
| C8 | **ffmpeg-amix-normalize-0** | amix normalize=0 で音量正規化無効化（SE volume対応） | hotfix_notes（cmd_14xx動画系） | 動画スキル（highlight/manga-short）共通パッチ化可 |
| C9 | **ffmpeg-filter-complex-split** | 70セグメント級の長大filter_complexを複数パスに分割する回避策 | make_v3.py系 hotfix | 横長MIX制作時の再発リスク大 |
| C10 | **bq-max-rows-explicit** | BigQuery --max_rows=10000 明示（デフォルト100行のRACE事故回避） | ashigaru複数のhotfix_notes | データ取得系スキルの標準オプション化 |

**問題要約**:
- dashboard🚨スキル化候補セクションが**1件のみ**。skill_candidate:found=true が過去10件以上あるのに表面化していない
- 候補→承認→実装→完了のライフサイクルを追跡する仕組みがない（C1だけが偶然進行中）
- pretool_check hotfix (C2) が Phase A で「全足軽が同じ回避策を独立発明」する非効率事態を起こしている
- 古い候補（C4/C5/C6）は「受託継続待ち」などで塩漬け。定期再評価されない

## h-2. やれてないこと

| # | 未対応事項 | 放置コスト |
|---|-----------|-----------|
| HN1 | skill_candidate:found=true の横断棚卸し自動化 | 報告値は上がるが dashboard に出ない=殿判断機会を逸失 |
| HN2 | 候補→承認→実装→リリースのステータス管理（Kanban化） | cmd_1439 以外の進捗が不透明。忘却→再発ループ |
| HN3 | pretool_check hotfix の恒久修正（C2） | cmd_1441 で4人が同じ回避策を独立発明した=非生産の極み |
| HN4 | 既存skills/ の棚卸し（使用実績・腐敗検知） | 23 skill のうち実際に起動される頻度不明。枯れskillを温存 |
| HN5 | skill_candidate フィールドの必須化チェック | 報告時 null 放置=候補が記録されず消滅するケース |
| HN6 | skill_candidate 提案→ skill-creator 連鎖の短縮 | 承認後も手動実装=実装ラグが大きい |

## h-3. アイデア（8案）

| # | アイデア | 緊急度 | コスト | 効果 | 根拠・具体実装 |
|---|---------|--------|--------|------|---------------|
| H-1 | **pretool_check恒久修正を最優先skill化**: C2 を「pretool-target-path-fix skill」化し、`scripts/pretool_check.sh` L78 の grep を `status: (assigned\|in_progress)` に正規表現化・target_path/output_file 両フィールド対応 | 今週 | LOW | 事故防止 | Phase A だけで4人がhotfix発明=恒久修正の ROI が突出。1行修正+unit test で済む |
| H-2 | **skill_candidate 棚卸しレポート自動生成**: 週次 cron で `grep -rA4 "^skill_candidate:" queue/reports/ \| grep -A3 "found: true"` を集計し `work/skill_candidate_report.md` を更新→dashboard🚨セクションに自動反映 | 今週 | MED | 運用改善 | HN1 解決。cron 1本で全候補を可視化 |
| H-3 | **skill-kanban.md 新設**: `shared_context/skill_kanban.md` を作り「候補」「殿承認済」「実装中」「完了」の4レーンで全候補を管理。H-2 の出力を自動流し込み | 今週 | MED | 運用改善 | HN2 解決。cmd_1439 以外の候補も見える化 |
| H-4 | **skills/ 棚卸し subtask化**: 23 skill を `skills/_audit.md` にリスト化、最終起動日（git log/tmux capture）と「現在も利用中?」判定を付記。3ヶ月不使用skillはarchive候補に | 来月 | MED | 運用改善 | HN4 解決。膨張したskillsを軽量化。manga-short-workflowとmanga-shortの役割重複なども棚卸し機会 |
| H-5 | **pretool_check ガード強化**: target_path 欠落時に「家老へのエラー通知」も自動送信（`inbox_write.sh karo "[ALERT] subtask_XXX target_path欠落"）` | 今週 | LOW | 事故防止 | HN3補強。欠落を黙って通すのではなく家老に即フィードバック |
| H-6 | **既存スクリプトのskill化一括サージ**: C3(minecraft-skin-to-rig)・C4(bq-embedding-batch)・C7(note-edit-clipboard-png)・C8(amix-normalize)・C10(bq-max-rows) を1週間で5件 skill 化する Phase B 集中実行サブタスク群 | 今週 | HIGH | QoL | 5 skill × 半日 = 2.5人日。足軽2-3人並列で1週間以内完了可能。C3は既にscriptsあるのでラッパー化だけ |
| H-7 | **skill_candidate フィールド必須化**: 報告YAMLバリデータで `skill_candidate.found` が `null` の場合 pretool_check が警告→true/false明示を強制 | 今週 | LOW | 事故防止 | HN5 解決。バリデータ既存なら数行追記で対応可 |
| H-8 | **skill承認判定テンプレ**: `shared_context/skill_approval_template.md` に「殿承認基準: ①再発回数3回以上 ②横断利用可能 ③1時間で実装可能」を明文化。候補提示時に3基準クリアを明記 | 来月 | LOW | 運用改善 | 承認プロセスの恣意性排除・候補群の優先順位付け自動化 |

**最優先3件**（Phase B 推奨）:
- **H-1**（pretool_check恒久修正）: Phase A で同じhotfixを4人が書いた=即時排除対象・ROI最大
- **H-2 + H-3**（自動棚卸し+Kanban）: HN1/HN2 を一撃解決。候補が dashboard に出続ける仕組みが主目的
- **H-6**（skill化サージ）: 塩漬け候補を一気に実装化。Phase B の最大成果物候補

---

# (i) cmem todolist Phase2/3 整理

## i-1. 現状

| 項目 | 値 | 備考 |
|------|----|------|
| cmem todolist ソース | `work/cmd_1436/todolist.md`（46行） | 2026-04-24 12:38 更新 |
| Phase1（即実行） | 3項目（C/J/D） | **全て完了** cmd_1440 で C/J/D 完遂・commit 1517ccc |
| Phase2（1週間内） | 4項目（G/K/A/B） | 未着手・今cmd_1441のフォーカス |
| Phase3（任意） | 3項目（F/M/L） | 未着手・殿判断待ち |
| 棚上げ | 2項目（E/H） | 廃案近い |
| 検証未完了 | 3項目（α/β/γ） | Phase2/3に紛れず別枠 |
| claude-mem 蓄積データ | 12,154 obs / 487,691t work / 98%節約 | 冒頭 $CMEM カウンタより |
| mem-search skill | 利用可能 | 使用実績は限定的 |

**問題要約**:
- Phase2 4項目が「未着手」のまま。担当も未割当
- 検証未完了（α/β/γ）が Phase2/3 の前提条件に絡むのに別枠扱いで紛失しやすい
- 殿/家老/足軽の実利用フローが「mem-search skill 叩く」のみで、能動的検索タイミングが未規定
- Phase3 のF(feedback候補抽出)は「殿curation」依存で殿待ち状態。プル型運用になっていない

## i-2. やれてないこと

| # | 未対応事項 | 放置コスト |
|---|-----------|-----------|
| IN1 | Phase2 G(復帰時context rebuild) の Session Start 手順組込 | 家老3時間/clearごとに context 消失→rebuild機会損失 |
| IN2 | Phase2 K(cmem_search.sh wrapper) 実装 | cmd_1440 で実装済(`scripts/cmem_search.sh`) = **実は完了済・todolist 更新漏れ** |
| IN3 | Phase2 A(cmd発令前検索 閾値化) の instructions/shogun.md 明文化 | 将軍が類似cmd再発令する事故リスク継続 |
| IN4 | Phase2 B(senkyou skill の cmem参照統合) | 戦況報告で過去傾向を無視→判断鈍化 |
| IN5 | 検証未完了 α(dateRange filter bug) の根因特定 | 古知見検索が機能せず・Phase3のFも連動NG |
| IN6 | 検証未完了 β(semantic検索 chroma-mcp 接続) の確認 | FTS5のみでは類似概念検索不可・価値半減 |
| IN7 | 検証未完了 γ(SKIP_TOOLS 見直し/Skill/SlashCommand記録化) | エージェント自己監査不可の状態継続 |
| IN8 | cmem ↔ MCP ↔ MEMORY.md の三層重複蓄積問題（足軽5号 E-8 と連動） | 同観察の3層重複で容量圧迫・検索ノイズ増 |

## i-3. アイデア（7案）

| # | アイデア | 緊急度 | コスト | 効果 | 根拠・具体実装 |
|---|---------|--------|--------|------|---------------|
| I-1 | **todolist.md 現状反映**: Phase2 K(cmem_search.sh) は cmd_1440 で実装済→✅に更新、J(モバイル対応worker LAN)も ✅済→Phase1完結を明示し Phase2残3項目(G/A/B)に集中 | 即 | LOW | 運用改善 | IN2 解決。5分で todolist 更新 |
| I-2 | **Phase2 G: Session Start に cmem 参照追加**: `instructions/karo.md` と `instructions/shogun.md` のSession Start step 3.5 に「直前24hの summary を `curl /api/summaries?limit=10` で取得→主要議題を確認」を追記 | 今週 | LOW | QoL | IN1 解決。家老/clear 後の context rebuild が機能し始める |
| I-3 | **Phase2 A: cmd発令前検索の閾値ルール**: `instructions/shogun.md` に「同カテゴリcmdを過去7日に発令したか不明な時のみ `scripts/cmem_search.sh "{キーワード}"` を実行」を明文化。必須化せず「疑念時のみ」が鍵 | 今週 | LOW | 事故防止 | IN3 解決。必須化はcmd起草遅延で殿激怒リスクあり |
| I-4 | **Phase2 B: senkyou skill 改修**: senkyou skill に「過去7日 summary 取得→ regression 兆候あれば戦況報告本文に併記」ロジック追加 | 今週 | MED | QoL | IN4 解決。変化検知系報告の精度UP |
| I-5 | **検証未完了α/β/γ の Phase B subtask 化**: 検証未完了3項目を `subtask_1441i_verify_α/β/γ` として Phase B で軍師/足軽に明示的に割当。dateRange bug は git blame で根因コード特定→patch PR | 今週 | MED | 事故防止 | IN5-7 解決。別枠放置を解消 |
| I-6 | **三層アーキテクチャ明文化**: 足軽5号 E-8 案と連動し `shared_context/memory_architecture.md` を作成。cmem=自動ログ・MCP=明示ルール・MEMORY.md=常時ロードindex の役割分担を合意形成 | 今週 | LOW | 事故防止 | IN8 解決。cmem稼働後の3層重複蓄積を予防 |
| I-7 | **mem-search 使用計測とフィードバック**: `/home/murakami/.claude/projects/.../memory/` に `mem_search_usage.log` を作り、各エージェントの検索頻度/hit率を記録。週次でdashboardに「今週 mem-search N回実行・hit率X%」を表示 | 来月 | MED | 運用改善 | cmemの実利用度を可視化。利用率低ければ Session Start 組込の強化・UI改善（wrapper enhancement）に接続 |

**最優先3件**（Phase B 推奨）:
- **I-1**（todolist現状反映）: 5分で終わる即効タスク。現状の齟齬を解消してPhase2の残タスクを正確化
- **I-5**（α/β/γ の subtask 化）: 検証未完了を別枠放置せず Phase B 実行レーンに載せる
- **I-6**（三層アーキ文書化）: 足軽5号 E-8 と連動し、cmem稼働後の重複事故を事前予防

---

# 4. 3カテゴリ横断の統合アイデア（g+h+i）

| # | 横断案 | 関連カテゴリ | 効果 |
|---|-------|-------------|------|
| X-1 | **Phase B `subtask_1441_*` 発令時の target_path 必須化**（H-1 実装と同時） | h + Phase A 全カテゴリ | cmd_1441 で全足軽が遭遇したブロック問題を次 Phase で再発させない |
| X-2 | **MCN送信後・スキル化実装後・cmem検証完了後 それぞれに `/schedule` で30日後フォローアップ登録** | g + h + i | 送信/実装後の「結果確認忘却」を全部 schedule で予防（G-7/H-2/I-7 共通原則） |
| X-3 | **殿要承認事項を dashboard.md 🚨 に自動集約するバッチ**（weekly cron） | g + h + i | MCN可否・skill承認・cmem運用方針は殿判断項目が多い。毎週朝に 🚨セクションへ一覧化 |

---

# 5. Phase B 統合時の申し送り

- **(g)** は内容作業よりも「送信チャネル確定」がブロッカー。G-1 を `subtask_1441g_channel` として Phase B 最優先 subtask 化推奨
- **(h)** は H-1(pretool恒久修正) が最速の事故防止策。Phase A の hotfix 多発事実がエビデンスとして強力で、殿承認取得が容易なはず
- **(h)** の H-6 skill化サージは 5 skill × 半日 = 2.5人日。idle 足軽（3号/5号）に前倒し着手可能（家老1440代 subtask 化）
- **(i)** は **I-1** を即実行（5分）して todolist 齟齬を解消→ Phase2残タスクを確実に消化可能状態へ
- **三層アーキ(I-6)** は足軽5号 E-8 と内容重複のため、Phase B で軍師が「統合版 memory_architecture.md」として1本化すべき（同じ文書を2人が書く非効率を避ける）
- 本ghi カテゴリは **実装コスト中〜低**・Phase B で subtask 10-15本に分解可能（家老命名候補: `subtask_1441g_{channel/trace/qc}` / `subtask_1441h_{pretool/kanban/surge}` / `subtask_1441i_{todolist/sessionstart/arch}`）
- **target_path フィールド付与の先例**: 本タスク着手時点でタスクYAMLに `target_path: /home/murakami/multi-agent-shogun/work/cmd_1441/ideas/ashigaru7_ghi.md` が付与済で pretool_check.sh の BLOCK を回避できた（家老の Phase A 中盤以降の運用改善）。Phase B では家老が全subtaskにtarget_path明記すべき

---

# 6. 足軽7号からの追加確認事項

- **ドズル社ガイドライン原文URL/PDF** の所在を殿に確認したい（本文起草時に直接引用したいが `projects/dozle_kirinuki/context/` 配下に見当たらず）
- **`/schedule` の cron ルーチン追加権限**: ashigaru が `/schedule` 直接登録可能か、karo 経由が必須か運用ルール未確認
- **skill_candidate 横断棚卸し の自動化権限**: `queue/reports/` を週次 grep するバッチは家老/足軽どちらの責務かを Phase B 発令時に明確化されたし
