# Udemy 19章 公式仕様 verify 結果 — 確定修正リスト

| 項目 | 内容 |
|------|------|
| 調査日 | 2026-05-14 |
| 調査者 | shogun (将軍) |
| モデル | Opus 4.7 + effort high (WebFetch ツール経由で公式ドキュメント verify) |
| 対象 | 初級v4 7章 + 中級v5 12章 全19章の「要verify」47項目 |
| 公式ドキュメント | 8カテゴリ (hooks/memory/skills/sub-agents/permissions/mcp/commands/docs) |

---

## 📊 集計

| Verdict | 件数 | 意味 |
|---------|------|------|
| ❌ 齟齬 | 17 | 公式仕様と矛盾・**修正必須** |
| 🟡 部分一致 | 18 | 範囲が狭い・補強推奨 |
| ✅ 一致 | 7 | 修正不要 |
| ❓ 判定不能 | 5 | 別ソース要 |

| 優先度 | 件数 | 含む verdict |
|--------|------|--------------|
| **高** | 17 | ❌齟齬14 + 🟡3 |
| 中 | 22 | 🟡15 + ❌3 + ❓4 |
| 低 | 8 | ✅7 + ❓1 |

---

## 📌 用語整理 (殿2026-05-14指摘反映)

「スラッシュコマンド」の階層を明示する:

| 区分 | 例 | 公式? | 講座での扱い |
|------|----|-------|------------|
| **スラッシュコマンド機構** (`/<name>` 機能自体) | - | ✅ **公式機能** | 講座で説明OK |
| **組み込みコマンド** | `/init` `/memory` `/agents` `/plan` `/model` `/effort` `/mcp` `/permissions` `/context` `/clear` `/diff` 等 | ✅ **公式組み込み** | 説明OK・公式ドキュメント引用可 |
| **バンドルスキル** | `/loop` `/schedule` `/simplify` `/debug` `/batch` `/claude-api` `/security-review` `/review` | ✅ **公式バンドル** | 説明OK |
| **独自カスタムスラッシュコマンド** | `/handoff` `/advisor` `/rehydrate` 等 | ❌ **本リポジトリ独自** | 「本講座 (本リポジトリ) 独自のカスタム」と注記必須・受講者が再現するには SKILL.md or `.claude/commands/<name>.md` 雛形を提示 |
| **`/command` 表記** | - | ❌ **公式にも本リポジトリにも非存在** | 誤記の可能性・「カスタムスラッシュコマンド (`/<任意名>`)」に書き換え推奨 |

→ `/handoff` `/advisor` `/rehydrate` を講座で扱うこと自体は問題なし。**「公式組み込みではない・本リポジトリ独自実装」と明示**して、受講者が SKILL.md or `.claude/commands/` で自作する手順を併記すれば成立する。

---

## 🚨 優先度【高】17項目 (launch前最優先修正)

### v09 ❌齟齬 — beginner_ch04_history_v4
- **問題**: Hookタイミング数要verify (L3誕生② (L159-169))
- **公式仕様**: 公式hookイベントは29種類(SessionStart/Setup/UserPromptSubmit/PreToolUse/PostToolUse/Notification/Stop/SubagentStop/PreCompact/PostCompact/SessionEnd等)。3つに限定は誤り。
- **修正案**: 「PreToolUse/PostToolUse/Stop等の主要タイミング(全29種類)」と書き換え、誕生時期の象徴例として3つを挙げるなら「代表例」と明示。

### v12 ❌齟齬 — beginner_ch05_hook_v4
- **問題**: hook引数受取仕様要verify (L267-275 (pretool_check.sh)、L313-323 (ミニ演習))
- **公式仕様**: 公式hookはコマンドフックの場合 stdin JSON payload で入力を受け取る (例: `COMMAND=$(jq -r '.tool_input.command' < /dev/stdin)`)。$1引数や$CLAUDE_TOOL_INPUT環境変数は公式仕様に存在しない。
- **修正案**: pretool_check.sh を `INPUT=$(cat); COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')` 形式に全面書き換え。$1/$CLAUDE_TOOL_INPUT記述を全削除。致命傷ゆえ最優先修正。

