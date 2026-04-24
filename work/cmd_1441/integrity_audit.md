# cmd_1441 Phase B 統合: integrity_audit.md

軍師統合版。Phase A 全 9ファイル（ashigaru1-7 + gunshi_j + shogun_horizontal）を突合し、重複統合・優先度付け・3軸評価(コスト/効果/リスク)を付与。Phase C 発令用の execution_plan.md とセット。

- **作成**: 2026-04-24 / gunshi (subtask_1441_phaseB)
- **Phase A 入力**: ashigaru1_a.md(9) + ashigaru2_b.md(7) + ashigaru3_c.md(10) + ashigaru4_d.md(7) + ashigaru5_e.md(8) + ashigaru6_f.md(8) + ashigaru7_ghi.md(22=g7+h8+i7) + gunshi_j.md(18) + shogun_horizontal.md(32=横断観点) **計 121 raw ideas**
- **統合後**: 重複・同根を束ね **28 subtask 候補** に集約 → execution_plan.md で Wave1/2/3 に配列
- **評価軸**: 優先度=緊急度(今夜/今週/2週内/来月) / 実装コスト(LOW<30min / MED<2h / HIGH半日+) / 効果(視聴者価値/事故防止/運用改善/QoL) / リスク

---

## 1. カテゴリ別棚卸し（9カテゴリ + j 横断 = 10カテゴリ）

### (a) dashboard 🚨 棚卸し（足軽1号 / 9案）
- **A-1** skill-candidate-tracker スキル化 → **(h) H-2/H-3 と統合** (Kanban型 lifecycle)
- **A-2** dozle_kirinuki submodule gcloud-sdk履歴書換 → **独立HIGH**・殿承認必須
- **A-3** Day6 charlotte vp9→h264 事前トランスコード → **(f) F-1 と統合**
- **A-4** target_path checklist 恒久化 → **(h) H-1/H-5 と統合** (pretool_check 恒久修正と同根)
- **A-5** bloom_routing 参照破綻是正 → **(d) G1 と統合**・殿判断要(A1-a復活 vs A1-b削除)
- **A-6** part_info.json oo_men誤記修正 → **独立LOW** (Day6 MIX 前提)
- **A-7** skill-creator whitelist 工程組込 → **(h) と統合** (skills/ 運用改善)
- **A-8** dashboard 🚨 lifecycle 自動化 → **(j) テーマ5-2 と統合**
- **A-9** .gitignore work/ 運用方針決定 → **(c) C-9 と統合**

### (b) cmd done化漏れ（足軽2号 / 7案）
- **B-1** shogun_to_karo.yaml status 一括更新 5件 (1393/1412/1417/1420/1424) → **即実行可・LOW**・Wave1 最速
- **B-2** cmd_1348 救出 (gitignore whitelist + git commit + done化) → **独立LOW**・Wave1
- **B-3** ntfy🎬完了→YAML status 自動done hook → **独立MED**・仕組化
- **B-4** YAML lint (PreToolUse 重複status検知) → **独立LOW**・仕組化
- **B-5** dashboard_archive ↔ shogun_to_karo.yaml 整合性 nightly → **独立MED**
- **B-6** on_hold/pending 自動 escalation cron → **独立MED**
- **B-7** 救出メタcmd の自動close リンク (resolves_cmd) → **独立LOW**

### (c) ファイル蓄積整理（足軽3号 / 10案）
- **C-1** handoff_transcripts_prune (1.8GB削減) → **独立MED**・Wave1
- **C-2** work/cmd_1424 9.3GB 回収 → **Wave1 最優先**・殿承認 LOW
- **C-3** handoff_md_rotate → **独立MED**
- **C-4** reports_yaml_rotate → **独立MED**
- **C-5** tasks_yaml_archive (CLAUDE.md手動ルール自動化) → **独立MED**
- **C-6** disk_watchdog.sh + cron → **独立LOW**・Wave1
- **C-7** 既存cmd_rotate/dashboard_rotate を precompact_hook 自動起動 → **独立LOW**・Wave1
- **C-8** scripts/archive/ 空ディレクトリ用途明示 → LOW・来月
- **C-9** work/ 直下散乱の _tmp/ 集約ルール → **(a) A-9 と統合**
- **C-10** shared_context/disk_retention_policy.md 一枚集約 → C-1〜C-7 完了後

