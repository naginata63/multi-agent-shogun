# Udemy 19章 修正版 最終レビュー 1ページサマリ

## 1. 章別総覧

| # | 章 | 総合重大度 | 主要残存問題 |
|---|----|---|---|
| 初00 | beginner_ch00_intro | 低 | 旧講座名残存, フック弱, 断言強め |
| 初01 | beginner_ch01_prompt | 中 | スライド17枚, フック弱, 公式分類要verify |
| 初02 | beginner_ch02_claude_md | 中 | walrus誤記, 18枚, local.md要verify |
| 初03 | beginner_ch03_md_family | 中 | 19枚, 用語4語未説明, フック弱 |
| 初04 | beginner_ch04_history | 中 | 29種要verify, 6モード要verify, 15枚 |
| 初05 | beginner_ch05_hook | 中 | 17枚, フック位置, >&2未説明 |
| 初06 | beginner_ch06_outro | 低 | 用語3語未注釈, ライフサイクル唐突 |
| 中00 | intermediate_v5_ch00_intro | 中 | Skill/SC混同, 18枚, フック平坦 |
| 中01 | intermediate_v5_ch01_command | 中 | $N誤記疑, legacy表記, 18枚 |
| 中02 | intermediate_v5_ch02_failure | 中 | Skill/SC混同, 22枚, フック弱 |
| 中03 | intermediate_v5_ch03_lost_mid | 中 | 23枚, LitM偏重, hook早出し |
| 中04 | intermediate_v5_ch04_long_text | 中 | 41枚, 29種要verify, 200行根拠 |
| 中05 | intermediate_v5_ch05_role_files | 中-高 | 35枚, 5方式要verify, local.md |
| 中06 | intermediate_v5_ch06_advisor | 中 | tool_ID要verify, 21枚, 29種 |
| 中07 | intermediate_v5_ch07_hooks | 中 | 28枚, SubAgentStop表記, jq唐突 |
| 中08 | intermediate_v5_ch08_fail_safe | 中 | 29種誤疑, 6モード誤疑, 19枚 |
| 中09 | intermediate_v5_ch09_business | 中 | Skill/SCをlegacy混同, 29種, 14枚 |
| 中10 | intermediate_v5_ch10_reference | **高** | 28枚, advisor_ID断定, 公式断定累積 |
| 中11 | intermediate_v5_ch11_skill | **高** | FileChanged誤記, 29種, Skill/SC混同 |

## 2. 高重大度章の詳細

### 中10 (逆引き辞典) — 重大度 高
- 公式断定の累積: harness記事 (3箇所)・hook 29種類 (3箇所)・advisor_20260301 tool ID (4箇所)・Agent=Model+Harness定式・URL `code.claude.com/docs/ja/`・2026-03記事・「コマンドはスキルにマージと明記」— **計7種類の未verify断定が同一章に集中**
- スライド28枚 (推奨の2倍超) — 早見表3分割/見分け方3枚/パターン3枚/末尾3枚を統合し14枚以下へ
- ch08で既指摘の問題が未対応のまま再発

### 中11 (Skill) — 重大度 高
- **FileChanged を公式 hook と明記** — 公式hookに存在しない (要verify・受講者を実装段階で誤らせる致命傷級)
- hook 公式29種類 表記が5箇所以上に残存
- 「Skills/legacy commands」併記4箇所 — Skill と Custom Slash Commands を別公式機能として整理せず混同
- 17枚 → 14枚への圧縮 (3統合提案)

## 3. 致命傷 (Critical issues)

