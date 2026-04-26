# advisor稼働テスト: work/dingtalk_qc/README.md確認手順（cmd_1357）

## 重要: このタスクはadvisor()の呼び出しが必須

## Step1: 実装前にadvisor()を呼ぶ（必須）
作業を始める前に `advisor()` ツールを呼び出し、以下について助言を得よ:
- 「work/dingtalk_qc/README.md の内容確認タスクを始めます。進め方について助言をください。」

advisor の応答を踏まえて以降の作業を進めること。

## Step2: README.mdを読んで内容確認
`work/dingtalk_qc/README.md` を Read ツールで読み込む。

確認する観点:
- 記載されているスクリプト名・パスが実際に存在するか（Glob/Grep で確認）
- 手順・コマンド例に古い情報・矛盾がないか
- CLAUDE.mdに記載されたルールと矛盾していないか

## Step3: 問題があれば修正、なければスキップ
- 問題あり → Edit ツールで修正（軽微な誤記のみ。大幅な書き直しは不要）
- 問題なし → 修正不要。「確認済み、問題なし」を記録

## Step4: 完了前にもう一度advisor()を呼ぶ（必須）
成果物（確認結果・修正内容）をまとめた上で `advisor()` を呼び出す:
- 「README.mdの確認が完了しました。見落としがないか最終レビューをお願いします。」

advisor のフィードバックを反映してから次Stepへ進む。

## Step5: 報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽2号、subtask_1357a完了。README確認結果とadvisor呼び出し結果を報告。" \
  report_completed ashigaru2
```
