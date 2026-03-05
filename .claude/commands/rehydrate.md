最新の引き継ぎファイルを読み込んで作業を再開します。

以下の手順で実行してください：

1. 自分のagent_idを確認する:
   `tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}'`

2. 最新の引き継ぎファイルを見つける:
   `ls queue/handoff/{agent_id}_*.md 2>/dev/null | sort | tail -1`

3. 引き継ぎファイルが見つかった場合:
   - そのファイルをReadする
   - 「Next Actions」セクションから作業を再開する
   - 必要に応じてqueue/tasks/{agent_id}.yamlも読む

4. 引き継ぎファイルが見つからない場合:
   - queue/tasks/{agent_id}.yaml を読んで作業状態を確認する
   - instructions/{agent_id_type}.md を読んでロールを確認する
     （agent_id_type: shogun/karo/gunshi、またはashigaruNならashigaru）
