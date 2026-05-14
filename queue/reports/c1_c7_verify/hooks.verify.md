公式 docs 取得完了。WebFetch agent の集計に矛盾あり (本文サマリ「28個」vs 引用表「29行」)。引用表が一次ソースゆえ再カウントする。

引用表から精査:
1. SessionStart / 2. Setup / 3. UserPromptSubmit / 4. UserPromptExpansion / 5. PreToolUse / 6. PermissionRequest / 7. PermissionDenied / 8. PostToolUse / 9. PostToolUseFailure / 10. PostToolBatch / 11. Notification / 12. SubagentStart / 13. SubagentStop / 14. TaskCreated / 15. TaskCompleted / 16. Stop / 17. StopFailure / 18. TeammateIdle / 19. InstructionsLoaded / 20. ConfigChange / 21. CwdChanged / 22. FileChanged / 23. WorktreeCreate / 24. WorktreeRemove / 25. PreCompact / 26. PostCompact / 27. Elicitation / 28. ElicitationResult / 29. SessionEnd

**= 29 event 確定**。`FileChanged` も表 22 番目に明示。

---

## 致命傷 C1 判定 (FileChanged は公式 hook event か)

- **judgment**: ✅実在
- **official_fact**: 公式ドキュメント引用 — `| FileChanged | When a watched file changes on disk. The matcher field specifies which filenames to watch |` (Hook Lifecycle 表 22 行目)。さらに matcher 表で `| FileChanged | 監視するリテラル ファイル名（[FileChanged](#filechanged)を参照） | .envrc|.env |`、決定制御表でも `WorktreeRemove、Notification、SessionEnd、PostCompact、InstructionsLoaded、StopFailure、CwdChanged、FileChanged | なし | 決定制御なし` と 3 箇所で言及されている
- **講座記述の問題**: 中級編 ch11 で `FileChanged` を使用している記述は公式仕様と完全一致。**問題なし**
- **推奨修正**: 不要 (記述維持)
- **priority**: — (修正不要)

---

## 致命傷 C2 判定 (公式 hook event 数 = 29 種類)

- **judgment**: ✅実在
- **official_fact**: 公式ドキュメント Hook Lifecycle 表に 29 個の event が明示列挙されている (SessionStart / Setup / UserPromptSubmit / UserPromptExpansion / PreToolUse / PermissionRequest / PermissionDenied / PostToolUse / PostToolUseFailure / PostToolBatch / Notification / SubagentStart / SubagentStop / TaskCreated / TaskCompleted / Stop / StopFailure / TeammateIdle / InstructionsLoaded / ConfigChange / CwdChanged / FileChanged / WorktreeCreate / WorktreeRemove / PreCompact / PostCompact / Elicitation / ElicitationResult / SessionEnd)
- **講座記述の問題**: 多章での「29 種類」記述は公式仕様と**完全一致**。先のレビューエージェント (S14558 等) が「29 種類」を致命傷扱いした判定は**誤検出**の可能性が極めて高い。なお講座本文に「29種類（代表的な抜粋）」と書いていた箇所 (obs 25396) は、抜粋ではなく**全 29 種類が公式の総数**ゆえ「（代表的な抜粋）」の括弧書きを除去する方が正確
- **推奨修正**: 「29 種類」の数字はそのまま維持。但し「29種類（代表的な抜粋）」と書いている箇所があれば「（代表的な抜粋）」を削除し「Claude Code 公式 hook event 全 29 種類 (Anthropic docs 2026-01 時点)」のように出典明記。レビューエージェント側の致命傷リスト C2 はクローズ可
- **priority**: 低 (語句調整のみ)

---

**結論**: C1・C2 ともに講座記述は公式仕様と一致。レビューエージェントの C2 致命傷判定は誤検出。C1 → 修正不要。C2 → 「（代表的な抜粋）」の文言があれば削除し出典付記の軽微修正のみ。
