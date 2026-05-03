---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-size: 1.7em; padding: 50px 70px; background: #fafafa; display: flex !important; flex-direction: column !important; justify-content: flex-start !important; align-content: flex-start !important; align-items: stretch !important; }
  section h1:first-child, section h2:first-child { margin-top: 0; }
  section.cover { background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%); color: #fff; text-align: center; justify-content: center !important; align-items: center !important; }
  section.cover h1 { font-size: 1.6em; color: #fff; border: none; }
  section.cover h2 { font-size: 1.0em; color: #fde68a; }
  section.cover .meta { font-size: 0.7em; opacity: 0.85; margin-top: 1.5em; }
  h1 { color: #1e3a8a; border-bottom: 3px solid #1e3a8a; padding-bottom: 0.2em; font-size: 1.4em; }
  h2 { color: #2563eb; font-size: 1.1em; }
  h3 { color: #4b5563; font-size: 1.0em; }
  blockquote { border-left: 4px solid #f59e0b; background: #fffbeb; padding: 0.4em 0.8em; font-style: italic; color: #78350f; }
  code { background: #f0f0f0; padding: 1px 5px; border-radius: 3px; font-size: 0.85em; }
  pre { background: #1e293b; color: #f1f5f9; padding: 0.6em; font-size: 0.7em; border-radius: 6px; }
  table { font-size: 0.78em; border-collapse: collapse; }
  th { background: #1e3a8a; color: #fff; padding: 0.4em 0.8em; }
  td { padding: 0.4em 0.8em; border: 1px solid #ddd; }
  .big { font-size: 1.6em; font-weight: bold; color: #1e3a8a; }
  .free { background: #facc15; color: #78350f; padding: 2px 8px; border-radius: 4px; font-size: 0.65em; font-weight: bold; }
---

<!-- _class: cover -->

# Supervisor Pattern: 完了検証 Gate の実装
## AIエージェントの「完了」を機械的に検証する

<div class="meta">
中級編 v4 — 第11章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第11章へようこそ。テーマはSupervisor Patternです。エージェントが「完了しました」と報告したのに、実際には完了していなかった、こういう経験はありませんか。この章では、Phase-Gatingという仕組みで完了報告を機械的に検証する方法を解説します。40分間、AIエージェント開発における品質保証の最前線を学んでいきましょう。なぎなたと申します。
-->

---

## この章で学ぶこと [L3: Apply + Create]

1. **Supervisor Pattern / Phase-Gating** の概念を説明できる
2. **完了条件5項目** の設計思想を理解する
3. **PostToolUse hook** による自動検証の仕組みを設計できる
4. **宣言型検証** と **opt-in設計** の利点を説明できる
5. **実運用での調整ポイント** を理解する

<!--
この章では5つの到達点を目指します。Supervisor PatternとPhase-Gatingの概念を理解し、完了条件の設計思想を学びます。PostToolUse hookによる自動検証の仕組みを設計できるようになり、宣言型検証とopt-in設計の利点を説明できます。最後に実運用での調整ポイントを学びます。
-->

---

# 「完了しました」— 本当に完了していますか?

> AIエージェントが「タスク完了」と報告したのに、実際にはファイルが存在しなかったり、テストが通っていなかったりする。これは**毎日起きている**ことです。

- エージェントは「主観的には完了」を報告しがち
- 人間の目視チェックは属人的で抜けが生じる
- **機械的な検証** だけが確実な完了保証を与える

> **Supervisor Pattern**: 上司(スーパーバイザー)が部下の完了報告を**必ず再確認**するパターン — 信頼するが、検証する

<!--
つかみのスライドです。エージェントにタスクを任せて完了報告を受け取ったあと、実際に確認したら違っていた、こういう経験は多くの開発者が持っているはずです。Supervisor Patternは、上司が部下の完了報告を必ず再確認するパターンです。信頼はするが、必ず検証するという姿勢が、エージェント開発での品質保証の基本です。
-->

---

# Supervisor Pattern と Phase-Gating

**Supervisor Pattern**: エージェントの自律的な動作に対して、外部から検証・承認を挟む設計パターン

**Phase-Gating**: タスクの各Phaseの完了を、次のPhaseに進む前に**Gate**で強制検証する仕組み

| パターン | 役割 | 例 |
|---------|------|-----|
| **Supervisor** | 外部からの完了検証 | done_gate.sh が status:done を検査 |
| **Phase-Gating** | Phase間の通過条件 | verify_runner がテスト結果を確認 |

> これらはソフトウェア工学の**Code Review**や**CI/CD Pipeline**と同じ考え方 — 自動化された品質Gate

<!--
Supervisor PatternとPhase-Gatingは、エージェント開発における品質保証の2つの柱です。Supervisorは外部からの完了検証、Phase-Gatingは各Phaseの通過条件を強制する仕組みです。ソフトウェア工学のCode ReviewやCI/CD Pipelineと同じ考え方で、すでに馴染みのある概念をエージェント開発に適用したものです。
-->

---

# 完了条件5項目 — 何を検証すべきか

エージェントのタスク完了を宣言する前に、5つの条件を満たしているか:

| # | 検証項目 | 理由 |
|---|---------|------|
| 1 | **成果物ファイルが存在する** | 存在しないものは完了ではない |
| 2 | **成果物が正しい内容である** | 存在するだけでは不十分 |
| 3 | **品質レビューが実施された** | advisor等の第三者チェック |
| 4 | **報告が提出された** | 完了の記録と通知 |
| 5 | **事後手順が実行された** | commit/push等の必須ステップ |

> これらを毎回人間が確認するのは非現実的 → **自動化が必須**

<!--
完了を宣言する前に検証すべき5つの項目です。成果物の存在、内容の正確性、品質レビュー、報告提出、事後手順の5つです。これらを毎回人間が確認するのは現実的ではありません。だから自動化が必要です。
-->

---

# 宣言型検証 Gate — 設計思想

**宣言型検証** = エージェントが事前に完了条件をYAMLで宣言し、Gateがそれを機械的に照合する

```yaml
# task YAML の宣言例
post_steps:
  - path/to/output_file.csv    # このファイルが存在するか検証
  - reports/report.yaml        # 報告書が提出されたか検証
verify:
  command: "npm test"
  timeout_seconds: 60
```

**3つの設計原則**:

1. **宣言型**: YAMLに条件を書く — Gateは推測しない
2. **opt-in**: verify欄がない場合は素通り — 段階的導入が可能
3. **自動連鎖**: PostToolUse → verify_runner → Gate の連鎖が自動回転

<!--
宣言型検証の設計思想です。エージェントが事前に完了条件をYAMLで宣言しておき、Gateはそれを機械的に照合します。3つの設計原則があります。宣言型はYAMLに条件を書くことでGateの推測を排除します。opt-inはverify欄がない場合に素通りする設計で、段階的な導入が可能です。自動連鎖はPostToolUse hookが自動的にverify_runnerを起動し、結果をGateに渡す仕組みです。
-->

---

# PostToolUse hook による自動検証

PostToolUseイベントで **verify_runner** が発火する仕組み:

```json
// settings.json に登録
{
  "hooks": {
    "PostToolUse": [
      {"hooks": [{"type": "command",
        "command": "bash scripts/verify_runner.sh",
        "timeout": 130}]}
    ]
  }
}
```

> ※本講座サンプル実装 — 実際のプロジェクトではスクリプトパスやタイムアウト値を調整してください

**実行フロー**:
1. エージェントがtask YAMLを `Write`/`Edit` する
2. **PostToolUse hook** が発火
3. `verify_result: pending` を検出 → `verify.command` を実行
4. 結果で `verify_result` を `pass`/`fail` に上書き

<!--
PostToolUse hookによる自動検証の仕組みです。エージェントがtask YAMLを編集するとPostToolUse hookが発火し、verify_runnerが起動します。verify_resultがpendingの場合、宣言されたコマンドを自動実行し、結果でpassまたはfailに上書きします。これがPhase-Gatingの実装です。
-->

---

# Gate が BLOCK する3つのパターン

| # | BLOCK条件 | 対応 |
|---|----------|------|
| 1 | **post_steps 未完了** — marker ファイルが存在しない | 成果物を生成 |
| 2 | **verify_result ≠ pass** — 検証コマンドが未実行または失敗 | コマンドを実行してpassを確認 |
| 3 | **品質レビュー不足** — 実装前/完了前のレビューが未実施 | レビューを実施 |

- **BLOCK メッセージ** が具体的な対応方法を指示
- エージェントはメッセージを読んで**自力で修正**可能

<!--
GateがBLOCKする3つのパターンです。post_steps未完了、verify_result不合格、品質レビュー不足の3つです。BLOCKされた場合、具体的な対応方法がメッセージで指示されるため、エージェントは自力で問題を修正できます。これがSupervisor Patternの実用的な強みです。
-->

---

# 「未完了の完了報告」の再現例

エージェントが `status: done` を宣言したが、実際には:

```yaml
# task YAML (エージェントが書いた状態)
- task_id: subtask_build_widget
  status: done          # ← エージェントは「完了」と宣言
  verify:
    command: "npm test"
  verify_result: pending  # ← まだ実行されていない
  post_steps:
    - dist/widget.js      # ← まだ存在しない
```

**Gate の反応**:
```
BLOCK: subtask_build_widget
  - post_steps 未完了 (1件欠落): dist/widget.js
  - verify_result: pending (コマンド未実行)
対応: 成果物を生成し、npm test を実行してから status:done を宣言せよ
```

<!--
未完了の完了報告の再現例です。エージェントはstatus:doneを宣言しましたが、verify_resultはpendingのままで、post_stepsに指定されたファイルも存在していません。Gateはこれを検出してBLOCKし、具体的な対応方法を指示します。エージェントはこのメッセージを見て、まず成果物を生成し、テストを実行してから再度doneを宣言します。
-->

---

# 実運用での調整ポイント

**条件の追加**:
- 新しい検査項目はGateスクリプトにブロックを追加
- 例: lintチェック・セキュリティスキャン・依存関係の更新確認

**条件の除外**:
- `verify:` 欄を書かない → 自動的にSKIP (opt-in設計)
- 特定タスクだけ検査を緩和したい場合に有効

**閾値の変更**:
- 品質レビューの最低回数の調整
- verify のタイムアウト秒数の調整

**ログの活用**:
- verifyコマンドの実行結果ログ
- 品質レビュー呼出の全履歴ログ

<!--
実運用での調整ポイントです。条件の追加はGateスクリプトに新しい検査ブロックを追加するだけで済みます。条件の除外はverify欄を書かないだけで自動的にSKIPされます。閾値の変更やログの活用も柔軟に対応できます。opt-in設計のおかげで、プロジェクトの成熟度に合わせて段階的に導入できるのが大きな利点です。
-->

---

# この章のまとめ

- **Supervisor Pattern**: エージェントの完了報告を外部から機械的に検証する設計パターン
- **Phase-Gating**: 各Phaseの完了をGateで強制検証する仕組み
- **宣言型検証**: YAMLに完了条件を宣言 → Gateが機械的に照合
- **PostToolUse hook** が verify_runner を自動起動 → `pending` を `pass`/`fail` に更新
- **opt-in 設計** で段階的導入が可能
- **BLOCK メッセージ** が具体的な対応方法を指示 → エージェントは自力で修正可能

<!--
この章のまとめです。Supervisor Patternはエージェントの完了を外部から検証するパターンで、Phase-Gatingは各Phaseの通過を強制する仕組みです。宣言型検証、PostToolUse hookによる自動化、opt-in設計、具体的なBLOCKメッセージの4つが実装の柱です。
-->

---

# 確認問題

**Q1**: Supervisor Patternの「Supervisor」とは何を指すか？
- A: エージェント自身の自己評価機能
- B: エージェントの完了報告を外部から検証する仕組み
- C: エージェントを監視するカメラ

**Q2**: verify欄をtask YAMLに書かなかった場合、どうなるか？
- A: 常にBLOCKされる
- B: 検査をスキップして素通りする (opt-in)
- C: デフォルトのコマンドが自動実行される

**Q3**: PostToolUse hookがverify_result: pendingを検出したとき、何をするか？
- A: メールで通知を送る
- B: verify.commandを実行し、結果でverify_resultを上書きする
- C: タスクを自動的に削除する

<!--
確認問題です。Q1、Supervisorはエージェントの完了報告を外部から検証する仕組みを指します。Q2、verify欄を書かなかった場合、検査をスキップして素通りします。これがopt-in設計です。Q3、PostToolUse hookがpendingを検出すると、verify.commandを実行し、その結果でverify_resultをpassまたはfailに上書きします。
-->

---

<!-- _class: cover -->

# 第11章 完了!
## Supervisor Pattern / Phase-Gating の仕組みを理解したか?

**到達点チェック**:
- ✅ Supervisor Pattern / Phase-Gating の概念を説明できる
- ✅ 完了条件5項目の設計思想を理解している
- ✅ PostToolUse hookによる自動検証を設計できる
- ✅ 宣言型検証とopt-in設計の利点を説明できる
- ✅ 実運用での調整ポイントを理解している

**次章**: Guardrails設計 — Silent Fail検出パターン

<div class="meta">
講師: なぎなた
</div>

<!--
第11章完了です。Supervisor PatternとPhase-Gatingの仕組みを理解できたでしょうか。到達点を振り返りましょう。5つの到達点を理解できていれば完璧です。次章では、エラーが出ていないのに結果がおかしい「静かな失敗」を検出するGuardrails設計を解説します。
-->
