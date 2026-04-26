# Skill Candidates Inventory (自動棚卸し)

**最終更新**: 2026-04-26T03:30:01 / skill-candidate-tracker (cmd_1447)

`queue/reports/*.yaml` の `skill_candidate.found=true` を横断抽出した一覧。
同名候補は初出/最終言及日で集約。Python/PyYAML でパース (旧形式 bare + 新形式 nested 両対応)。

## サマリー

- 総候補数: **4**
- 🚨 PENDING (未スキル化): **4**
- ✅ IMPLEMENTED (スキル化済): **0**
- 🟡 NAMELESS (旧形式・name欠落): **0**
- 🔁 2回以上言及 (ashigaru.md skill化基準クリア): **1**
- 🆕 直近7日以内初出 (cutoff=2026-04-19): **4**

## 候補一覧 (PENDING 先頭・last_seen 降順)

| # | skill_name | status | mentions | first_seen | last_seen | purpose | evidence |
|---|-----------|--------|----------|-----------|----------|---------|----------|
| 1 | `multi-view-mix-generator` | 🚨 PENDING | 2 | 2026-04-25 | 2026-04-25 | 4視点動画のMIX生成スクリプト。タイムラインJSON→clip抽出→concat→YouTube。 視点切替・2x2 grid対応。Day5/Day6で同パターン実証済 (zephyrus_v3.sh, gen_seg8sen.py)。 | subtask_1464b(ashigaru1), qc_1464b(gunshi) |
| 2 | `master-telop-two-stage` | 🚨 PENDING | 1 | 2026-04-25 | 2026-04-25 | 動画MIXのテロップ後付け二段生成方式。master(テロップなし)+drawtext後加工でテロップミス時の再コストを最小化 | subtask_1485a(ashigaru1) |
| 3 | `marp-lan-publish` | 🚨 PENDING | 1 | 2026-04-25 | 2026-04-25 | MarkdownファイルをMarp HTML化し、LAN内HTTP公開でスマホレビュー可能にする | subtask_1466a(ashigaru7) |
| 4 | `video-qc-llm-mode` | 🚨 PENDING | 1 | 2026-04-25 | 2026-04-25 | LLM軍師(動画再生不可)用の動画系QCチェックリスト。ffprobe specs + sync_record.yaml + drawtext_params_diff.md + 元素材ビットレート分析の4点セットで mpv 視聴の代替確認を | qc_1485a(gunshi) |

## 🔁 2回以上言及された候補 (skill化基準クリア)

- **`multi-view-mix-generator`** (PENDING, 2回) — 4視点動画のMIX生成スクリプト。タイムラインJSON→clip抽出→concat→YouTube。 視点切替・2x2 grid対応。Day5/Day6で同パターン実証済 (zephyrus_v3.sh, gen_seg8sen.py)。

## 🆕 直近7日以内 初出候補 (軍師 quarterly review 観察対象)

- **`multi-view-mix-generator`** (PENDING) — first_seen=2026-04-25
- **`master-telop-two-stage`** (PENDING) — first_seen=2026-04-25
- **`marp-lan-publish`** (PENDING) — first_seen=2026-04-25
- **`video-qc-llm-mode`** (PENDING) — first_seen=2026-04-25

---

## 運用

- **weekly cron**: `shared_context/cron_inventory.md` C14 参照 (毎週日曜深夜)
- **即時再生成**: `/skill-inventory` slash command または `bash skills/skill-candidate-tracker/collect.sh --write`
- **判定ロジック**: `skills/<name>/` 実在で IMPLEMENTED。なければ PENDING。name 欠落の旧形式 → NAMELESS (軍師レビューで name 付与 or 見送り判断)