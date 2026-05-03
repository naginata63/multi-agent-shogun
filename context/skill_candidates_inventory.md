# Skill Candidates Inventory (自動棚卸し)

**最終更新**: 2026-05-03T10:51 / karo (cmd_1587/cmd_1590)

`queue/reports/*.yaml` の `skill_candidate.found=true` を横断抽出した一覧。
同名候補は初出/最終言及日で集約。Python/PyYAML でパース (旧形式 bare + 新形式 nested 両対応)。

## 🚨 要対応 (殿承認待ち)

| # | skill_name | 提案元 | 概要 | 承認状況 |
|---|-----------|--------|------|---------|
| 1 | **subtitle-color-speaker-qc** | cmd_1587/gunshi | subtitle_speaker_qc.py — 字幕色→話者キー紐付けQC (PIL+Gemini Vision 2方式・strict/updateモード・DoZ社字幕品質基盤) | 🚨 殿承認待ち |
| 2 | **lecture_grep_rule_refinement** | cmd_1590 ch08/gunshi | lecture_design_rules.md Section 12 のgrep ルール精緻化 — `候` が `候補`等の現代語をfalse positive検出する問題の修正 | 🚨 殿承認待ち |

## サマリー

- 総候補数: **2**
- 🚨 PENDING (未スキル化): **2**
- ✅ IMPLEMENTED (スキル化済): **0**
- 🟡 NAMELESS (旧形式・name欠落): **0**
- 🔁 2回以上言及 (ashigaru.md skill化基準クリア): **0**
- 🆕 直近7日以内初出 (cutoff=2026-04-26): **2**

## 候補一覧 (PENDING 先頭・last_seen 降順)

| # | skill_name | status | mentions | first_seen | last_seen | purpose | evidence |
|---|-----------|--------|----------|-----------|----------|---------|----------|
| 1 | subtitle-color-speaker-qc | 🚨 PENDING | 1 | 2026-05-03 | 2026-05-03 | DoZ社字幕色→話者紐付けQC | gunshi_cmd_1587_qc.yaml |
| 2 | lecture_grep_rule_refinement | 🚨 PENDING | 1 | 2026-05-03 | 2026-05-03 | grep戦国用語ルール精緻化 | gunshi_cmd_1590_ch08_qc.yaml |

## 🔁 2回以上言及された候補 (skill化基準クリア)

_(なし)_

## 🆕 直近7日以内 初出候補 (軍師 quarterly review 観察対象)

- **subtitle-color-speaker-qc** (2026-05-03): cmd_1587 - subtitle_speaker_qc.py 17115 bytes・PIL+Gemini Vision・前提注意: 実運用前に字幕焼き込み版で再テスト推奨
- **lecture_grep_rule_refinement** (2026-05-03): cmd_1590 ch08 - `候` grep false positive修正

---

## 運用

- **weekly cron**: `shared_context/cron_inventory.md` C14 参照 (毎週日曜深夜)
- **即時再生成**: `/skill-inventory` slash command または `bash skills/skill-candidate-tracker/collect.sh --write`
- **判定ロジック**: `skills/<name>/` 実在で IMPLEMENTED。なければ PENDING。name 欠落の旧形式 → NAMELESS (軍師レビューで name 付与 or 見送り判断)