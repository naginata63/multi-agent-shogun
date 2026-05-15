# Udemy 19章 修正フェーズ用 章間統一表記ガイド (Canonical Terms Guide)

**用途**: Pass 4 修正フェーズで各章を書き換える際、章間齟齬を構造的に排除するため。各章修正前に本ガイドを context として渡し、用語・定義・配置パスを揃える。

**適用日**: 2026-05-14

**根拠ソース**:
- Claude Code 公式ドキュメント (https://code.claude.com/docs/ja/)
- Anthropic Advisor Tool 公式 (https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)
- 47 項目 verify 結果 (queue/reports/2026-05-14_udemy_verify_*.md)

---

## 1. hook 定義

✅ **正典表現**: 「hook = AI のライフサイクルイベント (セッション開始/プロンプト送信/ツール実行前後/圧縮前/終了等) に任意のシェルコマンド・HTTP・MCP ツール・プロンプトを発火させる仕組み。安全装置はその代表的用途の一つ」

❌ **避けるべき表現**:
- 「AI の動きに制限をかける仕組み」(狭義すぎる)
- 「安全装置」単独定義 (用途の一つに過ぎぬ)
- 「AI に質問を送る瞬間に自動で関連資料を検索して一緒に送る仕組み」(UserPromptSubmit + additionalContext の一用途を全体定義に流用)

📚 **根拠**: 公式 hooks は 29 種類のライフサイクルイベントで任意処理を差し込む広義機構。安全装置/関連資料注入はいずれも一用途。**verify ID**: v01, v02, v25

---

## 2. hook 種類数 (29 種)

✅ **正典表現**: 「Hook イベントは公式で 29 種類 (SessionStart / Setup / UserPromptSubmit / UserPromptExpansion / PreToolUse / PermissionRequest / PermissionDenied / PostToolUse / PostToolUseFailure / PostToolBatch / Notification / SubagentStart / SubagentStop / TaskCreated / TaskCompleted / Stop / StopFailure / TeammateIdle / InstructionsLoaded / ConfigChange / CwdChanged / FileChanged / WorktreeCreate / WorktreeRemove / PreCompact / PostCompact / Elicitation / ElicitationResult / SessionEnd)。本講座では代表的な 4 つ (または 7 つ) を抜粋して解説」

❌ **避けるべき表現**:
- 「Hook は 3 つのタイミング (PreToolUse / PostToolUse / Stop)」(ch04 L159-169)
- 「Hook には 7 種類のイベント」断定 (ch05 L114, L117)
- 「4 つのフックを覚えれば AI の動作の前・後・開始時・入力時の全タイミングを網羅できます」(ch07 L120-131)
- 「自動で動かす — 4 つの hook」断定 (ch00 intro L177)
- 「18 本の実戦 hook で主要カテゴリを網羅」(ch06 L116-122)

📚 **根拠**: 公式 hook イベントは 29 種類。代表抜粋は OK だが「網羅」「全タイミング」断定は誤り。**verify ID**: v09, v13, v16, v19, v35

---

## 3. hook 引数受取仕様 (★致命傷)

✅ **正典表現**:
```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')
# または: COMMAND=$(jq -r '.tool_input.command' < /dev/stdin)
```
「コマンドフックは stdin から JSON ペイロードを受け取る」

❌ **避けるべき表現**:
- `$1` でコマンド内容を受け取る
- `$CLAUDE_TOOL_INPUT` 環境変数で受け取る
- 「`pretool_check.sh "$1"` でコマンドを検査」例

📚 **根拠**: 公式 hook はコマンド型の場合 stdin JSON payload 方式のみ。`$1` 引数・`$CLAUDE_TOOL_INPUT` 環境変数は公式仕様に**存在しない**。コピペすると動作しない致命傷ゆえ最優先修正。**verify ID**: v12

---

## 4. SubagentStop 表記 (a 小文字)

✅ **正典表現**: `SubagentStop` (a は小文字)

❌ **避けるべき表現**: `SubAgentStop` (A 大文字・公式仕様に存在せず)

📚 **根拠**: 公式表記は `SubagentStop`。`SubAgentStop` はコピペ動作不可。全章で grep -r 一括置換。**verify ID**: v14

---

## 5. Skill 配置と仕様

✅ **正典表現**:
- **標準形式**: `.claude/skills/<skill-name>/SKILL.md` (ディレクトリ + SKILL.md エントリポイント)
- **personal**: `~/.claude/skills/<skill-name>/SKILL.md`
- **legacy 互換**: `.claude/commands/<name>.md` (単一 .md 単独動作・サポートファイル機能なし)
- **読込挙動**: description のみが常駐し、本体は使用時にオンデマンド読込
- **自律発動条件**: description のキーワードマッチ
- **description 公式形式**: 「〇〇する。Use when ユーザーが××を尋ねるとき、××したいとき」(何をするか + Use when ユースケース前置き)

❌ **避けるべき表現**:
- `.claude/skills/<name>.md` の単一ファイル形式を標準として提示 (ch11 L96-102, L137)
- `.claude/skills/*.md` という配置パス表記 (ch01 L154-165)
- 「Skill = 業務領域の常駐道具」(オンデマンド読込なのに「常駐」と誤誘導)
- 日本語トリガーフレーズ列挙のみ (公式推奨は自然文 + Use when 前置き形式)

📚 **根拠**: 公式は「各スキルは SKILL.md をエントリポイントとするディレクトリ」と明記。本リポジトリの skill-creator/senkyou 等もディレクトリ形式採用。**verify ID**: v06, v21, v23, v46, v47

---

## 6. CLAUDE.md 読込挙動

✅ **正典表現**:
- **読込タイミング**: 「新しい会話/セッションの開始時に読み込む」(プロセス再起動は不要)。`/clear` や `/compact` の後もディスクから再読込される
- **階層 (4 階層)**:
  1. 管理ポリシー (`/Library/Application Support/ClaudeCode/CLAUDE.md` 等)
  2. ユーザー指示 `~/.claude/CLAUDE.md`
  3. プロジェクト指示 `./CLAUDE.md` または `./.claude/CLAUDE.md`
  4. ローカル `./CLAUDE.local.md`
- **マージ挙動**: ディレクトリツリーを上方向に歩いて全 CLAUDE.md を読込・**連結** (上書きではない)。サブディレクトリの CLAUDE.md はオンデマンド読込
- **優先順位**: 後に読まれるプロジェクト指示が矛盾時に従われやすい (上書きではなく「後勝ち」)
- **固有性**: Claude Code は `CLAUDE.md` を読む (`AGENTS.md` ではない)。Cursor は `.cursorrules`、Windsurf は `.windsurfrules`

❌ **避けるべき表現**:
- 「Claude Code を再起動 → 自動的に読み込まれる」(プロセス再起動誤解)
- 「プロジェクト CLAUDE.md が global より優先 (上書き)」(連結が正しい)
- 階層に触れず単一ファイルのように扱う説明

📚 **根拠**: 公式「各セッションの開始時に読みます」「発見されたすべてのファイルはコンテキストに連結され、互いに上書きするのではなく」。**verify ID**: v03, v04, v08, v31

---

## 7. Subagent 呼出方式

✅ **正典表現**:
- **定義場所**: `.claude/agents/<name>.md` (プロジェクト) / `~/.claude/agents/<name>.md` (ユーザー) の YAML フロントマター付き Markdown
- **呼出方式 (5 方式)**:
  1. description ベースの自動委譲
  2. 自然言語でのサブエージェント名指定
  3. @-mention (`@"agent-name (agent)"`)
  4. CLI フラグ `--agent <name>`
  5. Agent (旧 Task) ツール経由生成
- **`/agents` コマンド**: 管理用タブ付きインターフェース (呼出用ではない)
- **`/agent <name>`**: **存在しない** (混同注意)

❌ **避けるべき表現**:
- 「呼出は自然言語か自動委譲」のみ (@-mention・`--agent`・Agent ツールが欠落)
- 「ユーザーが頼むと AI が自動で起動」断定 (明示指定方式が欠落)
- `/agent <name>` 個別呼出コマンドが存在するかのような記述

📚 **根拠**: 公式は 5 方式すべてを記載。**verify ID**: v05, v30

---

## 8. imports / @path 構文

✅ **正典表現**:
- 「CLAUDE.md 内で `@path/to/import` 構文により他ファイルを取り込む機能」
- 「インポートされたファイルは展開され、CLAUDE.md と一緒に起動時にコンテキストに読込まれる」
- 「相対パス・絶対パス両方可。相対パスはインポート元ファイル基準」
- 「再帰的インポート可・最大深度 5 ホップ」
- imports は **CLAUDE.md 内部の構文機能**であり、独立した .md ファイル種別ではない

❌ **避けるべき表現**:
- 「imports」を「commands / skills / imports」の 3 つ並列で「.md 仲間」分類 (ch06 S5)
- imports が独立したファイル種別かのような誤誘導

✅ **正しい並列**: 「CLAUDE.md / skills / commands」を 3 大カテゴリとし、imports は **CLAUDE.md 内部の @path 構文として別枠**で説明

📚 **根拠**: 公式 imports は `@path/to/import` 構文機能。**verify ID**: v07, v17

---

## 9. MCP 定義

✅ **正典表現**: 「MCP (Model Context Protocol) = LLM と外部ツール・データソース・API を繋ぐオープンソース標準プロトコル。Claude Code を数百の外部ツールに接続し、サーバーがツール・データベース・API へのアクセスを提供する」

**用途例** (公式記載): 課題追跡・監視データ分析・DB クエリ・デザイン統合・ワークフロー自動化・外部イベント対応

**MCP 呼出 3 方式**:
1. 自然言語で Claude に依頼
2. `@server:protocol://resource/path` で参照
3. `/mcp__server__prompt` スラッシュコマンド

❌ **避けるべき表現**:
- 「MCP = AI の記憶を拡張する仕組み」(ch06 S8) — 公式に「記憶拡張」という説明は一切登場しない
- 記憶拡張を MCP の定義として中心に置く

✅ 「claude-mem 等の MCP サーバーは記憶拡張の**一用途例**」として後段で補足する形に。

📚 **根拠**: 公式定義は「AI ツール統合のためのオープンソース標準」。**verify ID**: v15, v42

---

## 10. スラッシュコマンド階層 (機構/組込/バンドル/独自カスタム)

修正時の最重要トピック。**4 階層を明示**して受講者が「Claude Code 標準」と「本講座独自」を混同しないようにする。

✅ **正典表現** (4 階層を明示):

| 階層 | 例 | 出所 |
|------|----|------|
| **機構** (built-in mechanism) | スラッシュコマンドという仕組み自体 | Claude Code 本体機能 |
| **組込コマンド** (built-in commands) | `/clear`, `/compact`, `/memory`, `/init`, `/agents` 等 | 公式コマンド表に掲載 |
| **バンドルスキル** (bundled skills) | `/review`, `/security-review`, `/simplify` 等 | Anthropic 公式同梱 |
| **独自カスタム** (custom skills/commands) | `/handoff`, `/advisor`, `/senkyou` 等 | 本リポジトリ独自実装 |

**カスタムコマンド作成方式**:
- **推奨**: Skills (`.claude/skills/<name>/SKILL.md`) — ディレクトリ名がコマンド名 `/<name>` になる
- **legacy 継続**: `.claude/commands/<name>.md` 単一ファイル
- 公式は「カスタムコマンドはスキルにマージされました」と明記

❌ **避けるべき表現**:
- 「`/command` (定型プロンプトの保存)」表記 — 公式に `/command` という単一コマンドは**存在しない** (ch00 L188-198, ch10 L73/L173/L210/L215)
- `/handoff` を Claude Code 標準のように記述 (ch09 L100)
- `/advisor` を Claude Code 標準スラッシュコマンドのように繰返し提示 (ch10 L102/L186/L210/L213/L222)
- 独自カスタムを「組込」「バンドル」と区別なく並列提示

✅ 独自カスタムを扱う場合は **必ず「本講座/本リポジトリ独自のカスタムスラッシュコマンドであり、Claude Code 標準には含まれない」と注記**せよ。

📚 **根拠**: 公式コマンド表に `/command`・`/handoff`・`/advisor` の掲載なし。Skills 統合明記。**verify ID**: v20, v40, v43, v44

---

## 11. Permission モデル (2 軸構造)

✅ **正典表現**: 「Permission は 2 軸構造」

- **軸 1 — 権限モード (6 種)**: `default` / `acceptEdits` / `plan` / `auto` / `dontAsk` / `bypassPermissions` — 全体動作を制御
- **軸 2 — ツール個別ルール (3 種)**: `Allow` / `Ask` / `Deny` — `deny → ask → allow` の順で評価
- **拡張**: PreToolUse フックで実行時拡張も可能

❌ **避けるべき表現**:
- 「許可・確認・禁止の 3 段」のみ (軸 1 のモード制が欠落・ch04 L159-169)
- Allow/Ask/Deny だけで Permission モデル全体を説明したように見せる

📚 **根拠**: 公式は 2 軸構造を明記。歴史背景説明としても 1 行追記で軸 1 (モード) の存在を併記必須。**verify ID**: v10

---

## 12. MEMORY.md 自動メモリ機能

✅ **正典表現**:
- **格納場所**: `~/.claude/projects/<project>/memory/MEMORY.md` (**マシンローカル・git 管理外**)
- **読込ルール**: 「MEMORY.md の最初の 200 行、または最初の 25KB のいずれか先に来る方が、すべての会話の開始時に読み込まれます」
- **構造**: MEMORY.md (インデックス) + トピックファイル群
- **トピックファイル読込**: Claude が必要時に標準 Read ツールでオンデマンド読込
- **バージョン**: v2.1.59 以降
- memory MCP とは別物

❌ **避けるべき表現**:
- 「**プロジェクト内**の MEMORY.md を自動で読み込みます」(ch04) — 正しくは `~/.claude/projects/<project>/memory/`
- 「自動検索」(公式用語に存在せず・「Claude が必要時にトピックファイルをオンデマンド読込」が正確)

📚 **根拠**: 200 行/25KB は公式正解。格納場所がマシンローカルである点が肝。**verify ID**: v27, v45

---

## 13. PreCompact / PostCompact 公式扱い

✅ **正典表現**: 「PreCompact / PostCompact は公式 hook イベント (29 種類の 1 つ)。本講座のスクリプト実装は著者独自だが、**hook イベント自体は公式機能**」

❌ **避けるべき表現**:
- PreCompact を「附録: 著者独自の運用例 (公式機能ではありません)」分類 (ch04)

✅ 「**イベント自体は公式 / スクリプト実装は著者独自**」を明確に分離せよ。

📚 **根拠**: PreCompact/PostCompact は公式 hook の「Before/After context compaction」。**verify ID**: v28

---

## 14. ハーネス / ハーネスエンジニアリング (Anthropic 公式・業界標準用語) — 【2026-05-14 殿指摘で全面訂正】

✅ **正典表現**:
- **「ハーネス」は Anthropic 公式概念**で、Engineering Blog 複数記事で扱われている業界標準用語
- 公式定義 (業界標準): **Agent = Model + Harness** — モデルを「実際に仕事を完遂する work engine」に変えるための周辺コード・設定・実行ロジック一式
- 構成要素 (公式): プロンプト・ツール・コンテキストポリシー・hooks・サンドボックス・サブエージェント・フィードバックループ・回復経路 等
- 「**ハーネスエンジニアリング**は AI エージェントを実運用で信頼できる形にするための設計分野」と紹介可
- L3 階層を扱う際: 「hooks/skills/sub-agents 等で Claude の動作を制御・拡張する層 = ハーネス層」と公式整合した広義表現を用いる
- 公式記事を参照ソースとして示せる:
  - 「Effective harnesses for long-running agents」(2025-11-26 Anthropic Engineering Blog, Justin Young 著)
  - 「Harness design for long-running application development」(2026-03-24 Anthropic Engineering Blog)
- 業界類例 (補強用): OpenAI「Harness engineering: leveraging Codex」/ Martin Fowler / LangChain / Red Hat も同用語採用

❌ **避けるべき表現**:
- 「ハーネスは**本講座独自用語**」「Anthropic 公式ではない」(過去のレビュー判定が誤り・**完全撤回**)
- 「ハーネス = AI の動きに**安全装置を付ける**だけ」狭義定義 (ch01 L3 階層テーブル) — 公式は **work engine 化全体**を指す
- 「禁止操作リスト」「典型パターン」を講座独自命名 *扱いで弱める* — 「PreToolUse hook での安全装置実装パターン」として **公式 harness の一実装例**と位置付け

📚 **根拠**:
- Anthropic Engineering Blog 公式記事 2本 (2025-11 / 2026-03) で「harness」が公式用語として使用
- 業界全体で「Agent = Model + Harness」が標準定義として確立 (2026 中盤までに完全定着)
- **verify ID 再判定**: v02 (狭義定義) は依然 🟡部分一致 (公式は広義) / v37 (典型パターン) は ✅ 概念として整合・「公式 harness の一実装パターン」と注記すれば OK / v38 (禁止操作リスト) は実装パターン名として OK
- **2026-05-14 殿指摘**: 「ハーネスエンジニアリングは Claude が 2月に言い始めた」→ 公式記事 (2025-11, 2026-03) で確認・実体は正しい・将軍の元判定が完全な誤り

---

## 15. $ARGUMENTS / 引数置換仕様

✅ **正典表現**:
- `$ARGUMENTS` = 全引数
- `$ARGUMENTS[N]` または短縮形 `$N` = **0 ベース**・`$0` が**第 1 引数**・`$1` は第 2 引数
- frontmatter で `arguments: [name1, name2]` 宣言すれば `$name1` も可
- frontmatter 全フィールド任意・`description` のみ推奨
- `` `!command` `` で動的シェル注入は公式記載あり
- `@file` 参照記法は公式 commands/skills ページに**記載なし**

❌ **避けるべき表現**:
- `$1` を第 1 引数として書く (実際は `$0` が第 1 引数)
- `@file` を Claude Code 公式機能のように扱う

📚 **根拠**: 公式仕様で 0 ベース明示。**verify ID**: v22

---

## 16. Advisor Tool

✅ **正典表現**:
- `type: "advisor_20260301"`
- `anthropic-beta: advisor-tool-2026-03-01`
- 公式 URL: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool`
- **ハイブリッド構造**: executor は client/Claude Code 側で動き、advisor 部分のみ server-side で実行 (`server_tool_use` ブロックを emit)
- **beta 機能**: identifier が将来変わる可能性あり (一行注記推奨)

📚 **根拠**: 公式ページに上記すべて明記。**verify ID**: v32, v33, v34

---

## 17. 5 タスク同時指示 / Context Rot (出典明示)

✅ **正典表現**:
- 「5 つ頼んで 3 つしか出来ない」等の**具体数は経験談**であり公式仕様/ベンチマークではない旨を明示。または「複数タスクをまとめると追従率が下がる場合がある」程度の控えめ表現に
- 「Context Rot」は**コミュニティ/研究用語** (Chroma 等提唱) であり Anthropic 公式制約ではない旨を注記
- 容量上限・Lost in the Middle と同格の「公式 3 大制約」として並べる構成は弱める

❌ **避けるべき表現**:
- 経験談を公式ベンチマークのように断定
- Context Rot を公式制約として並列扱い

📚 **根拠**: 公式に該当記述・用語ともになし。**verify ID**: v24, v26

---

## 18. instructions/ ディレクトリ命名 (VSCode + GitHub Copilot 由来・Claude Code 用に派生) — 【2026-05-14 殿指摘で更新】

✅ **正典表現**:
- **「`instructions/`」の命名・概念は VSCode + GitHub Copilot 公式仕様 `.github/instructions/NAME.instructions.md`** が原型
  - VSCode 公式: `chat.instructionsFilesLocations` 設定のデフォルトに `.github/instructions` 含む
  - フォーマット: `.instructions.md` 拡張子・YAML frontmatter に `applyTo` フィールド
  - Microsoft / GitHub のドキュメント参照可
- 本リポジトリの `instructions/<role>.md` は **VSCode Copilot 由来命名を Claude Code 用に派生** させた独自運用パターン
  - 配置場所: top-level `instructions/` (`.github/instructions/` ではない)
  - ファイル形式: `<role>.md` (`.instructions.md` 拡張子ではない)
  - 読み込み: CLAUDE.md からの明示的 Read tool 指示で実現 (Claude Code 標準の自動読込ではない)
- 講座での扱い: 「**VSCode Copilot 公式の `.github/instructions/` 規約に着想を得て、Claude Code 用にアレンジした本リポジトリ独自運用**」と明示
- 公式が Claude Code 単体で類似機能を提供する場合の選択肢: ①`.claude/rules/` (パススコープ可能なルール) ②`.claude/skills/` (オンデマンド読込) ③`@path imports` (CLAUDE.md 内)

❌ **避けるべき表現**:
- 「`instructions/` は**本講座独自**」「VSCode 由来は一切触れない」(由来を隠すと受講者が "謎の独自規約" として混乱)
- `instructions/` を **Claude Code 公式の標準**のように扱う (ch05 L139-155 等)

📚 **根拠**:
- VSCode 公式: https://code.visualstudio.com/docs/copilot/customization/custom-instructions
- GitHub Copilot 公式: `.github/instructions/NAME.instructions.md` 規約
- Claude Code 公式ドキュメントには `instructions/` への言及なし (Claude Code 単体で見れば独自)
- **verify ID 再判定**: v29 (本講座独自) は 🟡部分一致 — 由来は VSCode Copilot 公式・派生は本リポジトリ独自
- **2026-05-14 殿指摘**: 「instructions は vscode 用じゃない？」→ 由来 confirmed・将軍の元判定「本講座独自」は不正確

---

## 19. PreToolUse BLOCK 制御プロトコル

✅ **正典表現**: PreToolUse hook で BLOCK するには以下のいずれか:
1. **exit code 2** で stderr にメッセージ出力
2. stdout に JSON を返す:
```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}
```

最小例を 1 スライド追加し、実装誘発リスクを回避せよ。

📚 **根拠**: 公式 hook 仕様で明記。**verify ID**: v39

---

## 20. その他

- **PostToolUse**: 公式 hook (29 種類の 1 つ・「After a tool call succeeds」で発火・`decision:"block"` でフィードバック可)。ch07 で 29 種類全体像を提示しない場合は補足注釈推奨 (v41)
- **claude-mem UI**: claude-mem 固有 UI の verify には別ソース (claude-mem 公式 README/GitHub) が必要。公式 MCP doc の範囲では「自然文入力で MCP サーバーを呼ぶ」こと自体は一般原則と整合 (v42)
- **L3 誕生時期**: hook 機能の公式リリース年表は記載なし。「2024〜2025 にかけて」など幅を持たせる (v11)

---

## 修正時の運用ルール

1. **章を編集する前に本ガイドを必ず参照せよ**。記憶や事前知識で書き換えるな。各トピックの「✅正典表現」を引用する形で書け。

2. **断定回避 5 原則**: hook 種類数・Permission 段数・skill 配置・command 表記・MEMORY.md 格納場所の 5 領域は最優先で断定を避け、公式仕様に揃えよ。

3. **「公式機能 vs 本講座独自」を必ず分離**: `/handoff` `/advisor` `/senkyou` `instructions/` `ハーネスエンジニアリング` `禁止操作リスト` `done_gate.sh` 等を出す際は「本リポジトリ独自」注記を**省略するな**。

4. **コピペで動くコードを書け**: hook 引数受取は `INPUT=$(cat); ... | jq` 方式のみ。`$1` `$CLAUDE_TOOL_INPUT` `SubAgentStop` は**コピペ動作不可の致命傷**ゆえ全章 grep -r で殲滅せよ。

5. **章間整合 grep チェック**: 各章修正後、以下を grep して残存ゼロを確認:
   - `SubAgentStop` (大文字 A)
   - `$CLAUDE_TOOL_INPUT`
   - `/command ` (空白付き単一コマンド扱い)
   - `\.claude/skills/\*\.md` (単一ファイル前提)
   - 「Hook には [0-9]種類」「[0-9]つのフックを覚えれば」「全タイミングを網羅」

6. **章間相互参照は本ガイドのトピック番号を引用**: 「hook 種類数は本ガイド §2 参照」のように章を超えた参照は本ガイド経由で行い、章直接参照を避けよ (章番号変更耐性)。

---

## 21. 【新方針 2026-05-15】実装は Claude に書かせる前提 (受講者はプロンプト例)

殿確定 (2026-05-15):

✅ **正典方針**:
- hook シェルスクリプト・Skill (`SKILL.md`)・カスタムスラッシュコマンド (`.claude/commands/*.md`) の **実装は受講者が手書きしない**
- 受講者は **Claude (Claude Code) に「こう作って」と依頼するプロンプト** を覚える
- 講座は **「Claude にこう頼めば AI が作ってくれる」プロンプト例** を提供する

❌ **避けるべき表現**:
- 「pretool_check.sh を以下のように書きます: `INPUT=$(cat); jq -r ...`」(受講者に写経させる) → ❌
- 「SKILL.md を YAML フロントマターで書きます」(受講者に手書きさせる) → ❌

📚 **根拠**:
- 本講座のメインテーマは「**プロンプトエンジニアリング** (L1) + **コンテキストエンジニアリング** (L2) + **ハーネスエンジニアリング** (L3)」
- シェル/jq/YAML/Markdown frontmatter の文法は L1〜L3 と直接関係ない・学習負担を増やすだけ
- AI 時代の正しいスキルは「**AI に正確に指示できる力**」・実装は AI に任せる
- Claude Code は SKILL.md・hook・commands を **プロンプト 1 つで生成可能** (公式仕様)
- 受講者ペルソナ (社会人 2-3 年目・なんとか IT) はシェル/jq に詰まる → 脱落リスク

### プロンプト例の作り方 (講座本編で示すパターン)

```
[hook] 「Claude Code 用の PreToolUse hook を作って:
       - rm -rf を検知してブロック
       - stdin から JSON ペイロードを読む
       - 危険検知時は exit 2 で停止
       - `.claude/hooks/safety.sh` に保存して chmod +x も付けて」

[Skill] 「`/email-draft` という Skill を作って:
        - description: 「メール文面を起草する Skill。メール作成・返信時に使用」
        - 本体: 簡潔なビジネス日本語で・敬語・件名・宛名・本文の構造で
        - `.claude/skills/email-draft/SKILL.md` に保存して」

[カスタムスラッシュコマンド] 「`/ask-with-condition` という Skill を作って:
        - description: 「5軸条件指定で回答精度を上げるテンプレ呼出」
        - 本体: 殿の5軸条件指定プロンプトテンプレ
        - `.claude/skills/ask-with-condition/SKILL.md` に保存」
```

→ 受講者は **プロンプト + 検証** ループだけで 3 層を回す。実装は Claude が担当。
