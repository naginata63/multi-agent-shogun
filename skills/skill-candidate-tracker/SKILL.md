---
name: skill-candidate-tracker
description: |
  queue/reports/*.yaml を横断スキャンし skill_candidate.found=true を抽出→
  context/skill_candidates_inventory.md にマークダウン表で集約する継続改善スキル。
  weekly cron (C14) で自動更新され、「/skill-inventory」slash で即時再生成もできる。
  「スキル候補棚卸し」「skill candidate」「/skill-inventory」「skill化候補一覧」で起動。
  Do NOT use for: 新規スキルの設計・作成（それは skill-creator を使え）。
  Do NOT use for: hotfix トレンド分析（それは hotfix_trend_detector.sh / C12 の責務）。
allowed-tools: Read, Bash, Grep, Edit, Write
argument-hint: "[--write|--dry-run]"
---

# /skill-inventory — スキル化候補 自動棚卸し

殿判断 (2026-04-24 21:10) で skill-candidate-tracker を正式スキル化。目的は「手動目視運用からの脱却・継続改善インフラの整備」。

## North Star

**queue/reports/*.yaml に埋もれた `skill_candidate.found=true` を 1枚の表に集約し、手動見落としをゼロにする。**

- dashboard.md に掲載されていない候補 10 件超が発覚した事実 (subtask_1441ghi) の再発防止
- skill_candidate が nested 形式 / 旧 bare 形式どちらでも拾える
- 既存 `skills/` ディレクトリと突合し「すでにスキル化済か」を自動判定
- 軍師・家老が四半期レビューで使う単一情報源

## 動的コンテキスト (L2 読込時点の状態)

### 現在の候補件数 (found:true のみ)
!`grep -rB1 "found: true" /home/murakami/multi-agent-shogun/queue/reports/*.yaml 2>/dev/null | grep -c "^.*skill_candidate:" || echo 0`

### 最終生成日時 (inventory)
!`stat -c "%y" /home/murakami/multi-agent-shogun/context/skill_candidates_inventory.md 2>/dev/null || echo "(未生成)"`

### 既存スキル一覧 (照合用)
!`ls /home/murakami/multi-agent-shogun/skills/ 2>/dev/null | tr '\n' ' ' || echo "(なし)"`

---

## 手順

### Step 1: データ抽出 (collect.sh 実行)

本スキル同梱の `collect.sh` を実行する。`queue/reports/*.yaml` を走査し YAML として
`skill_candidate` ブロックを解析 → `found: true` の候補のみを抽出する。

```bash
cd /home/murakami/multi-agent-shogun
bash skills/skill-candidate-tracker/collect.sh --write
```

オプション:
- `--write` (default): `context/skill_candidates_inventory.md` に書き出す
- `--dry-run`: 標準出力にのみ出力して確認する

### Step 2: 既存スキルと照合

`collect.sh` 内部で以下を自動判定:

| 判定 | 条件 |
|------|------|
| **IMPLEMENTED** | 候補 name に対応する `skills/<name>/` が既存 |
| **PENDING** | name はあるがスキル未作成 |
| **NAMELESS** | name 欄なし・旧形式 (description のみ) |

### Step 3: inventory 生成

`context/skill_candidates_inventory.md` に以下の列を持つ markdown table を書き出す:

| 列 | 意味 |
|----|------|
| cmd_id | report ファイル名から抽出した `subtask_XXX` / `cmd_XXX` |
| agent | ファイル名先頭 (`ashigaruN` / `gunshi`) |
| skill_name | `skill_candidate.name`。無ければ `(nameless)` |
| purpose | `skill_candidate.description` 冒頭 120 文字 |
| status | IMPLEMENTED / PENDING / NAMELESS |
| first_seen | 同名候補の初出日 (report ファイルの mtime or report 内 `timestamp`) |
| last_seen | 同名候補の最終言及日 |
| evidence | report ファイルパス |

同一 `skill_name` の候補は集約 (first_seen=min, last_seen=max, evidence=複数列挙)。

### Step 4: 軍師レビュー用サマリー

inventory の末尾に以下を追記:

- PENDING 件数 / IMPLEMENTED 件数 / NAMELESS 件数
- 直近 7 日以内 first_seen の候補リスト (軍師 quarterly review の観察対象)
- 2 回以上言及された候補 (pattern repeated 2+ times = ashigaru.md の skill 化基準クリア)

### Step 5: ntfy 通知 (PENDING 新規検出時のみ)

前回実行時の state (`logs/skill_inventory_state.json`) と比較し、新規 PENDING が
1 件以上増えていたら ntfy で集約通知。重複通知を防ぐため state を更新して終了。

（state ファイルは cron 実行時に自動生成・管理される。手動実行時は `--no-ntfy` を付けてもよい）

---

## Triggering Test

**Should trigger:**
- 「スキル候補を棚卸しして」
- 「/skill-inventory」
- 「skill_candidate:true の一覧が欲しい」
- 「スキル化候補のインベントリ生成」

**Should NOT trigger:**
- 「新しいスキルを作りたい」→ skill-creator
- 「hotfix が繰り返されている」→ hotfix_trend_detector.sh (C12)
- 「MEMORY.md の棚卸し」→ monthly_feedback_review.sh (C13)

## Related

- **実装経緯**: cmd_1447 (2026-04-24 殿承認)
- **発見元**: subtask_1441ghi Phase A カテゴリ(h) スキル化アイデア
- **同種 cron 実装者**: cmd_1443_p09 H12 (cron_inventory + cron_health_check) ← 本タスク担当足軽が前作
- **cron 登録**: `shared_context/cron_inventory.md` の C14 参照
- **slash command**: `.claude/commands/skill-inventory.md`

## 禁止事項

- **新規 .py ファイル作成禁止** (cmd_1447 共通ルール)。python3 はワンライナー `-c` のみ
- **`git add .` 禁止 / 明示パスのみ** (CHK8 / 殿激怒 2026-04-24)
- 既存 hotfix_trend_detector と責務を重複させるな (hotfix_notes は対象外・skill_candidate のみ)
- inventory の上書き時も前回データを保持 (evidence 列を失うな)
