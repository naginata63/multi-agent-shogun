---
name: git push 認証方法 (本プロジェクト)
description: 本プロジェクトはSSH鍵不使用・HTTPS+gh auth git-credential認証が正規経路。SSH remote URLは誤り。
type: feedback
---

本プロジェクトの git push 認証は **HTTPS + gh CLI credential helper** が正規経路。

**Why:** ~/.ssh/ に秘密鍵は存在しない。普段は `gh auth git-credential` 経由のHTTPS認証でpushしていた。remote URLが `git@github.com:...` (SSH形式) のままだったのが2026-05-06のpush失敗の原因 (将軍が判明・復旧)。

**How to apply:**
- `git push` が `Permission denied (publickey)` で失敗したら → まず `git remote -v` で remote URL確認
- `git@github.com:...` (SSH) になっていたら即 `git remote set-url origin https://github.com/naginata63/multi-agent-shogun.git` に切替
- `gh auth status` で認証確認 → `Logged in to github.com as naginata63` ならOK
- それでも失敗なら `gh auth login` 再実行
- **SSH鍵がない = 異常ではない** (本プロジェクト設計上SSH鍵不使用)
- submodule (projects/dozle_kirinuki/) も同様にHTTPS URL推奨

確認済み設定:
- `~/.gitconfig`: `helper = !/home/murakami/.local/bin/gh auth git-credential`
- `~/.config/gh/hosts.yml`: github.com / naginata63 として認証済 (keyring保存)
- gh token scope: `gist read:org repo workflow`
