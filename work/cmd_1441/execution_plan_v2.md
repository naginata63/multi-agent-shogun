# cmd_1441 Phase C 実行計画 v2: execution_plan_v2.md

殿2重指示反映の差し戻し改訂版。v1 (execution_plan.md) を再構成し、動画系を保留タグ付与、仕組み改善系を優先度 A/B/C に再編、GLM/Sonnet/Opus[1m] 混在運用前提で各 subtask にモデル指定を追加。

- **作成**: 2026-04-24 / gunshi (subtask_1441_phaseB2)
- **前身**: work/cmd_1441/execution_plan.md (commit 889d948)
- **併読**: work/cmd_1441/decision_gates_v2.md (殿判断ゲート D1-D10 の改訂版)

---

## 0. v1 → v2 改訂差分 (必読)

| # | 差分項目 | v1 (旧) | v2 (新) | 根拠 |
|---|---------|---------|---------|------|
| Δ1 | Wave 体系 | Wave1/2/3 の3段 | **優先度 A/B/C + 保留 + MCN別軸** の4分類 | 殿指示(B) 仕組み優先 |
| Δ2 | 動画系 4件 | Wave1/2 内に配置 | **保留タグ + re-trigger条件 明記** | 殿指示(B) 動画編集どうでもいい |
| Δ3 | D4 bloom_routing 推奨 | "A1-b 削除" | **"A1-a 復活" 確定** (既実装) | 殿指示(A) bloom_routing復活 |
| Δ4 | S29 新設 | v1 欠落 | **PreCompact snapshot 強化** を優先度Cに追加 | 将軍1-A をcarry-in、advisor指摘 |
| Δ5 | D10 新設 | v1 なし | **capability_tiers モデルmapping** (GLM/Sonnet/Opus[1m] を L1-L6 に配置) を殿判断ゲート追加 | A1-a復活に伴う sub-gate・advisor BLOCK指摘 |
| Δ6 | モデル指定列 | v1 記載なし | **GLM / Sonnet / Opus[1m] 列追加** (全subtask に明記) | 殿指示 GLM/Sonnet混在運用前提 |
| Δ7 | subtask 再分類 | 28件 | **A=3件 / B=5件 / C=7件 / 保留=4件 / MCN別軸=1件 / 除外=別cmd** | 仕組み改善優先で重み付け |

---

## 1. モデル指定ルール (v2 新設)

| モデル | 用途 | 1 subtask あたり平均コスト |
|--------|------|--------------------------|
| **GLM** (足軽既定) | YAML 簡易編集・既存ファイル minor edit・status更新・git mv | LOW |
| **Sonnet** (家老・軍師) | md 新規起草・統合作業・設計レビュー・QC | MED |
| **Opus[1m]** (今夜限特例) | 大規模分析・複雑推論・Opus観測 | HIGH |

**原則**: Opus[1m] は今夜のみ。明日以降は GLM/Sonnet 混在。軍師は基本 Sonnet (今夜は Opus[1m])。

---

## 2. 優先度 A （今夜ウィンドウ・計3件）

**定義**: Opus[1m] 週次リセット直後の今夜〜明日朝の限定ウィンドウで実行すべき案件。

| subtask_id | 旧ID | 種子 | モデル | 担当候補 | 依存 | 並列可否 | 所要時間 | advisor | git push | 成果物 |
|-----------|------|------|--------|---------|------|---------|---------|---------|---------|-------|
| **p01-v2** | p11 (v1) | **S24 Opus[1m] 観測ダッシュボード + claude-mem dateRange bug 回避ガイド** (監視系ゆえ動画保留の対象外) | **Opus[1m] 今夜限** + Sonnet | 軍師 (観測設計) + 足軽5号 (α/β/γ) | なし | 並列可 | 2-3h | 実装前後 | 家老 | scripts/opus_observation.sh + crontab + memory/feedback_claude_mem_daterange_broken.md |
| **p02-v2** | p01 (v1) | **S01 cmd 一括 done化 (1393/1412/1417/1420/1424 5件)** | **GLM** | 足軽2号 | なし | 直列 (同yaml) | 15min | 実装前のみ | 家老 | shogun_to_karo.yaml status一括更新 |
| **p03-v2** | p07 (v1) | **S11 pretool_check 恒久修正 + target_path checklist + alert** | **Sonnet** | 足軽4号 | なし | 直列 (同script) | 1h | 実装前後 | 家老 | scripts/pretool_check.sh regex 拡張 + unit test + instructions/karo.md 5点セット化 |

