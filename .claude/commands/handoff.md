現在の作業状態を引き継ぎファイルに保存します。

以下の手順で実行してください：

1. 自分のagent_idを確認する:
   `tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}'`

2. タイムスタンプを取得する:
   `date "+%Y%m%d-%H%M"`

3. queue/handoffディレクトリを作成する:
   `mkdir -p queue/handoff`

4. 以下の内容でhandoffファイルを作成してください:
   保存先: queue/handoff/{agent_id}_{YYYYMMDD-HHMM}.md

   ## Agent
   - agent_id: {agent_id}
   - timestamp: {YYYYMMDD-HHMM}

   ## Goal / Scope
   - 現在取り組んでいるcmd/subtask IDと目的（task YAMLから）
   - スコープ外（やらないこと）

   ## Key Decisions
   - 採用した設計・アプローチと理由
   - 却下した選択肢と理由

   ## Done / Pending
   ### 完了
   - [x] 完了した作業項目
   ### 未完了
   - [ ] 残っている作業項目

   ## Next Actions
   （3〜7個、140文字以内/項目）
   1. 次にやること

   ## Affected Files
   - ファイルパス（行番号があれば記載）

   ## Risks / Unknowns
   - リスクや不明点、確認方法

5. git statusとgit diff --name-only HEADの結果も含める

6. 保存後、ファイルパスを確認してください。
