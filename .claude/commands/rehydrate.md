最新の引き継ぎファイルを読み込んで作業を再開します。

以下の手順で実行してください：

1. 自分のagent_idを確認する:
   `tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}'`

2. 最新の引き継ぎファイルを見つける:
   `ls queue/handoff/{agent_id}_*.md 2>/dev/null | sort | tail -1`

3. **鮮度チェック**: ファイル名のタイムスタンプを現在時刻と比較する。
   - **24時間以内**: そのまま信頼して4へ
   - **24時間より古い**: handoffの内容は古い可能性がある。queue/tasks/{agent_id}.yaml と
     `curl -s -w "\nHTTP %{http_code}\n" "http://192.168.2.4:8770/api/cmd_list?status=in_progress&slim=1"`
     を先に確認し、handoffと矛盾する場合は**現在のtask YAML/APIを正とする**（handoffは背景知識として使う）

4. 引き継ぎファイルが見つかった場合:
   - そのファイルをReadする
   - **「実行中バックグラウンドプロセス」セクションがあれば、各プロセスを `pgrep -af <script名>` で生存確認**
     - 生きている → 完了通知を待つ（自分で再起動・重複起動するな）
     - 死んでいる & 未完了 → ログ/出力先を確認し、再開が必要か判断
   - 「Next Actions」セクションから作業を再開する
   - 必要に応じてqueue/tasks/{agent_id}.yamlも読む

5. 引き継ぎファイルが見つからない場合:
   - queue/tasks/{agent_id}.yaml を読んで作業状態を確認する
   - instructions/{agent_id_type}.md を読んでロールを確認する
     （agent_id_type: shogun/karo/gunshi、またはashigaruNならashigaru）