**優先度A 並列グループ**:
- 足軽2号: p02-v2 (GLM・15min)
- 足軽4号: p03-v2 (Sonnet・1h)
- 足軽5号+軍師: p01-v2 (Opus[1m]+Sonnet・2-3h)

---

## 3. 優先度 B （今週・事故防止系・計5件）

**定義**: 仕組み改善のうち、放置すると事故・再発リスクが高い案件。今週中に家老が順次発令。

| subtask_id | 旧ID | 種子 | モデル | 担当候補 | 殿判断 | 依存 | 所要時間 | advisor | git push |
|-----------|------|------|--------|---------|--------|------|---------|---------|---------|
| **p04-v2** | p15 (v1) | **S13 skills/ whitelist→全体 tracked 運用改善** | GLM+Sonnet | 足軽1号 | D3: "全体 tracked" 殿承認要 | なし | 1-2h | 実装前後 | 家老 |
| **p05-v2** | p16 (v1) | **S16 bloom_routing A1-a 復活** (settings.yaml に bloom_routing + capability_tiers 追加) | Sonnet | 足軽4号 | **D10 capability_tiers モデルmapping 殿判断要** | p01-v2 後 | 1h | 実装前後 | 家老 |
| **p06-v2** | A-7/S13 由来 | **skill-creator に whitelist 工程組込 (cmd_1441_block.yaml 既存案と一体化)** | Sonnet | 足軽7号 | なし (設計運用決定のみ) | p04-v2 後 | 1h | 実装前後 | 家老 |
| **p07-v2** | p08 (v1) | **S19 memory/archive/ 新設 + hlsh_selection 8件 + png 4枚退避** | GLM | 足軽5号 | なし | なし | 30min | 実装前のみ | 家老 |
| **p08-v2** | S15 派生 | **J-5 ntfy wrapper 統一 (`scripts/ntfy_send.sh "level:title:body"`) + dashboard 🚨 auto-prune hook** | Sonnet | 足軽3号 | なし | なし | 2-3h | 実装前後 | 家老 |

**優先度B 並列グループ (今週)**:
- 足軽1号: p04-v2 (skills whitelist)
- 足軽3号: p08-v2 (ntfy wrapper)
- 足軽4号: p05-v2 (bloom_routing) ← D10 殿判断後に発令
- 足軽5号: p07-v2 (memory/archive/)
- 足軽7号: p06-v2 (skill-creator 工程組込)

---

## 4. 優先度 C （2週内・構造整理系・計7件）

**定義**: 運用品質・容量圧縮・整流化系。今週完了は不要だが2週内に発令すべき。

| subtask_id | 旧ID | 種子 | モデル | 担当候補 | 殿判断 | 依存 | 所要時間 | advisor | git push |
|-----------|------|------|--------|---------|--------|------|---------|---------|---------|
| **p09-v2** | p17 (v1) | **S17 instructions/{generated,cli_specific,common,roles}/ 26 file archive化** | Sonnet | 足軽4号 | D5 "archive化" 殿承認要 | p05-v2 後 | 1h | 実装前のみ | 家老 |
| **p10-v2** | p19 (v1) | **S20 MEMORY.md core 分割 + スキーマ統一** | Sonnet | 足軽5号 | D6 "shogun.md同期更新" 殿承認要 | p07-v2 後 | 2h | 実装前後 | 家老 |
| **p11-v2** | p20 (v1) | **S21 MCP 3D entity (11 entities) 集約 + 観察昇格仕組み** | Sonnet | 足軽5号 | D7 "snapshot+転記 必須" 殿承認要 | p10-v2 後 | 半日 | 実装前後 | 家老 |
| **p12-v2** | p22 (v1) | **S26 dozle_kirinuki submodule gcloud-sdk 履歴書換** | Sonnet | 足軽4号 | D9 "backup+force-with-lease" 殿承認要 | なし | 1日 | 実装前後 | 家老 (force-with-lease) |
| **p13-v2** | p10 (v1) | **S23 cmem todolist 反映 + Phase2 3案 (G/A/B)** | Sonnet | 足軽7号 | なし | p01-v2 後 | 1h | 実装前後 | 家老 |
| **p14-v2** | p09 (v1) | **S22 三層アーキ memory_architecture.md** | Sonnet | 足軽5号 or 軍師 | なし | p07-v2 後 | 1h | 実装前後 | 家老 |
| **p15-v2** | **S29 新設** | **PreCompact snapshot 強化** (dashboard 30→60行・git log/diff stat追加・pane末尾100行を含める) | Sonnet | 足軽3号 | なし (運用決定のみ) | なし | 2h | 実装前後 | 家老 |

