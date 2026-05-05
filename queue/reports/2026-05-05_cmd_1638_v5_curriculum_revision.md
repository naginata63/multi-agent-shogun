# cmd_1638 v5 詳細設計書 10 項目改訂 完了報告書

- **報告者**: 軍師 (gunshi)
- **task_id**: subtask_1638_v5_revision
- **parent_cmd**: cmd_1638
- **作成日**: 2026-05-05
- **判定**: ✅ **完了** (受入条件 19/19 充足)
- **commit**: 7ad3b07 / pushed to origin/main

---

## 1. 10 項目改訂対応マトリクス

| # | 殿指示 | 対応箇所 | 検証結果 |
|---|--------|---------|---------|
| [A] | ch00 に 3 層世界観スライド追加 + 11 困りごと→3 層欠如マッピング表 | §3 (3 層モデル + 章配置 + 章構成図)・§4 (11→3 層欠如表)・ch00 解説アウトライン #2 #3 | ✅ §3 / §4 / ch00 のアウトラインに反映 |
| [B] | 全 12 章末尾に「強化した層」1 行追記 | 全 12 章末に `#### 強化した層` セクション追加 | ✅ grep `#### 強化した層` = **12 件** |
| [C] | ch03 タイトル変更 + 3 制約 (容量上限/Lost in the Middle/Context Rot) | ch03 タイトル「context window の 3 つの制約」+ アウトライン #1-#3 で 3 制約解説 | ✅ ch03 タイトル & 3 制約スライド配置済 |
| [C-2] | Lost in the Middle を「指示」ではなく「コンテキスト/参照情報」と正確記述 | ch03 専用ボックス「Lost in the Middle の正確な解釈 (殿指摘の反映)」 | ✅ 誤/正の対比で明記 |
| [D] | ch04 → JIT 対策の実装章 (claude-mem + handoff + Lazy Load + PreCompact) | ch04 タイトル「JIT 対策の実装」+ アウトライン #1-#5 で 4 道具解説 | ✅ JIT 概念スライド + 4 道具を解説 |
| [E] | 全 12 章 Emotional Hook を「現象→対策」構造に書き直し | 各章 `#### Emotional Hook (現象 → 対策)` 形式 | ✅ grep `#### Emotional Hook` = **12 件** |
| [F] | ch10 逆引き辞典を「症状→現象→対策→該当章」3 段構造化 | ch10 内「3 段逆引き早見表」必須スライドに 11 件全件配置 | ✅ 4 列構造 (症状/現象/対策/該当章) |
| [F-2] | ch10 に 3 層インデックス (プロンプト/コンテキスト/ハーネス不足由来) | ch10 内「3 層インデックス」必須スライド | ✅ 4 区分 (プロンプト/コンテキスト/ハーネス/複合) で全 11 件分類 |
| [G] | ch01 に Script/SlashCommand/Skill 比較表スライド | ch01 解説アウトライン #4 + 専用比較表 (6 行 × 4 列) | ✅ 比較表で 6 観点を明示 |
| [G-2] | ch01 末尾「Skill = `/command` の上位互換 (詳細 ch11)」布石スライド | ch01 解説アウトライン #6 として配置 | ✅ 布石明記 |
| [H] | ch07 末尾に「Skill が hook と連携する仕組み」スライド | ch07 内「Skill が hook と連携する仕組み (章末必須スライド)」 | ✅ 図解 + 説明文配置 |
| [I] | ch11 主題を「自分専用の Skill を作る」に変更 | ch11 タイトル「自分専用の Skill を作る — 3 層統合の到達点」 + 解説アウトライン全面刷新 | ✅ 主題変更 + 3 層統合演習として再設計 |

> 全 10 項目 (展開後 12 サブ項目) すべて反映済

---

## 2. 受入条件 19 件 充足検証

