---
name: skill-inventory
description: |
  スキル化候補の即時棚卸しを走らせ、context/skill_candidates_inventory.md を再生成する。
  「スキル候補を棚卸しして」「/skill-inventory」「skill_candidate一覧更新」で起動。
  Do NOT use for: 新規スキルの設計（それは skill-creator を使え）。
allowed-tools: Bash, Read
---

# /skill-inventory — スキル化候補 即時棚卸し

skill-candidate-tracker スキル (`skills/skill-candidate-tracker/SKILL.md`) の collect.sh を即時実行する。

## 動的コンテキスト

### 直近生成の inventory 冒頭 (存在すれば)
!`head -20 /home/murakami/multi-agent-shogun/context/skill_candidates_inventory.md 2>/dev/null || echo "(未生成)"`

### 前回実行の state
!`cat /home/murakami/multi-agent-shogun/logs/skill_inventory_state.json 2>/dev/null || echo "(state なし)"`

## 実行

```bash
cd /home/murakami/multi-agent-shogun
bash skills/skill-candidate-tracker/collect.sh --write --no-ntfy
```

実行後、以下を報告:
1. `context/skill_candidates_inventory.md` のサマリー (PENDING / IMPLEMENTED / NAMELESS / multi_mention 件数)
2. 前回から新規検出された PENDING 候補 (あれば)
3. 直近7日以内の初出候補 (軍師 quarterly review 観察対象)

## 禁止事項

- cron 定期実行 (C14) とぶつからないよう、手動実行時は必ず `--no-ntfy` を付ける
- 新規 .py 作成は禁止。collect.sh の python3 HEREDOC を編集するなら skill-candidate-tracker 側で実施すること
