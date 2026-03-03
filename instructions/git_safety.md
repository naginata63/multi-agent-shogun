# Git Safety Protocol (all agents)

**These rules have the same authority as Destructive Operation Safety. UNCONDITIONAL.**

## Part 1: Batch File Modification (5件以上のファイルを修正するとき)

sed, awk, Python scripts, shell loops 等でファイルを一括修正する際の必須手順。

### Core Rule

**「検証OKなら commit。NGなら restore。」** — これだけ覚えよ。

### Procedure

```
① SAVE:  git add <target_dir> && git commit -m "checkpoint: before <task_id>"
② TEST:  Run script on 1 file ONLY → verify output (content correct? file size OK?)
③ RUN:   If TEST OK → run script on remaining files (1 category at a time)
④ CHECK: git diff --name-status <target_dir>
         - D (deleted) entries → NG
         - M count ≠ expected → NG
         - Files outside target_scope modified → NG
⑤ RESULT:
   - OK → git add <target_dir> && git commit -m "fix(<category>): <task_id>"
          → repeat ②-⑤ for next category
   - NG (any step) → git restore <target_dir> → report to Karo → STOP
```

### Modification Rules

1. **Step ① is NEVER skippable.** No commit = no rollback = unrecoverable data loss.
2. **Step ② catches script bugs** on 1 file before they destroy a whole directory.
3. **Always `git add <target_dir>`**, never `git add .` or `git add -A`. Prevents staging other agents' work.
4. **Scope restriction**: Only modify files within `target_scope` from task YAML. Outside scope = STOP.
5. **One agent at a time** for batch modifications. Karo ensures sequential assignment.

## Part 2: Commit & Push Protocol (成果物の保全)

### Who Does What

| Action | Who | When |
|--------|-----|------|
| checkpoint commit | 足軽 | Before batch modification (Part 1 ①) |
| fix/feat commit | 足軽 | After verified work (Part 1 ⑤ or subtask completion) |
| **git push** | **家老 only** | **After cmd status → done** |

### Commit Message Format

| Prefix | Usage | Example |
|--------|-------|---------|
| `checkpoint:` | Pre-work safety save | `checkpoint: before subtask_167a` |
| `fix(<scope>):` | Bug fix / correction | `fix(01_sales): subtask_167a codeblock repair` |
| `feat(<scope>):` | New feature / content | `feat(coconala): subtask_160a add 20 prompts` |
| `docs(<scope>):` | Documentation change | `docs(readme): subtask_155a update setup guide` |

### Push Rules

1. **足軽は git push を実行してはならない。** Push は家老の責務。
2. **家老は cmd 完了確認後に `git push origin main` を実行。** `--force` 禁止（D003）。
3. **4時間ルール**: cmd が 4時間以上未完了の場合、家老は中間 push を実施（災害保護）。
4. **push 先は `origin` のみ。** `upstream` への push は殿の明示的承認が必要。