| # | 受入条件 | 結果 | 証跡 |
|---|---------|------|------|
| 1 | ch00 に 3 層世界観スライド | ✅ | §3 で 3 層モデル図 + ch00 解説 #2 |
| 2 | ch00 に 11 困りごと → 3 層欠如マッピング表 | ✅ | §4 で 11 件の欠如層を全件マッピング |
| 3 | 各章末「強化した層」1 行 (12 章全件) | ✅ | grep `#### 強化した層` = 12 件 |
| 4 | ch03 タイトル「context window の 3 つの制約」 | ✅ | line 331 |
| 5 | ch03 に 3 制約 (容量上限・Lost in the Middle・Context Rot) | ✅ | ch03 解説アウトライン #1-#3 |
| 6 | Lost in the Middle 正確記述 (指示ではなくコンテキスト) | ✅ | ch03 内専用ボックスで誤/正対比 |
| 7 | ch04 が JIT 対策の実装章として再構成 | ✅ | ch04 タイトル + 4 道具解説 |
| 8 | 全 12 章 Emotional Hook が「現象→対策」構造 | ✅ | grep `#### Emotional Hook (現象 → 対策)` = 12 件 |
| 9 | ch10 が「症状→現象→対策→該当章」3 段構造 | ✅ | 4 列 11 行の早見表 |
| 10 | ch10 に 3 層インデックス | ✅ | プロンプト/コンテキスト/ハーネス/複合 4 区分 |
| 11 | ch01 に Script/SlashCommand/Skill 比較表 | ✅ | 6 観点 × 4 列の比較表 |
| 12 | ch01 末尾「Skill 布石」スライド | ✅ | ch01 解説アウトライン #6 |
| 13 | ch07 末尾「Skill が hook と連携」スライド | ✅ | 図解付きで章末配置 |
| 14 | ch11 主題が「自分専用の Skill を作る」 | ✅ | ch11 タイトル変更済 |
| 15 | 章数 12 維持・所要時間合計 5-6h 維持 | ✅ | 12 章・335 min = 5h35min |
| 16 | NG ワード 0 件 | ✅ | grep カウント 0 |
| 17 | Marp HTML 再生成済 | ✅ | curriculum_intermediate_v5.html (1039 行) |
| 18 | URL 200 応答 | ✅ | curl http://192.168.2.4:8773/curriculum_intermediate_v5.html → 200 |
| 19 | git commit + push 済 | ✅ | commit 7ad3b07 / pushed |
| 20 | 完了報告書作成済 (本書) | ✅ | 本ファイル |

---

## 3. 改訂前後の差分要約

| 観点 | cmd_1637 完成版 | cmd_1638 改訂版 |
|------|---------------|-----------------|
| 行数 | 682 行 | 約 750 行 (+68 行) |
| 章数 | 12 章 | 12 章 (維持) |
| 所要 | 5h35min | 5h35min (維持) |
| 3 層世界観 | 武器①②③ として簡易記載 | **正式 3 層モデルとして §3 で詳説 + ch00 で先行提示** |
| ch00 | 困りごとフックのみ | **3 層スライド + 11→3 層欠如マッピング表追加** |
| 章末強化層 | なし | **全 12 章で 1 行明記** |
| ch03 | Lost in the Middle 中心 | **3 制約 (容量上限/LiM/Context Rot) に拡張** |
| ch04 | claude-mem + handoff 中心 | **JIT 4 道具 (claude-mem + handoff + Lazy Load + PreCompact) に再構成** |
| ch01 | `/command` のみ | **Script/SlashCommand/Skill 比較表 + Skill 布石追加** |
| ch07 | hook 4 種解説 | **末尾に「Skill+hook 連携」スライド追加** |
| ch10 | 早見表 1 段 | **3 段 (症状→現象→対策→章) + 3 層インデックスに刷新** |
| ch11 | 「ミニ自動化を作る」 | **「自分専用の Skill を作る」に変更 (講座到達点)** |
| Emotional Hook | 物語形式 | **「現象→対策」構造に統一 (12 章全件)** |

---

## 4. NG ワード検証結果

```bash
$ grep -cE "経済|階層|工程検問|サイレントフェイル|ハーネスエンジニアリング|queue/tasks|shogun|karo|ashigaru|gunshi|multi-agent-shogun" curriculum_intermediate_v5_marp.md
0
```

**結果**: ✅ **0 件** (ファイル全体)

### 章タイトル抽出 (12 章全件)

