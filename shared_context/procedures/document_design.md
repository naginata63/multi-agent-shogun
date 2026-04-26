# document_design.md — ドキュメント設計タスク手順

## 対象タスク
カリキュラム設計書・マーケ計画書・競合分析等、ドキュメント生成/改訂タスク全般。

## ワークフロー

### Step 1: 事前確認
1. `queue/shogun_to_karo.yaml` でparent_cmdの全commandを必ず読め（要約ではなく原文）
2. 既存成果物（drafts/配下等）を Read ツールで全文確認
3. `advisor()` 呼び出し（実装前必須）

### Step 2: 退避・ディレクトリ準備
1. 退避対象ファイルを `drafts/legacy/` に移動（`mv` コマンド）
2. 移動後に `ls drafts/` と `ls drafts/legacy/` で確認

### Step 3: ドキュメント生成・改訂
1. 既存ファイルを参照しながら新ファイルを Write ツールで生成
2. 大規模改訂の場合：分割して段階的に書く（1ファイルずつ完成させる）
3. acceptance_criteriaの各項目をチェックしながら進める

### Step 4: セルフQC
1. 生成ファイルを全文 Read して意図通りか確認
2. 削除/置換/追加箇所の対照表を最終報告YAMLに含める（軍師QCのため）
3. `advisor()` 呼び出し（完了前必須）

### Step 5: 完了報告
1. `queue/reports/{agent}_report_{task_id}.yaml` に報告YAML書き込み
2. `git add <dir> && git commit` （git add . 禁止）
3. `bash scripts/inbox_write.sh karo "完了報告" report_received {agent_id}` で家老通知

## 品質基準
- acceptance_criteriaの全項目を満たすこと
- 意図しない変更（既存ファイルの破壊等）がないこと
- 最終報告YAMLに変更箇所の証跡（対照表）を含めること

## 注意事項
- scope外の実装（コード/hookへの変更等）は禁止
- 大量ファイル操作前に `git add <dir> && commit` でセーブポイント作成
- API呼び出し・外部検索が必要な場合はstepsに明記されている場合のみ
