# cmd_1441 Phase C 実行計画: execution_plan.md

軍師統合版。integrity_audit.md の 28 subtask 候補を Wave 分離し、並列可能性・所要時間・advisor要否・git push担当を明示する。家老はこれを元に Phase C cmd を発令する。

- **作成**: 2026-04-24 / gunshi (subtask_1441_phaseB)
- **前提**: Phase A 9ファイル読了 → integrity_audit.md 28 subtask 統合完了
- **入力**: work/cmd_1441/integrity_audit.md
- **採用方針**: Wave 1 (殿ゲート不要) → Wave 2 (殿判断ゲート要) → Wave 3 (Wave2 依存) の3段構え

---

## 1. Wave 分離方針

| Wave | 条件 | 発令タイミング |
|------|------|----------------|
| **Wave 1** | 殿承認不要 or LOW-risk な即答で済む案件 (例: 中間動画削除の即答Yes/No) | Phase B 完了後、家老が即発令 (今夜〜明日) |
| **Wave 2** | 殿判断ゲート必要 (復活/削除・送信・履歴書換等) | 殿への提示 → 回答後に家老が発令 |
| **Wave 3** | Wave 2 完了依存・skill サージ・運用仕組化 | 今週後半〜来週 |

**時間窓クリティカル (今夜限定)**:
- **S07 TNT 漫画ショート完走** (Opus 週次リセット直後・足軽1号 or 2号 idle なら即着手)
- **S24 Opus[1m] 観測ダッシュボード** (基準値取得は今夜のみ)

---

## 2. Wave 1 （殿ゲート不要・即発令可・計11件）

| subtask_id | 種子 | 担当候補 | 依存 | 並列可否 | 所要時間 | advisor | git push | 成果物 |
|-----------|------|---------|------|---------|---------|---------|---------|-------|
| subtask_1441_p01 | **S01 cmd一括 done化 (5件)** | 足軽2号 | なし | 直列 (shogun_to_karo.yaml 単一編集) | 15min | 実装前のみ | 家老 | shogun_to_karo.yaml status更新 |
| subtask_1441_p02 | **S02 cmd_1348 救出** | 足軽2号 | p01 後 | 直列 (同yaml編集) | 30min | 実装前のみ | 家老 | .gitignore + dingtalk_qc_loop.py tracked + yaml done |
| subtask_1441_p03 | **S03 work/cmd_1424 9.3GB 回収** | 足軽3号 | 殿一問即答(削除OK?) | 並列可 (work/配下のみ) | 15min | 不要 (削除前du -sh) | 家老 | work/cmd_1424/ 中間動画削除・dashboard記載 |
| subtask_1441_p04 | **S04 handoff_transcripts prune** | 足軽3号 | なし | 並列可 | 1-2h | 実装前後 | 家老 | scripts/handoff_transcripts_prune.sh + crontab |
| subtask_1441_p05 | **S05 disk_watchdog + 既存rotate自動起動** | 足軽3号 | p04 後 | 並列可 (別script) | 1h | 実装前後 | 家老 | scripts/disk_watchdog.sh + precompact_hook 改修 |
| subtask_1441_p06 | **S07 TNT漫画ショート2本完走** | 足軽6号 or 1号 | なし | 直列 (同 /manga-short 工程) | 1-2h | 実装前後必須 | 家老 | panels_960_1080_shogun_v3_edited.json 合成 + asobunokinshi 合成 + YouTube 非公開アップ2件 |
| subtask_1441_p07 | **S11 pretool_check 恒久修正 + target_path checklist + alert** | 足軽4号 | なし | 直列 (pretool_check.sh 単一編集) | 1h | 実装前後必須 | 家老 | scripts/pretool_check.sh regex 拡張 + unit test + instructions/karo.md 5点セット化 |
| subtask_1441_p08 | **S19 memory/archive/ 新設 + 退避** | 足軽5号 | なし | 並列可 (memory/ 単独) | 30min | 実装前のみ | 家老 | memory/archive/{hlsh,images}/ + MEMORY.md リンク更新 |
| subtask_1441_p09 | **S22 三層アーキ memory_architecture.md** | 足軽5号 or 軍師 | p08 後 (同領域編集回避) | 並列可 (新規md) | 1h | 実装前後必須 | 家老 | shared_context/memory_architecture.md (cmem/MCP/MEMORY.md 役割分担) |
| subtask_1441_p10 | **S23 cmem todolist 反映 + Phase2 3案 (G/A/B)** | 足軽7号 | なし | 直列 (todolist.md 単一編集) → 並列 (instructions/shogun.md + karo.md + senkyou skill) | 1h | 実装前後必須 | 家老 | work/cmd_1436/todolist.md 更新 + instructions 2ファイル edit + senkyou skill 改修 |
| subtask_1441_p11 | **S24 α/β/γ検証 + Opus[1m] 観測ダッシュボード** | 足軽5号 (α/β/γ) + 軍師 (観測設計) | なし | 並列可 (観測は cron のみ) | 2-3h | 実装前後必須 | 家老 | scripts/opus_observation.sh + crontab + α/β/γ 検証report + feedback_claude_mem_daterange_broken.md |