```
ch00. 講座のゴール — 3 層の世界観と「困りごと」の正体
ch01. プロンプトを資産にする — `/command` と Skill 布石 [プロンプト層]
ch02. よくある失敗 3 パターンの診断 [プロンプト層]
ch03. context window の 3 つの制約 [コンテキスト層]
ch04. JIT 対策の実装 — claude-mem + handoff + Lazy Load [コンテキスト層] ★ 検索 [手動]
ch05. 役割別ファイルで AI を分業させる [ハーネス層]
ch06. 第三者 AI に見直してもらう — /advisor [ハーネス層]
ch07. 自動で動かす — 4 種類の hook + Skill 連携 [ハーネス層] ★ 検索 [自動]
ch08. 失敗を見逃さない仕組み [ハーネス層]
ch09. 3 層を統合して業務に組み込む — 営業/PM/データ分析 [応用]
ch10. 困った時の逆引き辞典 — 症状 → 現象 → 対策 → 該当章 [逆引き]
ch11. 自分専用の Skill を作る — 3 層統合の到達点 [演習]
```

✅ 章タイトルにも NG ワード 0 件

---

## 5. 残課題と推奨 follow-up cmd

### 5-1. 即時 follow-up (家老判断)

- **cmd_1639 (Phase 2)**: 12 章 × 本文執筆 (.md + .html)
  - 足軽 4 名並列推奨 (3 章ずつ分担)
  - 各章執筆完了後 udemy-checker (5 観点) → 軍師 QC
  - **改訂版で追加された 3 層対応・Emotional Hook 構造・章末強化層** を必ず守る
  - 推定: 3-5 日

### 5-2. 観察事項 (NON-BLOCKING)

1. **ch11 主題変更の影響**: 「自分専用の Skill を作る」は講座到達点として強力だが、Phase 2 執筆時に **Skill の frontmatter 書式 + when-to-use 説明** の実装難度を受講者に伝える必要あり。Skill 作成のハードルを過度に下げない / 過度に上げない balance が肝。
2. **ch04 JIT 化**: Lazy Load の概念は慣れた開発者には自明だが、社会人 2-3 年目には「常時注入とどう違うのか」が直感的に伝わりにくい。Phase 2 執筆時に Before/After スライドで「常時注入 vs Lazy Load」の context 消費比較を必ず入れる。
3. **ch07 + ch11 の Skill 重複**: ch07 末尾の Skill+hook 連携スライドと ch11 主題が近接するため、Phase 2 で「ch07 = Skill との連携の入口」「ch11 = Skill 作成の本番」という役割分担を明示する文言を入れる必要あり。

---

## 6. north_star_alignment

```yaml
north_star_alignment:
  status: aligned
  reason: "10 項目改訂により、講座の北極星 (AI を自分専用の常駐ツールに仕組み化) が 3 層モデルとして可視化された。ch00 の 3 層世界観 → 各章末「強化した層」 → ch10 の 3 層インデックス → ch11 の Skill 創作 という縦軸が一本通り、受講者が章を読むたびに『自分はどの層を強化しているか』を意識できる構造を実現。"
  risks_to_north_star:
    - "Phase 2 執筆時に各章の「強化した層」表記がブレると、3 層の物語線が断絶する。Phase 2 軍師 QC で必ず検証。"
    - "ch11 の Skill 主題は講座到達点だが、Skill の実装難度が高いと受講者が脱落する。Phase 2 で「最小 Skill (10 行)」のサンプルを必ず提示することを推奨。"
    - "Lost in the Middle の正確記述 (殿指摘) は Phase 2 で再度誤記される可能性がある。執筆者にこの定義を必須参照させる仕組み (Phase 1 事前 4 項目で固定) が必要。"
```

---

## 7. 最終判定

```
status: completed
acceptance_criteria_met: 19/19 (全条件充足)
blocking_issues: 0
nonblocking_observations: 3
artifacts:
  - projects/udemy_course/drafts/curriculum_intermediate_v5_marp.md (約 750 行・改訂版で上書き)
  - projects/udemy_course/drafts/curriculum_intermediate_v5.html (1039 行・再生成済)
  - queue/reports/2026-05-05_cmd_1638_v5_curriculum_revision.md (本書)
git: commit 7ad3b07 / pushed to origin/main
```

**本タスク (10 項目改訂) は完了。家老の Phase 2 (cmd_1639) 起票を待つ。**
