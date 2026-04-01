# スキルバジェット監査レポート

**実施日**: 2026-04-01
**担当**: ashigaru4 (subtask_1044a)

## サマリー

| 区分 | スキル数 | 文字数 | 16,000文字に対する使用率 |
|------|---------|--------|------------------------|
| skills/ (SKILL.md) | 20個 | 86,913 | 543.2% |
| .claude/commands/ (.md) | 4個 | 4,468 | 27.9% |
| **合計** | **24個** | **91,381** | **571.1%** |

⚠️ **合計文字数が予算の5.7倍超過。**

---

## skills/ 詳細 (20スキル)

| スキル名 | 文字数 |
|---------|--------|
| shogun-bloom-config | 12,986 |
| skill-creator | 7,243 |
| thumbnail | 6,036 |
| video-pipeline | 5,936 |
| highlight | 5,918 |
| shogun-model-list | 5,299 |
| collective-select | 4,475 |
| manga-short | 4,382 |
| shogun-model-switch | 4,325 |
| expression-gen | 4,314 |
| shogun-screenshot | 3,754 |
| youtube-stats | 3,441 |
| expression-short-workflow | 3,278 |
| gemini-video-transcribe | 3,135 |
| manga-short-workflow | 2,790 |
| gemini-image-prompt | 2,721 |
| restore-panes | 2,481 |
| shogun-readme-sync | 2,214 |
| shogun-agent-status | 1,290 |
| senkyou | 895 |
| **合計** | **86,913** |

## .claude/commands/ 詳細 (4コマンド)

| コマンド名 | 文字数 |
|----------|--------|
| handoff.md | 2,107 |
| format-prompt.md | 1,323 |
| rehydrate.md | 535 |
| batch-safety.md | 503 |
| **合計** | **4,468** |

---

## 備考

- **skills/ ディレクトリ**: Claude Code の系統プロンプトには自動ロードされず、タスクYAML作成時にKaroが参照する設計。ただし巨大なSKILL.mdをタスクに埋め込む場合は実質コンテキストを圧迫する。
- **最大スキル**: `shogun-bloom-config` (12,986字) — 単体で予算の81.2%を占める。
- **.claude/commands/ のみ**: 4,468字 = 予算の27.9%（現行制約内）。
- **削減候補**: shogun-bloom-config、skill-creator、thumbnail は各5,000字超え。内容精査推奨。

## 結論

`.claude/commands/` (スラッシュコマンド) 単体では27.9%で予算内。
`skills/` を含めた合計では571%と大幅超過。
`skills/` が直接コンテキストに乗らない設計である点を踏まえると、実運用上の問題は`.claude/commands/`に限定される可能性あり。
ただし `shogun-bloom-config` (12,986字) など大型スキルの整理は今後の課題。