**優先度C 並列グループ (2週内)**:
- 足軽3号: p15-v2 PreCompact snapshot 強化
- 足軽4号: p09-v2 instructions archive → p12-v2 submodule 履歴書換
- 足軽5号: p10-v2 MEMORY.md core → p11-v2 MCP 3D → p14-v2 三層アーキ
- 足軽7号: p13-v2 cmem todolist

---

## 5. 保留 （動画系・殿指示 (B) により今cycle対象外・計4件）

**定義**: 殿方針「仕組み改善優先・動画編集は今どうでもいい」により、本 cmd_1441 Phase C から一時離脱。ただし再開トリガー (re-trigger) 条件が満たされたら即発令可能。成果物リストと担当候補は保持。

| subtask_id | 旧ID | 種子 | re-trigger 条件 | 担当候補 (再開時) | 所要時間 (再開時見積) |
|-----------|------|------|----------------|------------------|---------------------|
| **paused_p06** | p06 (v1) | **S07 TNT漫画ショート2本完走** (panels_960_1080 + asobunokinshi) | 殿「漫画ショート再開」 or 殿「TNT完走」指示 | 足軽6号 or 1号 | 1-2h |
| **paused_p12** | p12 (v1) | **S08 charlotte vp9→h264 + Day6 MIX workflow** | 殿「Day6 MIX 発令」 or 4視点MIX 素材準備指示 | 足軽6号 | 3-4h |
| **paused_p13** | p13 (v1) | **S09 part_info.json oo_men誤記修正** (Day6 MIX 前提条件) | 殿「Day6 MIX 発令」連動 (paused_p12 と同時再開) | 足軽5号 | 10min |
| **paused_p14** | p14 (v1) | **S10 20260417 panels 11バリアント剪定 + 命名規約** | 殿「panels 整理」 or Day6 MIX 発令連動 | 足軽2号 or 7号 | 2h |

**re-trigger プロトコル**:
1. 殿からの動画系再開指示を家老が受領
2. 家老が該当 `paused_p*` subtask を `assigned` に昇格・inbox_write 発令
3. 軍師は本 execution_plan_v2.md の担当候補・所要時間見積をベースに不変のまま渡せる

---

## 6. MCN 別軸 (殿アクション要・継続・計1件)

**定義**: 殿の直接判断・送信アクション・外部事情依存のため、Phase C Wave とは別軸で継続管理。

| subtask_id | 旧ID | 種子 | 状態 | 殿判断 |
|-----------|------|------|------|--------|
| **mcn_v2** | p21 (v1) | **S25 MCN v2 (送信チャネル確定～送信～30日後 /schedule)** | **D8 継続** | ガイドライン URL/PDF + 送信チャネル + AI 3段構え承認 → 確定次第 v2 起草再開 |

---

## 7. cmd_1441 対象外 (別 cmd 化・計 複数件)

v1 で Wave3 に配置していた案件のうち、殿方針「仕組み改善優先」に照らして重みが低いものは cmd_1441 から外し、別 cmd に分離する。家老の発令判断に委ねる。