### v13 ❌齟齬 — beginner_ch05_hook_v4
- **問題**: Hookイベント数要verify (L114, L117)
- **公式仕様**: 公式hookイベントは29種類(SessionStart/Setup/UserPromptSubmit/UserPromptExpansion/PreToolUse/PermissionRequest/PermissionDenied/PostToolUse/PostToolUseFailure/PostToolBatch/Notification/SubagentStart/SubagentStop/TaskCreated/TaskCompleted/Stop/StopFailure/TeammateIdle/InstructionsLoaded/ConfigChange/CwdChanged/FileChanged/WorktreeCreate/WorktreeRemove/PreCompact/PostCompact/Elicitation/ElicitationResult/SessionEnd)。
- **修正案**: 「Hookには29種類のイベント(代表的なものは以下7つ)」と表現を改め誇大断定を回避。

### v14 ❌齟齬 — beginner_ch05_hook_v4
- **問題**: SubAgentStop表記要verify (L117)
- **公式仕様**: 公式表記は SubagentStop (aは小文字)。SubAgentStop は存在しない。
- **修正案**: 全章で SubAgentStop → SubagentStop に grep -r 一括置換。コピペ動作不可になる致命傷。

### v15 ❌齟齬 — beginner_ch06_outro_v4
- **問題**: MCP定義要verify (S8 L137-141付近(青色ブロックのMCP説明))
- **公式仕様**: 公式定義は『AI ツール統合のためのオープンソース標準』であり、Claude Code を『数百の外部ツールとデータソースに接続』し、サーバーが『ツール、データベース、API へのアクセスを提供する』もの。用途例は課題追跡・監視データ分析・DB クエリ・デザイン統合・ワークフロー自動化・外部イベント対応であり、『記憶拡張』という説明は公式ドキュメントに一切登場しない。
- **修正案**: S8 L137-141 の MCP 定義を『LLM と外部ツール/データソース/API を繋ぐオープン標準プロトコル』に改め、記憶拡張は『claude-mem 等の一用途例』として後段で補足する形に修正せよ。

### v19 ❌齟齬 — intermediate_v5_ch00_intro
- **問題**: hook4種要verify (L177)
- **公式仕様**: 公式hookイベントは29種類。4種類限定は誤り。
- **修正案**: 「自動で動かす — 主要4つのhookを軸に(全29種類のうち代表)」と明示。断定を避け代表例として位置付け。

### v20 ❌齟齬 — intermediate_v5_ch00_intro
- **問題**: /command表記要verify (L188-L198)
- **公式仕様**: 公式の「すべてのコマンド」表に `/command` という組み込みコマンドは存在しない。独自コマンドは Skills (`.claude/skills/<name>/SKILL.md`) で作成し、ディレクトリ名が `/<name>` となる (旧 `.claude/commands/<name>.md` も legacy として継続動作)。「カスタムコマンドはスキルにマージされました」と公式に明記。
- **修正案**: 「/command」という単一コマンド表記をやめ、「カスタムスラッシュコマンド (Skills または `.claude/commands/<name>.md`)」と書き換え、`<name>` の部分が自分で命名する識別子であることを明示せよ。

### v28 ❌齟齬 — intermediate_v5_ch04_long_text_solution
- **問題**: PreCompact公式性要verify (「本編4主役+附録の全体図」スライド)
- **公式仕様**: PreCompact は公式hookイベント (29種類の1つ・「Before context compaction」)。PostCompact も公式。
- **修正案**: PreCompactを「附録(公式機能ではない)」分類から「公式hookイベント」分類へ移動。「スクリプト実装は著者独自/イベント自体は公式」と明記。

