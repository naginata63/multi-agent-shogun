Read the file `instructions/git_safety.md` and display its full contents. Then run `git status` and `git log --oneline -5` to show the current repository state.

After displaying, remind the agent:
- If you are about to run a batch modification script on 5+ files, follow Part 1 SAVE→TEST→RUN→CHECK→RESULT
- Checkpoint commit BEFORE running any script (Step ① is NEVER skippable)
- Use `git add <target_dir>` only — never `git add .`
- Ashigaru: commit only. Karo will push after cmd completion.
