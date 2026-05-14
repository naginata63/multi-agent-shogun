[{"id":"v05","verdict":"🟡部分一致","official_fact":"公式は `/agents` を管理用タブ付きインターフェースと明記し、`/agent <name>` というスラッシュコマンドは存在しない。ただし明示的呼出には『自然言語』『自動委譲』に加えて『@-mention (@\"agent-name (agent)\")』『CLI フラグ `--agent <name>`』『settings.json の `agent` フィールド』も公式に存在する。",
"recommendation":"注意ボックスに「呼出は自然言語/自動委譲/@-mention/`--agent` CLI フラグの4方式」と追記し、@-mention と `--agent` を欠落しないよう補強せよ。",
"priority":"中"},
{"id":"v30","verdict":"🟡部分一致","official_fact":"公式仕様ではサブエージェントは `.claude/agents/` (プロジェクト) または `~/.claude/agents/` (ユーザー) の YAML フロントマター付き Markdown ファイルで定義し、(a) description ベースの自動委譲、(b) 自然言語でのサブエージェント名指定、(c) @-mention、(d) `--agent` CLI フラグ、(e) Agent (旧 Task) ツール経由生成 の複数方法で起動できる。「ユーザーが頼むとAIが自動で起動」だけでは@-mention/明示指定の存在が欠落している。",
"recommendation":"L221-L246 で `.claude/agents/<name>.md` への YAML フロントマター定義方法と Agent (旧 Task) ツール経由起動を明示し、L280-L290 で『自動起動だけでなく @-mention や `--agent <name>` での明示指定も可能』と補足せよ。",
"priority":"中"}]