### (d) 設計書・instructions 棚卸し（足軽4号 / 7案 G1-G7）
- **G1 (P0)** bloom_routing 参照破綻 → **(a) A-5 と統合**・**殿判断必須**(A1-a復活 vs A1-b削除、推奨A1-b)
- **G2-G3 (P1)** instructions/{generated,cli_specific,common,roles}/ 26 file 死木 → **独立MED**・archive化
- **G4 (P2)** WhisperX 言及に「AssemblyAI移行済」注記追記 → **独立LOW**
- **G5 (P2)** panel_review_claude_gen.md モデル名 4-6→4-7 統一 → **独立LOW**
- **G6 (P2)** advisor_proxy_design.md にサブスク前提明記 → **独立LOW**
- **G7 (P2)** MEMORY.md 292行（上限超過懸念）→ **(e) E-2 と統合**

### (e) memory 整理（足軽5号 / 8案）
- **E-1** memory/archive/ 新設 + hlsh_selection 8件 + png 4枚退避 → **独立LOW**・Wave1
- **E-2** MEMORY.md core/*.md 分割 → **独立MED**・**(d) G7 と統合**
- **E-3** MEMORY.md フォーマット統一スキーマ → E-2 と同時
- **E-4** MCP add_observations 呼出タイミング shogun.md 明文化 → **独立LOW**
- **E-5** memory/ 月次棚卸し cmd 定例化 → **独立LOW**・来月
- **E-6** 3D系11 entities を memory/3d_context.md 集約 + MCP 削除 → **独立HIGH**・殿承認要(可逆性担保)
- **E-7** feedback 重要教訓を MCP entity に昇格 → E-4 後続
- **E-8** 三層アーキ(cmem/MCP/MEMORY.md) 文書化 → **(i) I-6 と統合**・独立LOW・今夜

### (f) 動画系積残（足軽6号 / 8案）
- **F-1** charlotte vp9→h264 事前トランスコード → **(a) A-3 統合済**・**Day6 MIX blocker**
- **F-2** 過去DoZ編 HL/SH候補一括選定 (集合知 /collective-select 5本) → **独立HIGH**・今週
- **F-3** TNT 20260421 漫画ショート2本 /manga-short 完走 → **Wave1 最優先今夜**
- **F-4** work/ 退避候補リスト作成 (514GB→300GB目標) → **(c) 関連**・LOW
- **F-5** cmd_1412 on_hold 再提示テンプレ → **独立LOW**・殿判断要
- **F-6** 20260417 panels 11バリアント剪定 + 命名規約 → **独立MED**・今週
- **F-7** Day6 MIX 優先区間指定 workflow md → **独立LOW**・F-1と対
- **F-8** 動画系バックログ集計ビュー → **独立MED**・来月

### (g) MCN申請 v2（足軽7号 / 7案）
- **G-1** 送信チャネル確定 + 窓口特定 → **Wave2 最優先ブロッカー**・殿判断要(ガイドラインURL/メール)
- **G-2** 実績証跡リンクブロック追加 → LOW・G-1 後
- **G-3** ガイドライン遵守表に根拠URL併記 → MED
- **G-4** 軍師QCゲート (v1→v2校閲) → **独立LOW**・送信前必須
- **G-5** AI画像生成 3段構え提案化 → LOW
- **G-6** 他チャンネルMCN加入事例リサーチ3件 → **独立MED**・足軽並列可
- **G-7** 30日無応答再送 /schedule 登録 → LOW・送信後

### (h) スキル化候補 積残（足軽7号 / 8案）
- **H-1** pretool_check 恒久修正 skill化 → **Wave1 事故防止最優先**・Phase A 4人 hotfix の ROI 突出・**(a) A-4 / C-1 と統合**
- **H-2** skill_candidate 棚卸しレポート自動生成 → **独立MED**
- **H-3** shared_context/skill_kanban.md (4レーン管理) → H-2 と対
- **H-4** skills/ 棚卸し (_audit.md) → 来月MED
- **H-5** pretool_check target_path 欠落で家老inbox アラート → H-1 同時 LOW
- **H-6** 塩漬けskill 5件(C3/C4/C7/C8/C10) 一括実装サージ → **独立HIGH**・今週・足軽並列
- **H-7** skill_candidate フィールド必須化バリデータ → **独立LOW**
- **H-8** skill 承認判定テンプレ (再発3回+横断+1h実装) → 来月LOW

### (i) cmem todolist Phase2/3（足軽7号 / 7案）
- **I-1** todolist.md 現状反映 (Phase1 C/J/D/K ✅化) → **Wave1 5分タスク**・即実行
- **I-2** Phase2 G: Session Start に cmem 参照追加 → **独立LOW**・家老/将軍 instructions 更新
- **I-3** Phase2 A: cmd発令前検索の閾値ルール明文化 → **独立LOW**
- **I-4** Phase2 B: senkyou skill 改修 → **独立MED**
- **I-5** 検証未完了 α/β/γ の subtask 化 (dateRange bug / semantic / SKIP_TOOLS) → **独立MED**
- **I-6** 三層アーキ memory_architecture.md → **(e) E-8 と統合**・1本化
- **I-7** mem-search 使用計測とフィードバック → 来月MED

### (j) 横断・軍師（軍師 / 6テーマ 18案）
- **J-テーマ1** severity数値化 / 冪等性チェック項目 / QC schema統一 / verification_method追加 → **独立MED**
- **J-テーマ2** Opus[1m]観測ダッシュボード / claude-mem dateRange bug 回避ガイド → **Wave1 今夜ウィンドウ**・ /I-5 と統合 (β/γも)
- **J-テーマ3** cron インベントリ / kill_orphan_chrome 頻度見直し / cron失敗検知 → **独立MED**
- **J-テーマ4** feedback rule 四半期レビュー cron / test coverage / E2E再現pack → (e)(h) と連動LOW
- **J-テーマ5** ntfy wrapper 統一 / 🚨 auto-prune / ntfy 失敗fallback → **(a) A-8 と統合**・MED
- **J-テーマ6** 殿 precondition 欄 / 設計レビュー後殿ゲート必須化 → **独立LOW**

### shogun_horizontal (横断補完 / 8分類 32項目)
- **将軍 3-A** disk cleanup (Day6 MIX前提) → **(c) C-2/C-1 と統合**・Wave1
- **将軍 3-B** dozle submodule push対策 → **(a) A-2 と統合**・Wave2
- **将軍 6-A** Opus[1m] 観測ウィンドウ → **(j) J-テーマ2 と統合**・Wave1 **今夜限定**
- **将軍 1-D** MCP化石化 → **(e) E-6 と統合**
- **将軍 5-A/5-C** shared_context棚卸し / feedback 月次レビュー → (j) テーマ4 と統合
- **将軍 8-C** クォータ消費ペース観測機構 → J-テーマ2 と統合
- **将軍 2-B** 完了後 curl 目視確認 memory化 → **独立LOW**・MEMORY.md 反映済 (2026-04-23 教訓)
- **将軍 4-A** MCN申請文 v1 殿レビュー → **(g) と統合**
- その他の軽微項目は 2-A/2-C/2-D/4-B/4-C/4-D/4-E/5-B/5-D/6-B/6-C/6-D/7-A/7-B/7-C/7-D/8-A/8-B/3-C/3-D/3-E/1-A/1-B/1-C → Phase B 統合対象外(小粒・来月以降)

---

## 2. 重複統合マップ（121 raw ideas → 28 subtask 候補）

| 統合後 subtask 種子 | 構成 raw ideas | 出所カテゴリ |
|---------------------|----------------|--------------|
| **S01** cmd一括 done化 | B-1 | (b) |
| **S02** cmd_1348 救出 | B-2 | (b) |
| **S03** work/cmd_1424 9.3GB 回収 | C-2 + 将軍3-A | (c)+将軍 |
| **S04** handoff_transcripts prune 1.8GB | C-1 | (c) |
| **S05** disk_watchdog + 既存rotate自動起動 | C-6 + C-7 | (c) |
| **S06** tasks/reports/handoff YAML archive 3本立て | C-3 + C-4 + C-5 + 将軍3-E | (c)+将軍 |
| **S07** TNT漫画ショート2本完走 | F-3 | (f) |
| **S08** charlotte vp9→h264 + Day6 MIX workflow | A-3 + F-1 + F-7 | (a)+(f) |
| **S09** part_info.json oo_men誤記修正 | A-6 | (a) |
| **S10** 20260417 panels 剪定 + 命名規約 | F-6 | (f) |
| **S11** pretool_check 恒久修正 + target_path checklist + alert | A-4 + H-1 + H-5 + H-7 | (a)+(h) |
| **S12** skill-candidate-tracker + Kanban + 棚卸し自動化 | A-1 + H-2 + H-3 | (a)+(h) |
| **S13** skills/ whitelist 運用改善 + skill-creator 工程組込 | A-7 + A-9 + C-9 | (a)+(c) |
| **S14** 塩漬けskill 5件 実装サージ | H-6 | (h) |
| **S15** dashboard 🚨 lifecycle + ntfy wrapper 統一 | A-8 + J-5 | (a)+(j) |
| **S16** bloom_routing 整流化 | A-5 + G1 | (a)+(d) |
| **S17** instructions/{generated,cli_specific,common,roles}/ archive化 | G2 + G3 | (d) |
| **S18** ドキュメント軽微修正群 (WhisperX注記・4-7統一・advisor前提明記) | G4 + G5 + G6 | (d) |
| **S19** memory/archive/ 新設 + hlsh/png退避 | E-1 | (e) |
| **S20** MEMORY.md core分割 + スキーマ統一 | E-2 + E-3 + G7 | (d)+(e) |
| **S21** MCP 3D entity 集約 + 観察昇格仕組み | E-4 + E-6 + E-7 | (e) |
| **S22** 三層アーキ memory_architecture.md | E-8 + I-6 | (e)+(i) |
| **S23** cmem todolist 現状反映 + Phase2 3案 | I-1 + I-2 + I-3 + I-4 | (i) |
| **S24** claude-mem 検証未完了 α/β/γ + Opus[1m]観測 | I-5 + J-2 + 将軍6-A/8-C | (i)+(j)+将軍 |
| **S25** MCN v2 (送信チャネル確定+証跡+軍師QC+他社リサーチ+schedule再送) | G-1〜G-7 | (g) |
| **S26** dozle_kirinuki submodule gcloud-sdk 履歴書換 | A-2 + 将軍3-B | (a)+将軍 |
| **S27** cmd_1412 on_hold 再提示テンプレ | F-5 | (f) |
| **S28** 軍師QC基盤強化 (severity数値化/冪等性/schema/verification_method) | J-1 + J-3 + J-4 + J-6 | (j) |

**残raw (統合対象外・Phase C以降の別cmd候補)**:
- (b) B-3〜B-7 (仕組化 5件): ntfy→status自動化 / YAML lint / archive整合 / on_hold escalation / resolves_cmd → 来月 cmd_XXXX で一本化
- (c) C-8/C-10: 軽微整理・来月
- (f) F-2 過去DoZ HL/SH選定5本・F-4 退避リスト・F-8 バックログビュー → Wave3 後続
- (h) H-4 skills/_audit / H-8 承認判定テンプレ → 来月
- (i) I-7 mem-search使用計測 → 来月

---

## 3. 優先度マトリックス（高/中/低 × 緊急度）

| 優先度 \ 緊急度 | 今夜(観測ウィンドウ限定含む) | 今週 | 2週内 | 来月 |
|-----------------|------------------------------|------|-------|------|
| **高** | S07 TNT漫画 / S03 disk 9.3GB / S24 Opus観測 | S08 Day6 MIX基盤 / S11 pretool恒久 / S01 cmd一括done / S16 bloom_routing | S25 MCN v2 / S26 submodule履歴書換 | — |
| **中** | S22 三層アーキ / S23 todolist反映 | S04 transcripts prune / S05 disk_watchdog / S12 skill-candidate-tracker / S14 塩漬けskill サージ / S17 instructions archive / S19 memory/archive/ / S20 MEMORY.md core分割 / S27 cmd_1412再提示 | S09 part_info修正 / S10 panels剪定 / S15 dashboard lifecycle / S21 MCP観察昇格 / S28 QC基盤強化 | S06 YAML archive 3本立て |
| **低** | — | S02 cmd_1348救出 / S13 skills whitelist改善 / S18 ドキュメント軽微 | — | — |

**今夜限定ウィンドウ (Anthropic週次リセット直後・明日朝殿クォータリセット)**:
- **S07 TNT漫画ショート2本完走** (即着手可・殿モチベ向上)
- **S24 Opus[1m] 観測ダッシュボード** (今夜のみ基準値取得可能)
- **S22 三層アーキ memory_architecture.md** (cmd_1440 連動・衝突予防)
- **S23 cmem todolist 現状反映** (5分タスク)

---

## 4. 3軸評価（実装コスト / 効果 / リスク）

| subtask | コスト | 効果 | リスク | 備考 |
|---------|--------|------|--------|------|
| S01 cmd一括done化 | LOW(15min) | 運用改善(状態正常化) | LOW | YAML Edit のみ |
| S02 cmd_1348 救出 | LOW(30min) | 運用改善 | LOW | gitignore whitelist+commit+done |
| S03 work/cmd_1424 9.3GB回収 | LOW(15min) | 事故防止(Day6 MIX前提) | **殿承認必要** | 削除前`du -sh`確認 |
| S04 transcripts prune | MED(1-2h) | 運用改善(1.8GB削減) | LOW | claude-mem依存不在確認済 |
| S05 disk_watchdog+rotate起動 | LOW(1h) | 事故防止 | LOW | crontab追加 |
| S06 YAML archive 3本立て | HIGH(6h) | QoL(token節約) | MED | 多ファイル編集・バッチ化要 |
| S07 TNT漫画完走2本 | MED(1-2h) | 視聴者価値 | LOW | 既存skill /manga-short |
| S08 charlotte トランスコード+Day6 MIX | MED(3-4h) | 視聴者価値 | MED | NVENC GPU所要・concat検証 |
| S09 part_info.json修正 | LOW(10min) | 事故防止 | LOW | JSON edit 1箇所 |
| S10 panels剪定+命名規約 | MED(2h) | 事故防止 | LOW | git mv + md制定 |
| S11 pretool恒久修正 | LOW(1h) | 事故防止(Phase A 4人hotfix ROI突出) | LOW | 1行修正+unit test |
| S12 skill-candidate-tracker | MED(2-3h) | 運用改善 | LOW | cron+skill作成 |
| S13 skills whitelist運用改善 | MED(1-2h) | 事故防止 | LOW | .gitignore + skill-creator md更新 |
| S14 塩漬けskill 5件サージ | HIGH(2.5人日) | QoL | MED | 足軽並列3人で1週間 |
| S15 dashboard lifecycle+ntfy統一 | MED(2-3h) | 運用改善 | LOW | hook+wrapper |
| S16 bloom_routing整流化 | LOW(30min) | 事故防止 | **殿判断要**(復活vs削除) | karo.md/CLAUDE.md編集 |
| S17 instructions 26file archive | MED(1h) | QoL | LOW | git mv 履歴保持 |
| S18 ドキュメント軽微修正群 | LOW(30min) | 事故防止 | LOW | 3箇所 edit |
| S19 memory/archive/ 新設 | LOW(30min) | QoL | LOW | git mv |
| S20 MEMORY.md core分割 | MED(2h) | QoL | **殿確認要**(structure変更) | shogun.md Session Start 更新同期 |
| S21 MCP 3D entity集約 | HIGH(半日) | QoL | **殿承認必要**(削除可逆性) | snapshot → 全文転記 → 削除順 |
| S22 三層アーキ md作成 | LOW(1h) | 事故防止 | LOW | 単ファイル |
| S23 cmem todolist反映+Phase2 3案 | LOW-MED(1h) | 運用改善 | LOW | md更新+instructions追記 |
| S24 α/β/γ検証+Opus観測 | MED(2-3h) | 運用改善 | LOW | 検証別枠化・観測cron |
| S25 MCN v2 一式 | MED-HIGH(半日) | 交渉優位/事故防止 | **殿承認必要**(送信前全項) | 送信チャネル確定が最大blocker |
| S26 dozle submodule履歴書換 | HIGH(1日) | 運用改善 | **HIGH**(殿承認+backup+force-with-lease) | 共同作業者なし確認 |
| S27 cmd_1412 再提示テンプレ | LOW(30min) | 運用改善 | LOW | md作成 |
| S28 QC基盤強化 | MED(2-3h) | 事故防止 | LOW | qc_template.md 追記 |

---

## 5. Wave 分離（execution_plan.md との対応）

- **Wave 1 (殿ゲート不要・即実行可)**: S01・S02・S03(殿即答LOW)・S04・S05・S07・S11・S19・S22・S23・S24
- **Wave 2 (殿判断ゲート要)**: S08(Day6 MIX前提合意)・S09・S10・S13・S16(復活vs削除)・S17・S18・S20・S21・S25 MCN v2・S26 submodule履歴書換・S27 cmd_1412再提示・S28
- **Wave 3 (Wave2 依存)**: S06(YAML archive 運用方針決定後)・S12(skill-candidate lifecycle)・S14(塩漬けskill サージ)・S15(dashboard lifecycle)・F-2過去DoZ HL/SH選定・F-8 バックログビュー

---

## 6. Phase A → Phase B 引継ぎメモ

1. **target_path 付与運用**: Phase A 中盤以降、家老が subtask YAML に `target_path: work/cmd_1441/ideas/ashigaru{N}_{x}.md` を付与する運用に改善。Phase C 発令時は **全 subtask に target_path 必須**（S11 で恒久修正化）
2. **新規.py 禁止ルール**: Phase A 完全遵守。Phase C も同じく既存skill/script活用のみ
3. **Phase A 全成果物 git commit 済**: commit IDs = 040ff46(f) / 233f9aa(b) / 56ede22(j) 等
4. **軍師自己反省**: qc_1425d2 時点で part_info.json oo_men実存を見落とし → S09 で自己申告 + S28 QC基盤強化に反映
5. **良循環サイクル 3件継続**: (i) qc_1425c2→cmd_1439 yt-dlp-js-runtimes-fix skill化 (ii) cmd_1436 K→cmd_1440 D cmem_search.sh (iii) cmd_1436 J→cmd_1440 J WORKER_HOST=0.0.0.0
6. **pretool_check hotfix 4人独立発明**: 足軽 2/3/4/5 号が同じ workaround を発明 → S11 ROI 突出の根拠
7. **disk 88%**: Day6 MIX 200GB+ 消費見込みの直前に残 116GB → S03 即回収で 9.3GB 解放 + S04 で 1.8GB 追加 = 合計 11GB 即時確保可能

---

## 7. 北極星アラインメント

- **North Star**: ドズル社切り抜きチャンネル質・効率の両立（Day6 MIX 高品質制作・MCN加入・収益化見据え）
- **整合性**:
  - Wave1 S07 TNT漫画完走 → 投稿数増 (直接寄与)
  - Wave1 S03/S04/S05 disk cleanup → Day6 MIX 前提条件 (視聴者価値)
  - Wave1 S22/S23/S24 cmem観測基盤 → 運用効率向上 (間接寄与)
  - Wave2 S08 Day6 MIX 基盤 → 4視点MIX という差別化コンテンツ (視聴者価値)
  - Wave2 S25 MCN v2 → 公式認定 (収益化基盤)
- **リスク**:
  - S26 submodule 履歴書換失敗 → 12 commits消失リスク (backup必須)
  - S21 MCP 3D entity 削除不可逆 → snapshot + 全文転記手順必須
  - Wave1 Opus[1m] 観測ウィンドウ今夜限定 → S24 先行実装必須
  - MCN v2 送信チャネル未確定 → S25 ブロッカーで送信ラグ発生中
- **自己評価**: **aligned** - Phase C 発令で北極星方向への加速が得られる

---

以上、28 subtask 候補の統合整理を完了。execution_plan.md にて Wave 別 subtask 定義と並列可否判定を提示する。
