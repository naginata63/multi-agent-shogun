# Skill Candidates Inventory (自動棚卸し)

**最終更新**: 2026-05-03T11:04 / karo (殿判断反映)

`queue/reports/*.yaml` の `skill_candidate.found=true` を横断抽出した一覧。
同名候補は初出/最終言及日で集約。Python/PyYAML でパース (旧形式 bare + 新形式 nested 両対応)。

## 殿判断済み (2026-05-03)

| # | skill_name | 判断 | 理由 |
|---|-----------|------|------|
| 1 | ~~subtitle-color-speaker-qc~~ | ❌ 却下 | 既存スクリプト直呼出で十分・DoZ専用カラー表・PIL+Gemini Python依存・利用頻度低い |
| 2 | **lecture-speaker-notes-grep-check** | ✅ 承認 | cmd_1592 で実装中・Udemy制作標準QCとして価値高い |
| 3 | lecture_grep_rule_refinement | → cmd_1592 に統合 | check.sh のgrep戦国語パターン精緻化として実装 |

## サマリー

- 総候補数: **3**
- 🚨 PENDING (未スキル化): **0**
- ✅ IMPLEMENTING (実装中): **1** (lecture-speaker-notes-grep-check / cmd_1592)
- ❌ REJECTED: **1** (subtitle-color-speaker-qc)
- → 統合済: **1** (lecture_grep_rule_refinement → cmd_1592)

## 候補一覧

| # | skill_name | status | first_seen | purpose | evidence |
|---|-----------|--------|-----------|---------|----------|
| 1 | lecture-speaker-notes-grep-check | ✅ IMPLEMENTING | 2026-05-03 | Marp lecture speaker notes自動検証 | cmd_1592 |
| 2 | ~~subtitle-color-speaker-qc~~ | ❌ REJECTED | 2026-05-03 | DoZ社字幕色→話者紐付けQC | gunshi_cmd_1587_qc.yaml |
| 3 | lecture_grep_rule_refinement | → 統合 | 2026-05-03 | grep戦国用語false positive修正 | cmd_1592 統合 |

## 🔁 2回以上言及された候補 (skill化基準クリア)

_(なし)_

## 🆕 直近7日以内 初出候補

- **lecture-speaker-notes-grep-check** (2026-05-03): cmd_1592 実装中

---

## 運用

- **weekly cron**: `shared_context/cron_inventory.md` C14 参照 (毎週日曜深夜)
- **即時再生成**: `/skill-inventory` slash command または `bash skills/skill-candidate-tracker/collect.sh --write`
- **判定ロジック**: `skills/<name>/` 実在で IMPLEMENTED。なければ PENDING。name 欠落の旧形式 → NAMELESS (軍師レビューで name 付与 or 見送り判断)