| 旧ID | 種子 | 送り先 |
|------|------|-------|
| p25 (v1) | S06 tasks/reports/handoff YAML archive 3本立て | 別 cmd「運用整備bundle」(来月) |
| p26 (v1) | S12 skill-candidate-tracker skill + Kanban | 別 cmd「skill管理整備」(来月) |
| p27 (v1) | S14 塩漬け skill 5件 実装サージ | 別 cmd「skill サージ」(来月・2.5人日) |
| p28 (v1) | S15 dashboard lifecycle (単体) | **p08-v2 に一部吸収** + 残りは来月 |
| p23 (v1) | S27 cmd_1412 on_hold 再提示テンプレ | **保留 (動画系の派生案件扱い)** |
| p24 (v1) | S28 軍師QC基盤強化 | 別 cmd「QC基盤強化」(来月・軍師自タスク) |
| (v1対象外) | B-3〜B-7 仕組化5件 (ntfy→status自動化/YAML lint/archive整合/on_hold escalation/resolves_cmd) | 別 cmd「運用自動化bundle」 |
| (v1対象外) | F-2/F-4/F-8 動画系残 | 動画保留と同扱い |

---

## 8. 同一ファイル編集の直列化 (v2 更新)

v1から変更なし + v2 で追加。複数 subtask が編集対象 → 家老が batch 化 or 順次発令。

| ファイル | 編集 subtask | 推奨順序 |
|---------|-------------|---------|
| `.gitignore` | p04-v2 (skills/全体 tracked 変更) + p06-v2 (skill-creator 工程組込時の動作確認で編集可能性) | p04-v2 → p06-v2 |
| `shogun_to_karo.yaml` | p02-v2 (5件 done) → (動画系再開時 paused_p* done更新) | p02-v2 先行 |
| `CLAUDE.md` | p05-v2 (bloom_routing復活) → p09-v2 (参照修正) → p10-v2 (Session Start) | p05-v2 → p09-v2 → p10-v2 |
| `karo.md` | p03-v2 (5点セット) + p05-v2 (bloom_routing) | **p05-v2 → p03-v2** ※v1の順序を入れ替え (bloom復活が先・checklist統合が後) |
| `shogun.md` | p13-v2 (cmem Session Start) + p10-v2 (MEMORY.md 分割) + p11-v2 (MCP add_observations) | p13-v2 → p10-v2 → p11-v2 |
| `memory/MEMORY.md` | p07-v2 (archive リンク) → p10-v2 (core 分割) | p07-v2 → p10-v2 |
| `config/settings.yaml` | p05-v2 (bloom_routing + capability_tiers 追加) | 単独 |
| `scripts/pretool_check.sh` | p03-v2 (regex 拡張) | 単独 |

---

## 9. advisor 要否リスト (v2)

### 必須 (実装前後 両方)
p01-v2 / p03-v2 / p04-v2 / p05-v2 / p06-v2 / p08-v2 / p10-v2 / p11-v2 / p12-v2 / p13-v2 / p14-v2 / p15-v2

### 実装前のみ
p02-v2 / p07-v2 / p09-v2

### 不要
なし (v2 では全subtask が advisor 必須)

---

## 10. 北極星アラインメント (v2)

- **北極星**: ドズル社切り抜きチャンネル質・効率の両立 (長期的にはDay6 MIX 高品質・MCN加入・収益化)
- **v2 での変更による影響**:
  - **短期的北極星寄与度は下がる** (動画系保留→視聴者価値への即時貢献が減る)
  - **中長期的北極星寄与度は上がる** (仕組み改善で再発事故防止・Day6 MIX 再開時の迅速さ確保)
- **リスク**:
  - 動画保留が長期化すると投稿頻度低下 → 殿の動画系再開判断を要監視 (dashboard 🚨 に保留4件を可視化)
  - D10 capability_tiers モデル mapping 殿判断遅延 → p05-v2 bloom_routing 復活発令が遅れる
- **自己評価**: **aligned** (殿指示に沿った再編・仕組み整備を最優先化)

---

## 11. v2 承認条件 (軍師→家老→殿)

1. 本ファイル + decision_gates_v2.md の2点提出
2. 家老による軍師 QC (subtask_1441_phaseB2_qc)
3. 殿判断ゲート D1-D10 の回答受領
4. 家老が優先度A から順次 Phase C cmd 発令開始 (今夜中に p01-v2 + p02-v2 + p03-v2 を並列発令可能)

以上、execution_plan_v2.md として提出する。動画系は保留タグ保持・仕組み改善系は A/B/C 優先度で即時発令可能状態とした。