### Wave 1 並列グループ判定

**並列グループA (同時走行可能・最大6並列)**:
- p01→p02 直列ペア (足軽2号単独)
- p03 (足軽3号 work/)
- p06 (足軽6号 /manga-short)
- p07 (足軽4号 scripts/pretool_check)
- p08 (足軽5号 memory/)
- p10 (足軽7号 work/cmd_1436/)

**直列依存**:
- p04 → p05 (足軽3号、transcripts→watchdog の順)
- p08 → p09 (memory/ 領域重複回避のため順次)

**同時実行推奨 (今夜)**:
- **最速優先**: p06 TNT完走 + p11 Opus観測設計 + p01+p02 cmd done化 を 並列発令
- p07 pretool恒久は Phase B→C 境界で優先度高

---

## 3. Wave 2 （殿判断ゲート要・計13件）

殿への提示形式: 家老が dashboard.md 🚨要対応 に「Phase B 統合完了 / Phase C 発令候補 / 殿判断事項 N 件」を書き、ntfy 通知で一括提示。

| subtask_id | 種子 | 担当候補 | 殿判断事項 | 依存 | 並列可否 | 所要時間 | advisor | git push | 成果物 |
|-----------|------|---------|-----------|------|---------|---------|---------|---------|-------|
| subtask_1441_p12 | **S08 charlotte トランスコード + Day6 MIX workflow** | 足軽6号 | Day6 MIX の優先区間(3分×3箇所等)決定 | p03 disk 確保後 | 並列可 (新規work/cmd_XXXX/) | 3-4h | 実装前後必須 | 家老 | charlotte_h264/*.mp4 + shared_context/procedures/day6_mix_workflow.md |
| subtask_1441_p13 | **S09 part_info.json oo_men誤記修正** (軍師 qc_1425d2 見落とし是正の self-申告を subtask description に残す・実装は足軽側) | 足軽5号 (cmd_1425d2 元担当) | 不要 (軽微 edit) | なし | 並列可 | 10min | 実装前のみ | 家老 | part_info.json edit + gunshi_report_qc_1425d2 update-note |
| subtask_1441_p14 | **S10 20260417 panels 剪定 + 命名規約** | 足軽2号 or 7号 | cmd_1413 採用 / 1411 却下の再確認 | なし | 並列可 (該当フォルダ) | 2h | 実装前後必須 | 家老 | panels/_deprecated/ 移動 + 命名規約md |
| subtask_1441_p15 | **S13 skills whitelist 運用改善** | 足軽1号 | .gitignore whitelist vs skills/ 全体tracked 方針 | なし | 直列 (.gitignore 単一編集) | 1-2h | 実装前後必須 | 家老 | .gitignore batch 更新 + skills/skill-creator/SKILL.md 工程追加 |
| subtask_1441_p16 | **S16 bloom_routing 整流化** | 足軽4号 (発見元) | A1-a 復活 vs A1-b 削除 (推奨 A1-b) | なし | 並列可 (config + md) | 30min | 実装前のみ | 家老 | config/settings.yaml 追記 or karo.md/CLAUDE.md 該当削除 |
| subtask_1441_p17 | **S17 instructions/{generated,cli_specific,common,roles}/ archive化** | 足軽4号 | archive化OK? (git mv で履歴保持) | p16 後 (同領域編集回避) | 直列 | 1h | 実装前のみ | 家老 | instructions/archive/202603/ + CLAUDE.md 参照修正 |
| subtask_1441_p18 | **S18 ドキュメント軽微修正群 (WhisperX/4-7/advisor前提)** | 軍師 or 足軽4号 | 不要 (軽微) | なし | 並列可 (3ファイル別) | 30min | 不要 | 家老 | 3md edit 1commit |
| subtask_1441_p19 | **S20 MEMORY.md core 分割 + スキーマ統一** (軍師は設計レビュー・QCのみ、実装は足軽側) | 足軽5号 | Session Start 変更可否 (shogun instructions 連動) | p08 (memory/archive) 後 | 直列 | 2h | 実装前後必須 | 家老 | memory/core/{rules,projects,cli,knowledge}.md + MEMORY.md 減量 + shogun.md 更新 |
| subtask_1441_p20 | **S21 MCP 3D entity 集約 + 観察昇格仕組み** | 足軽5号 | 削除可逆性担保手順承認 (snapshot→転記→削除) | p19 後 | 直列 (MCP 操作) | 半日 | 実装前後必須 | 家老 | mcp_snapshot_YYYYMMDD.json + memory/3d_context.md 全文転記 + delete_entities 実行 |
| subtask_1441_p21 | **S25 MCN v2 一式 (送信チャネル〜軍師QC〜schedule)** | 足軽7号 + 軍師QC + 殿 | ガイドラインURL/PDF提供 + 送信先確定 + AI3段構え承認 + 送信タイミング | なし | 直列 (承認ゲート多段) | 半日 | 実装前後必須 | 家老 (送信は殿自身) | application_draft_v2.md + 遵守表URL併記 + 他社リサーチmd + 30日後 /schedule 登録 |
| subtask_1441_p22 | **S26 dozle_kirinuki submodule 履歴書換** | 足軽4号 | 書換OK? + 共同作業者なし確認 + backup確認 + force-with-lease 承認 | なし | 並列可 (submodule 単独) | 1日 | 実装前後必須 | 家老 (force-with-lease) | filter-repo 実行 + google-cloud-sdk 0件 + origin push成功 |
| subtask_1441_p23 | **S27 cmd_1412 on_hold 再提示テンプレ** | 足軽1号 | 10分版視聴データ参照可否 | なし | 並列可 | 30min | 実装前のみ | 家老 | work/cmd_1441/phaseB_decisions/cmd_1412_recheck.md + dashboard 🚨追加 |
| subtask_1441_p24 | **S28 軍師QC基盤強化** | 軍師 | severity数値化/冪等性/schema変更承認 | なし | 並列可 (qc_template.md 単一) | 2-3h | 実装前後必須 | 家老 | shared_context/qc_template.md 追記 + qc_report_schema.yaml |

### Wave 2 殿判断ゲート一覧（ntfy 通知で一括提示想定）

| # | 殿判断事項 | 関連 subtask | 推奨 | 推奨理由 |
|---|-----------|-------------|------|----------|
| D1 | Day6 MIX 優先区間 (3分×3箇所等) | p12 | **3分×3箇所** | 9時間MIXは disk/時間ともに非現実的 |
| D2 | cmd_1413採用/1411却下の再確認 | p14 | **現状維持** | panels剪定の前提 |
| D3 | skills whitelist vs 全体tracked | p15 | **全体 tracked** | 新規skill毎の手動作業排除 |
| D4 | bloom_routing A1-a復活 vs A1-b削除 | p16 | **A1-b 削除** | 全Opus[1m]統一方針 → ルーティング不要 |
| D5 | instructions 26file archive化 OK? | p17 | **archive化** | 7週間未更新・現役参照なし |
| D6 | MEMORY.md Session Start 変更可否 | p19 | **shogun.md同期更新** | 292行の視認性改善 |
| D7 | MCP 3D entity 削除可逆性手順承認 | p20 | **snapshot+転記 必須** | 復旧手順を md 化してから削除 |
| D8 | MCN ガイドラインURL/PDF / 送信チャネル確定 / AI 3段構え承認 | p21 | **送信先確定が最優先blocker** | v1 dormant 解消 |
| D9 | dozle_kirinuki submodule 履歴書換 OK? | p22 | **backup + force-with-lease** | 12 commits 消失リスク要管理 |

**(Wave 1 は殿 LOW-risk 即答で閉じる。p03 work/cmd_1424 9.3GB 削除は「Day6 MIX 前提・中間動画のみ・.gitignore済」ゆえ Wave 1 内で家老が一問即答を取る運用で足りる。Wave 2 の D1〜D9 から除外。)**

---

## 4. Wave 3 （Wave 2 依存 or 運用仕組化・計5件 + 残 raw 4件）

| subtask_id | 種子 | 担当候補 | 依存 | 並列可否 | 所要時間 | advisor | git push | 成果物 |
|-----------|------|---------|------|---------|---------|---------|---------|-------|
| subtask_1441_p25 | **S06 tasks/reports/handoff YAML archive 3本立て** | 足軽3号 | p05 完了・殿方針決定 | 並列可 (3スクリプト) | 6h | 実装前後必須 | 家老 | scripts/{handoff_md,reports_yaml,tasks_yaml}_rotate.sh + shared_context/disk_retention_policy.md |
| subtask_1441_p26 | **S12 skill-candidate-tracker skill + Kanban** | 足軽1号 | p15 skills/運用決定後 | 並列可 | 2-3h | 実装前後必須 | 家老 | skills/skill-candidate-tracker/SKILL.md + shared_context/skill_kanban.md + weekly cron |
| subtask_1441_p27 | **S14 塩漬けskill 5件 実装サージ** | 足軽2/3/5号並列 | p26 Kanban 運用開始後 | 並列可 (5 skill 個別) | 2.5人日 | 各 skill 実装前後必須 | 家老 (5コミット) | 5スキル (C3 minecraft-skin-to-rig / C4 bigquery-embedding-batch / C7 note-edit-clipboard-png / C8 ffmpeg-amix-normalize-0 / C10 bq-max-rows-explicit) |
| subtask_1441_p28 | **S15 dashboard 🚨 lifecycle 自動化 + ntfy wrapper 統一** | 足軽5号 | p27 後 (負荷分散) | 並列可 (2script) | 2-3h | 実装前後必須 | 家老 | scripts/dashboard_alert_lifecycle.py + scripts/ntfy_send.sh |

**Wave3 残 raw (別 cmd 化候補・cmd_1441 スコープ外)**:
- B-3〜B-7 仕組化5件 (ntfy→status自動化 / YAML lint PreToolUse / archive整合 nightly / on_hold escalation / resolves_cmd) → **cmd_XXXX 運用自動化 bundle** で一括発令推奨
- F-2 過去DoZ編 HL/SH 選定 5本 → **cmd_XXXX 過去DoZ一括** で別発令 (2.5〜4時間)
- F-4 work/ 退避候補リスト → p03/p25 完了後に軽量 md 化
- F-6 軽微 (C-8/C-10, H-4/H-8, I-7, J-4) → **来月cmd**

---

## 5. 並列グループマトリックス（同時走行可能な組み合わせ）

### Wave 1 同時発令推奨セット (今夜)

```
┌────────────────────────────────────────────┐
│  Group α (今夜即着手・最大6並列)                │
├────────────────────────────────────────────┤
│  足軽1号: idle (or p23 cmd_1412 再提示)         │
│  足軽2号: p01 → p02 直列                       │
│  足軽3号: p03 (殿即答後) → p04 → p05 直列       │
│  足軽4号: p07 pretool 恒久                     │
│  足軽5号: p08 → p09 直列 or p11 Opus観測        │
│  足軽6号: p06 TNT漫画完走 ★今夜のみウィンドウ     │
│  足軽7号: p10 cmem todolist+Phase2             │
│  軍師  : p11 Opus観測設計 + p09 after        │
└────────────────────────────────────────────┘
```

### Wave 2 殿判断後の発令セット (明日以降)

```
┌────────────────────────────────────────────┐
│  Group β (殿判断後)                           │
├────────────────────────────────────────────┤
│  p12 Day6 MIX (p03 disk 確保 + D2 区間決定後)  │
│  p15/p16/p17 ドキュメント整流化 (並列可)        │
│  p18 軽微修正 (並列可)                         │
│  p19 → p20 MEMORY/MCP (直列)                 │
│  p21 MCN v2 (殿承認多段ゲート)                 │
│  p22 submodule 履歴書換 (要backup)            │
│  p23 cmd_1412 再提示 (殿判断後)              │
│  p24 QC基盤強化 (並列可)                      │
└────────────────────────────────────────────┘
```

### 同一ファイル編集の直列化

以下のファイルは複数 subtask が編集対象 → 家老が batch 化 (1 subtask に merge or 順次発令)：

| ファイル | 編集 subtask | 推奨順序 |
|---------|-------------|---------|
| `.gitignore` | p02 (dingtalk_qc_loop.py) + p15 (skills/ whitelist) | p02 → p15 (p15 で一括再整理) |
| `shogun_to_karo.yaml` | p01 (5件 done) + p02 (cmd_1348 done) + p23 (cmd_1412 記録) | p01 → p02 → p23 |
| `CLAUDE.md` | p16 (bloom_routing削除) + p17 (参照修正) + p19 (Session Start) | p16 → p17 → p19 |
| `karo.md` | p07 (5点セット) + p16 (bloom_routing) | p16 → p07 |
| `shogun.md` | p10 (cmem Session Start) + p19 (MEMORY.md 分割) + E-4 (MCP add_observations) | p10 → p19 → (p20 時 E-4 同時) |
| `memory/MEMORY.md` | p08 (archive リンク) + p19 (core 分割) | p08 → p19 |

---

## 6. advisor 要否リスト

### 必須 (実装前後 両方)
p04 / p05 / p06 / p07 / p09 / p10 / p11 / p12 / p14 / p15 / p19 / p20 / p21 / p22 / p24 / p25 / p26 / p27 / p28

### 実装前のみ
p01 / p02 / p08 / p13 / p16 / p17 / p23

### 不要
p03 (殿即答のみ) / p18 (軽微・差分小)

---

## 7. git push 担当整理

- **Wave 1/2/3 全件**: 家老 (karo) が cmd 完了時に push
- **例外**: p22 submodule 履歴書換のみ **家老 force-with-lease** (通常 push 不可)
- **足軽 git push 禁止**: 全 subtask で遵守 (F-forbidden 足軽ルール)

---

## 8. 完了条件・QC観点

### 全体完了条件 (cmd_1441)
- Wave 1 全 11 件 status=done (Phase B+C で今週中想定)
- Wave 2 発令済 & 殿判断ゲート応答済 (10件)
- Wave 3 p25/p26/p28 発令済 (来週)
- dashboard 🚨要対応 から p01〜p28 対応事項の消去 (lifecycle-1)
- dozle submodule push 成功 (p22)
- MCN v2 送信 (p21)

### 各 Wave QC観点 (軍師による品質検査)
- **Wave 1**: 実ファイル存在 / git commit / `file:line` 証跡 / テスト実行 (p06 動画アップ確認・p07 pretool_check unit test)
- **Wave 2**: 殿判断内容が subtask に反映されたか・ドキュメント整合性 (p16 bloom_routing 削除漏れなし・p17 archive 履歴保持)
- **Wave 3**: cron 起動確認 / alertライフサイクル動作 / skill サージ5件全完了

### 検証コマンド例

```bash
# p03 完了確認
du -sh /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/cmd_1424/ || echo "empty or gone"

# p07 完了確認
bash -c 'source <(grep -A5 "status:" scripts/pretool_check.sh | head)' # regex (assigned|in_progress) 存在確認

# p16 完了確認 (A1-b 採用時)
grep -r "bloom_routing" instructions/ CLAUDE.md config/ || echo "references removed"

# p22 完了確認
cd projects/dozle_kirinuki && git rev-list --objects --all | grep -c google-cloud-sdk # 0 件
```

---

## 9. 北極星アラインメント（execution_plan 視点）

- **整合性**: Wave 1/2/3 の各件は integrity_audit.md の「視聴者価値/事故防止/運用改善/QoL」いずれかで北極星(切り抜きチャンネル質・効率)に寄与
- **最大寄与**: p06 TNT完走・p12 Day6 MIX・p21 MCN v2 → 視聴者価値・収益化基盤
- **最大リスク**: p22 submodule 履歴書換失敗 / p20 MCP 3D削除不可逆 → 緩和策 = backup + force-with-lease + snapshot+転記手順
- **今夜ウィンドウ**: Opus 週次リセット直後 + 明日朝殿クォータリセット → **Wave 1 の p06/p11/p10/p11 を今夜中に走らせるべき**

---

以上、Wave 1 (11 subtask) / Wave 2 (13 subtask) / Wave 3 (4 subtask) 計 **28 subtask** を Phase C 発令用に分解整理。家老は本文書を元に cmd 化し発令されたし。