### v29 ❌齟齬 — intermediate_v5_ch05_role_files
- **問題**: instructions命名規約要verify (L139-L155, L323-L327, L344-L347, L367-L378)
- **公式仕様**: 公式ドキュメントには `instructions/` ディレクトリへの言及は一切なし。公式が推奨する分割先は ①.claude/rules/ (パススコープ可能なルール)・②.claude/skills/ (オンデマンド読込) ・③@path imports (CLAUDE.md内)。
- **修正案**: 「instructions/email.md」等は講師独自の運用パターンである旨を明記するか、公式機能である `.claude/rules/` または `skills/` に置換。Claude Code公式の標準と誤認させない注釈を追加。

### v35 ❌齟齬 — intermediate_v5_ch07_hooks
- **問題**: 4つのhook網羅要verify (L120-L131 (4つのフック表) / L21 (cover サブタイトル))
- **公式仕様**: 公式hookイベントは29種類。Notification/Stop/SubagentStop/PreCompact/PostCompact/SessionEnd/TaskCreated/InstructionsLoaded等4つでは網羅不可。
- **修正案**: 「主要4つのhookでAIの動作の代表的タイミングをカバー(全29種類の中から実用度の高い4つを抜粋)」へ。「全タイミング網羅」は削除。

### v40 ❌齟齬 — intermediate_v5_ch09_business_integration
- **問題**: /handoff公式性要verify (L100付近 (/handoff言及箇所))
- **公式仕様**: 公式コマンド表 (https://code.claude.com/docs/ja/commands) に `/handoff` は掲載されていない。組み込み・バンドルスキルどちらでもなく、本リポジトリ独自の `.claude/commands/handoff.md` 実装。
- **修正案**: 「/handoff は本講座 (本リポジトリ) 独自のカスタムスラッシュコマンドであり、Claude Code 標準には含まれない」と注記を入れよ。受講者が自前で作る場合の SKILL.md or `.claude/commands/handoff.md` 雛形を提示せよ。

### v43 ❌齟齬 — intermediate_v5_ch10_reference
- **問題**: /advisor公式性要verify (L102, L186, L210, L213, L222)
- **公式仕様**: 公式コマンド表に `/advisor` は掲載されていない。組み込みでもバンドルスキルでもない。受講者環境では存在しない。
- **修正案**: 「/advisor は本リポジトリ独自スキルである」旨を明示。または公式の `/review`・`/security-review`・`/simplify` などの代替を案内し、advisor を扱う場合は SKILL.md の自作手順を併記せよ。

### v44 ❌齟齬 — intermediate_v5_ch10_reference
- **問題**: /command表記要verify (L73, L173, L215, L210)
- **公式仕様**: v20 と同じ。公式に `/command` という単一コマンドは存在せず、カスタムスラッシュコマンドは Skills (`.claude/skills/<name>/SKILL.md`) で命名・作成する。`.claude/commands/<name>.md` も legacy として動作。
- **修正案**: 「/command」表記を全削除し、「カスタムスラッシュコマンド (`/<任意名>` を Skills で定義)」に統一せよ。L73, L173, L210, L215 全箇所修正。

### v47 ❌齟齬 — intermediate_v5_ch11_skill
- **問題**: Skillファイル形式要verify (L96-L102 (構造), L137 (Step 3))
- **公式仕様**: 公式は『各スキルは SKILL.md をエントリポイントとするディレクトリです』と明記。標準形式は `.claude/skills/<skill-name>/SKILL.md` で、サポートファイル(template、examples/、scripts/ 等)を同ディレクトリに置ける。単一 .md ファイルは `.claude/commands/` 互換動作で動くが、スキル本来のディレクトリ形式が推奨。
- **修正案**: 講座記述を『.claude/skills/<name>/SKILL.md』ディレクトリ形式を標準として提示する形に修正。単一 .md は『.claude/commands/ 由来の互換動作で動作するがサポートファイル機能が使えない劣後形式』と注釈。本プロジェクトの skill-creator/senkyou 等が採用しているディレクトリ形式が公式標準である旨明示。

### v23 🟡部分一致 — intermediate_v5_ch01_command
- **問題**: Skill自律呼出要verify (L154-165 (使い分け表)、L207-216 (Skill 布石))
- **公式仕様**: 公式仕様の配置パスは `.claude/skills/<skill-name>/SKILL.md` (ディレクトリ+SKILL.md)。自律呼出は『Claude は会話に関連する場合に自動的にスキルを読み込む』ことができ、判定根拠は『description は Claude がスキルを自動的に読み込むかどうかを決定するのに役立ちます』(description マッチ方式) で正しい。
- **修正案**: 配置先表記を『.claude/skills/*.md』から『.claude/skills/<name>/SKILL.md』に修正。自律呼出の発火条件は『description のキーワードマッチ』である旨を明記。

### v27 🟡部分一致 — intermediate_v5_ch04_long_text_solution
- **問題**: MEMORY.md自動読込要verify (「実践: MEMORY.mdに書く」スライド)
- **公式仕様**: 公式: 「`MEMORY.md` の最初の 200 行、または最初の 25KB のいずれか先に来る方が、すべての会話の開始時に読み込まれます」。ただし格納先は「プロジェクト内」ではなく `~/.claude/projects/<project>/memory/MEMORY.md` (マシンローカル、git管理外)。自動メモリ機能はv2.1.59以降。
- **修正案**: 200行/25KBは公式正解。ただし「プロジェクト内のMEMORY.md」は誤り。正しくは「~/.claude/projects/<project>/memory/MEMORY.md (マシンローカル・git管理外)」に修正必須。

### v46 🟡部分一致 — intermediate_v5_ch11_skill
- **問題**: Skill description要verify (L113-L116)
- **公式仕様**: 公式の description 例は『Summarizes uncommitted changes and flags anything risky. Use when the user asks what changed, wants a commit message, or asks to review their diff.』のように『何をするか + Use when ユースケース前置き』形式。公式は『主要なユースケースを前置きしてください』『ユーザーが自然に言うキーワードが含まれていることを確認します』を推奨。トリガーフレーズ列挙は公式例には無いが、キーワード含有という意味では合致。
- **修正案**: description 例を公式に揃え『〇〇する。Use when ユーザーが××を尋ねるとき、××したいとき』形式に変更。日本語起動フレーズ列挙パターンはローカル運用拡張として注記し、公式推奨は『自然文+ユースケース前置き』である旨明示。

---

## ⚠️ 優先度【中】22項目

| ID | 章 | Verdict | 修正の要点 |
|----|----|---------|-----------|
| v17 | beginner_ch06_outro_v4 | ❌齟齬 | 「imports」を「.md仲間」と並列化するのは概念混同。「CLAUDE.md / skills / commands」の3つを並列にし、imports はC... |
| v25 | intermediate_v5_ch03_lost_in_middle | ❌齟齬 | 「hook = AIのライフサイクルイベントに処理を差し込む仕組み。本章ではUserPromptSubmit hookで関連資料を自動注入する用法を紹介」と広義... |
| v38 | intermediate_v5_ch08_fail_safe | ❌齟齬 | 「禁止操作リスト(本講座独自の設計パターン名・PreToolUse hookで実装)」と明示し、Claude Code標準機能との誤認を防ぐ。 |
| v01 | beginner_ch00_intro_v4 | 🟡部分一致 | 「hook = AIのライフサイクルイベント(セッション開始/プロンプト送信/ツール実行前後/圧縮前/終了等)に任意の処理を差し込む仕組み。安全装置はその代表的... |
| v02 | beginner_ch01_prompt_v4 | 🟡部分一致 | L3行を「hooks/skills/sub-agentsで AI のライフサイクルを制御する層」など広義表現に。安全装置は代表例として補足。 |
| v03 | beginner_ch02_claude_md_v4 | 🟡部分一致 | 「Claude Codeを再起動」→「新しい会話/セッションを開始すると」に修正。/clearや/compactの後も再注入される旨を補足するとより正確。 |
| v04 | beginner_ch02_claude_md_v4 | 🟡部分一致 | 「起動時に自動読込」は正しいが、最低限①ユーザー(~/.claude/CLAUDE.md)②プロジェクト(./CLAUDE.md)の2階層と、ディレクトリツリー... |
| v05 | beginner_ch03_md_family_v4 | 🟡部分一致 | 注意ボックスに「呼出は自然言語/自動委譲/@-mention/`--agent` CLI フラグの4方式」と追記し、@-mention と `--agent` ... |
| v06 | beginner_ch03_md_family_v4 | 🟡部分一致 | 配置場所『.claude/skills/』は正しいが、正式形式は『.claude/skills/<skill-name>/SKILL.md』ディレクトリ構造であ... |
| v08 | beginner_ch03_md_family_v4 | 🟡部分一致 | 「プロジェクトCLAUDE.mdがglobalより優先」は方向性は正しいが、厳密には「上書きではなく連結。プロジェクト指示が後に読まれるため、矛盾時はClaud... |
| v10 | beginner_ch04_history_v4 | 🟡部分一致 | 「許可・確認・禁止の3段」は Allow/Ask/Deny ルールとしては正しいが、これは2軸構造の片側のみ。Permission Mode (default/... |
| v16 | beginner_ch06_outro_v4 | 🟡部分一致 | 「18本の実装例(主要hookイベントをカバー)」と表現を限定。「網羅」を避け「主要カテゴリの実装例」へ。 |
| v21 | intermediate_v5_ch00_intro | 🟡部分一致 | 『常駐道具』は誤解を招く。『再利用可能なワークフロー定義(プレイブック)で、必要時にオンデマンド読込される業務領域パッケージ』のような表現に修正推奨。 |
| v22 | intermediate_v5_ch01_command | 🟡部分一致 | (1) Skills 統合 (`.claude/skills/<name>/SKILL.md` 推奨・legacy `.claude/commands/` 併存... |
| v30 | intermediate_v5_ch05_role_files | 🟡部分一致 | L221-L246 で `.claude/agents/<name>.md` への YAML フロントマター定義方法と Agent (旧 Task) ツール経由... |
| v31 | intermediate_v5_ch05_role_files | 🟡部分一致 | 「CLAUDE.md自動読込」はClaude Code固有である旨を明記。他ツール(Cursor=.cursorrules、Windsurf=.windsurf... |
| v39 | intermediate_v5_ch08_fail_safe | 🟡部分一致 | BLOCK制御プロトコル(exit code 2 + stderr or JSON permissionDecision:deny)の最小例を1スライド追加。実... |
| v45 | intermediate_v5_ch10_reference | 🟡部分一致 | 「永続記憶」=公式「自動メモリ」(MEMORY.md+トピックファイル)であることを明示。「自動検索」は曖昧なので「Claudeが必要時にトピックファイルをオン... |
| v24 | intermediate_v5_ch02_failure_patterns | ❓判定不能 | 『5つ頼んで3つしか出来ない』のような具体数は経験談であり公式仕様ではない旨を明示するか、あるいは『複数タスクをまとめると追従率が下がる場合がある』程度の控えめ... |
| v26 | intermediate_v5_ch03_lost_in_middle | ❓判定不能 | 『Context Rot』はコミュニティ/研究用語 (Chroma 等が提唱) である旨を明示し、容量上限・Lost in the Middle と同格の『公式... |
| v37 | intermediate_v5_ch07_hooks | ❓判定不能 | 『ハーネスエンジニアリングの典型パターン』は本講座 (multi-agent-shogun プロジェクト) 固有の概念整理である旨を明示し、Anthropic ... |
| v42 | intermediate_v5_ch09_business_integration | ❓判定不能 | claude-mem 固有 UI の verify には別ソース(claude-mem 公式 README/GitHub)が必要。公式 MCP doc の範囲で... |

---

## 🟢 優先度【低】8項目 (補強推奨・必須でない)

| ID | 章 | Verdict | 補強案 |
|----|----|---------|--------|
| v11 | beginner_ch04_history_v4 | ❓判定不能 | 公式リリースノート/changelog を別途確認し、断定を避け「2024〜2025にかけて」など幅を持たせる。 |
| v07 | beginner_ch03_md_family_v4 | ✅一致 | 修正不要。余裕があれば「最大5ホップの再帰インポート可」「相対パスはインポート元ファイル基準」を補足するとより精緻。 |
| v18 | beginner_ch06_outro_v4 | ✅一致 | 修正不要。「ライフサイクルイベント」は公式呼称と一致。 |
| v32 | intermediate_v5_ch06_advisor | ✅一致 | 修正不要。ただし『beta』であり将来 identifier が変わる可能性がある旨を一行注記すると講座の耐用年数が伸びる。 |
| v33 | intermediate_v5_ch06_advisor | ✅一致 | 修正不要。platform.claude.com は Anthropic の正式 Console/Docs ドメインとして稼働中 (Agent SDK ページか... |
| v34 | intermediate_v5_ch06_advisor | ✅一致 | 修正不要。ただし『executor は client/Claude Code 側で動き、advisor 部分のみ server-side で実行』というハイブリ... |
| v36 | intermediate_v5_ch07_hooks | ✅一致 | 修正不要。ただし『上位互換』の根拠として『公式がスキルは追加機能を提供と明記』を脚注で補強するとより堅牢。 |
| v41 | intermediate_v5_ch09_business_integration | ✅一致 | PostToolUse自体は公式名と一致。ただし ch07 で29種類のhook全体像を提示しない場合は補足注釈推奨。 |

---

## 📁 章別 修正項目数

| 章 | 高 | 中 | 低 | 合計 |
|----|----|----|----|------|
| beginner_ch00_intro_v4 | 0 | 1 | 0 | 1 |
| beginner_ch01_prompt_v4 | 0 | 1 | 0 | 1 |
| beginner_ch02_claude_md_v4 | 0 | 2 | 0 | 2 |
| beginner_ch03_md_family_v4 | 0 | 3 | 1 | 4 |
| beginner_ch04_history_v4 | 1 | 1 | 1 | 3 |
| beginner_ch05_hook_v4 | 3 | 0 | 0 | 3 |
| beginner_ch06_outro_v4 | 1 | 2 | 1 | 4 |
| intermediate_v5_ch00_intro | 2 | 1 | 0 | 3 |
| intermediate_v5_ch01_command | 1 | 1 | 0 | 2 |
| intermediate_v5_ch02_failure_patterns | 0 | 1 | 0 | 1 |
| intermediate_v5_ch03_lost_in_middle | 0 | 2 | 0 | 2 |
| intermediate_v5_ch04_long_text_solution | 2 | 0 | 0 | 2 |
| intermediate_v5_ch05_role_files | 1 | 2 | 0 | 3 |
| intermediate_v5_ch06_advisor | 0 | 0 | 3 | 3 |
| intermediate_v5_ch07_hooks | 1 | 1 | 1 | 3 |
| intermediate_v5_ch08_fail_safe | 0 | 2 | 0 | 2 |
| intermediate_v5_ch09_business_integration | 1 | 1 | 1 | 3 |
| intermediate_v5_ch10_reference | 2 | 1 | 0 | 3 |
| intermediate_v5_ch11_skill | 2 | 0 | 0 | 2 |

---

## 関連ファイル

- 個別レビュー (Pass 1): `queue/reports/review/*.review.md` (19件)
- 1ページ品質サマリ: `queue/reports/2026-05-14_beginner_intermediate_quality_summary.md`
- 抽出 JSON: `/tmp/verify_items.json` (47項目)
- グループ別 verify 結果: `queue/reports/verify/group_{1-8}.verify.md`
- 集約 JSON: `/tmp/verify_merged.json`