| # | 内容 | 該当章 | 対応 |
|---|----|------|-----|
| C1 | **FileChanged を公式 hook と断定** | 中11 | 実在公式hook (Stop/PostToolUse) に差替 or「カスタムhook想定」と限定 |
| C2 | **hook「公式29種類」断定 (出典不明)** | 初04, 中04, 中06, 中07, 中08, 中09, 中10, 中11 | 公式9〜10種に修正 or「複数のライフサイクルイベント」に弱化 |
| C3 | **権限モード6種類 (`auto`/`dontAsk`含む)** | 初04, 中08 | 公式4種 (default/acceptEdits/plan/bypassPermissions) に修正 |
| C4 | **Skills と Custom Slash Commands を「legacy/推奨」関係で混同** | 中00, 中02, 中09, 中11 | 別公式機能として両立記述 (手動 vs 自律発動) |
| C5 | **Python 3.12 例として walrus `:=` (実際は3.8由来)** | 初02 | 3.10+ `match`文 or 3.12 `type`文に差替 |
| C6 | **advisor tool ID `advisor_20260301`・beta header・`platform.claude.com` 断定** | 中06, 中10 | 公式docs再確認・未verify部分削除 |
| C7 | **harness Engineering Blog 2025-11 / 2026-03 断定引用** | 全章で連鎖 | URL/タイトル/日付verify or「Anthropicが用いる概念」に弱化 |
| C8 | **CLAUDE.local.md を現行階層として記載** (deprecated疑) | 初02, 中05 | 「古い形式・現在は @path import 推奨」と注記 |
| C9 | **MEMORY.md「200行/25KB自動読込」固定値** | 中04, 中05 | 出典明記 or「(本リポジトリの場合)」と限定 |
| C10 | **スラッシュコマンド `$N` を0ベースと説明** (Bash由来で1ベースが通説) | 中01 | 1ベースに訂正 (要verify) |
| C11 | **「カスタムコマンドはスキルにマージと公式明記」未出典断定** | 中01, 中10 | 公式docs該当箇所引用 or 表現弱化 |
| C12 | **サブエージェント呼出5方式 (`@-mention`・`--agent` CLI)** | 中05 | 公式3方式 (自動委譲/明示指定/Agentツール) に縮小検討 |
| C13 | **`.claude/commands/` を "legacy" 表記** | 中01 | 「単一ファイル形式」に変更 (現役機能) |
| C14 | **SubAgentStop ↔ SubagentStop 表記揺れ** | 中07 | プロジェクト統一表記に置換 (公式英語表記要verify) |

## 4. 横断的な残存問題

| 問題 | 影響範囲 | 全体対応方針 |
|----|----|----|
| **スライド密度過多** (10-12枚推奨に対し15〜41枚) | 19章中16章 | 全章で統合パスを通す — 特に中04 (41枚)・中05 (35枚)・中10 (28枚)・中07 (28枚) は最優先 |
| **公式仕様の未verify断定** (hook 29種・harness記事・advisor ID・MCP等) | 11章 | Anthropic公式docs (docs.anthropic.com/claude-code/) で一括verify → 表現を一斉弱化 |
| **Skills と Custom Slash Commands の混同** | 中00/02/09/11+初03 | 中級編全章で用語統一: Skill=自律発動 / Slash Command=手動起動 を別物として整理 |
| **フック文型が機能列挙型・痛点呼びかけ不足** | 13章 | カバー副題を痛点直撃型 (「〜した経験ありませんか?」) へ前倒し |
| **未注釈の専門用語** (YAML frontmatter, ライフサイクル, jq, stderr, exit code 2, chunk, TL;DR) | 全章 | 初出時の括弧書き短説明を徹底 (社会人2-3年目ターゲット適合) |
| **`v4/v5/なぎなた/handoff/rehydrate` 削除指示** | 全章 | **完全遵守済 (PASS)** |

## 5. 全体所見

殿削除指示4項目 (handoff/rehydrate/v4/v5/なぎなた) は19章全てで100%完全遵守されており、章構成・3階層モデルの一貫性・章間ブリッジ設計は良質。構造面の品質は到達済み。一方、Anthropic公式仕様面の未verify断定が**章を跨いで連鎖累積**しており、特に「hook 29種類」「Effective harnesses for long-running agents 2025-11」「advisor_20260301」「権限モード6種」「Skills/legacy commands混同」の5系統は単独章レビューでは指摘されても次章で同表現が再発する構造問題。中11の `FileChanged` 公式hook誤記は実装段階で受講者を必ず誤らせる致命傷で最優先対応。スライド数は19章中16章で推奨上限を超過しており、中04 (41枚) を筆頭に統合圧縮が体系的に必要。

## 6. 判定

**⚠️ 修正必要**

公開準備未完了。**3段階の対応が必須**:
1. **致命傷層** (C1〜C14): Anthropic公式docs一括verifyによる訂正/弱化を全章横断で1パス実施 (特にC1 FileChanged・C2 hook 29種・C4 Skill/SC混同・C5 walrus誤記 は録音前必須)
2. **構造層**: 中04/05/07/10 のスライド統合を最優先 (各章10枚以上の超過)
3. **UX層**: フック文型を痛点呼びかけ型へ前倒し・未注釈専門用語の括弧補足

致命傷層・構造層の対応後に再レビュー → ✅公開準備完了 へ昇格可能。
