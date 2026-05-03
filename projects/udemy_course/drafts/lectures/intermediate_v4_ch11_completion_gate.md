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

# 完了 Gate ハーネス
## AIの「完了報告」を機械的に検証する

<div class="meta">
中級編 v4 — 第11章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第11章へようこそ。この章のテーマは「完了 Gate ハーネス」です。AIが「完了しました」と報告したのに、実際には完了していなかった、こういう経験はありませんか。この章では、AIの完了報告を機械的に検証する門番の仕組みを解説します。40分間、AI開発における品質保証の最前線を学んでいきましょう。なぎなたと申します。
-->

---

## この章で学ぶこと [L3: Create]

1. **完了条件5項目** の設計思想を説明できる
2. **done_gate.sh** の構造と検査フローを理解する
3. **PostToolUse hook** としての登録方法を説明できる
4. **verify_runner** による自動検証の仕組みを理解する
5. **実運用での調整ポイント** を説明できる

<!--
この章では5つの到達点を目指します。まず完了条件を何で構成すべきかの設計思想を理解します。次にdone_gate.shというスクリプトがどのように完了を検査するかを学びます。そしてPostToolUse hookとしてこれを登録する方法を解説し、verify_runnerという自動検証の仕組みを理解します。最後に実際の運用でどう調整するかのポイントを学びます。Bloomの分類で言えばCreateレベル、これまでの知識を組み合わせて新しい仕組みを理解する段階です。
-->

---

# 「完了しました」— 本当に完了していますか?

> AIが「タスク完了」と報告したのに、実際にはファイルが存在しなかったり、テストが通っていなかったりする。これは**毎日起きている**ことです。

- AIは「主観的には完了」を報告しがち
- 人間の目視チェックは属人的で抜けが生じる
- **機械的な検証** だけが確実な完了保証を与える

<!--
つかみのスライドです。AIにタスクを任せて「完了しました」という報告を受け取ったあと、実際にファイルを開いたら中身が違っていた、あるいはテストが通っていなかった、こういう経験は多くの開発者が持っているはずです。AIは主観的には完了と判断して報告しますが、客観的な検証基準を満たしているとは限りません。人間が毎回目視で確認するのは属人的で抜けが生じます。解決策は機械的な検証です。この章ではその仕組みを解説します。
-->

---

# 完了条件5項目 — 何を検証すべきか

AIのタスク完了を宣言する前に、5つの条件を満たしているか:

| # | 検証項目 | 理由 |
|---|---------|------|
| 1 | **成果物ファイルが存在する** | 存在しないものは完了ではない |
| 2 | **成果物が正しい内容である** | 存在するだけでは不十分 |
| 3 | **品質レビューが実施された** | advisor等の第三者チェック |
| 4 | **報告が提出された** | 完了の記録と通知 |
| 5 | **事後手順が実行された** | commit/push等の必須ステップ |

> これらを毎回人間が確認するのは非現実的 → **自動化が必須**

<!--
完了を宣言する前に検証すべき5つの項目です。1番目は成果物ファイルが実際に存在すること。2番目はファイルの中身が正しいこと。3番目は品質レビュー、たとえばadvisorによるチェックが実施されていること。4番目は完了報告が提出されていること。5番目は事後手順、git commitやpushなどが実行されていることです。これらを毎回人間が確認するのは現実的ではありません。だから自動化が必要なのです。
-->

---

# done_gate.sh — 完了検証の門番

**done_gate.sh** = タスクが `status: done` を宣言する前に、検査を実行するスクリプト

- **呼出方法**:
  ```
  bash scripts/done_gate.sh <agent_id> <task_id> <task_yaml_path>
  ```

- **結果**:
  - exit 0 = **OK** (done を許可)
  - exit 2 = **BLOCK** (done 不可・理由は stderr)

- **設計原則**: opt-in — taskに `verify:` 欄がない場合は素通り (後方互換)

<!--
done_gate.shは完了検証の門番です。タスクYAMLでstatus:doneを宣言する前にこのスクリプトを呼び出し、検査を受けます。使い方はシンプルで、エージェントID、タスクID、YAMLパスを渡すだけです。結果はexitコードで返り、0ならdone許可、2ならBLOCKされます。重要な設計原則としてopt-in方式を採用しています。task YAMLにverify欄がない場合は検査をスキップし、素通りさせます。これにより既存タスクとの後方互換性を保っています。
-->

---

# done_gate.sh の検査フロー

```
done_gate.sh 呼出
      │
      ▼
  post_steps 未完了?
    YES → BLOCK (marker ファイル未検出)
      │
      NO (全 marker 存在)
      ▼
  verify: 欄あり?
    NO → SKIP (後方互換・素通り)
      │
      YES
      ▼
  verify_result = pass?
    NO → BLOCK (検証未完了)
      │
      YES
      ▼
  advisor 呼出 ≥ 2回?
    NO → BLOCK (実装前 + 完了前の必須呼出)
      │
      YES
      ▼
  exit 0 (done 許可)
```

<!--
done_gate.shの検査フローを図で表しました。まずpost_stepsの未完了チェックです。事後手順として指定されたmarkerファイルが存在するかを確認し、未完了ならBLOCKします。次にverify欄の有無を確認します。なければSKIPして素通りです。verify欄がある場合はverify_resultがpassであることを確認し、未達ならBLOCKします。最後にadvisorの呼出回数を確認し、最低2回、つまり実装前と完了前に呼び出されていることを検証します。すべて通過すればexit 0でdoneを許可します。
-->

---

# post_steps — 事後手順の marker チェック

**post_steps** = タスク完了後に必ず実行すべき手順をYAMLで宣言

```yaml
# task YAML の記述例
post_steps:
  - path/to/output_file.csv    # このファイルが存在するか検証
  - reports/report.yaml        # 報告書が提出されたか検証
```

- **仕組み**: 各パスがファイルとして存在するかを `os.path.isfile()` で確認
- **1件でも欠落** → BLOCK + 欠落一覧を stderr に出力
- **対応**: 指定ファイルを生成してから再度 status: done を宣言

<!--
post_stepsはタスク完了後の必須手順を宣言する仕組みです。YAMLにパスを列挙すると、done_gate.shがそのファイルの存在を確認します。たとえば成果物CSVや報告書YAMLをpost_stepsに列挙しておけば、それらが存在しない限りdoneを宣言できません。1件でも欠落していればBLOCKされ、欠落一覧がstderrに出力されます。これにより「完了報告したのにファイルが存在しない」という事故を防ぎます。
-->

---

# verify_result — 自動検証コマンドの仕組み

**verify** = タスクYAMLに検証コマンドを宣言し、自動実行させる仕組み

```yaml
# task YAML の記述例
verify:
  command: "cd project && npm test"
  timeout_seconds: 60
verify_result: run_now   # PostToolUse hook が自動実行
```

**実行フロー**:
1. YAMLが `Write`/`Edit` される
2. **PostToolUse hook** (`posttool_verify_runner.sh`) が発火
3. `verify_result: run_now` を検出 → `verify.command` を実行
4. 結果で `verify_result` を `pass`/`fail` に上書き
5. 実行ログは `logs/verify_{task_id}_{timestamp}.log` に保存

<!--
verify_resultは自動検証コマンドの仕組みです。タスクYAMLにverify欄でコマンドを宣言し、verify_resultをrun_nowに設定すると、PostToolUse hookが自動的にそのコマンドを実行します。コマンドのexitコードが0ならpass、それ以外ならfailです。実行ログは自動的に保存されるので、後から確認することもできます。これによりテスト実行やビルド確認を人間が手動で行う必要がなくなります。
-->

---

# verify_runner — PostToolUse hook の実装

`posttool_verify_runner.sh` は PostToolUse hook として登録:

```json
// settings.json
{
  "hooks": {
    "PostToolUse": [
      {"hooks": [{"type": "command",
        "command": "bash scripts/posttool_verify_runner.sh",
        "timeout": 130}]}
    ]
  }
}
```

**安全機能**:
- 危険コマンドを **自動reject** (`rm -rf`/`sudo`/`git push --force` 等)
- タイムアウト設定 (デフォルト60秒・最大120秒)
- **BLOCK不可** (PostToolUseはexit 0固定・異常時はWARNINGのみ)

<!--
verify_runnerをPostToolUse hookとして登録する方法です。settings.jsonのhooksセクションにPostToolUseを定義し、スクリプトのパスを指定します。timeoutは130秒に設定しています。安全機能として、危険コマンドを自動的にrejectします。rm -rfやsudo、git push --forceなどは実行されず、failとして記録されます。またPostToolUse hookはBLOCKできない仕様なので、異常時はWARNINGを出すにとどまります。
-->

---

# 「未完了の完了報告」の再現例

AIが `status: done` を宣言したが、実際には:

```yaml
# task YAML (AIが書いた状態)
- task_id: subtask_build_widget
  status: done          # ← AIは「完了」と宣言
  verify:
    command: "npm test"
  verify_result: run_now  # ← まだ実行されていない
  post_steps:
    - dist/widget.js      # ← まだ存在しない
```

**done_gate.sh の反応**:
```
BLOCK: subtask_build_widget post_steps 未完了 (1 件欠落)
  欠落 marker:
    - dist/widget.js
対応: post-step を完了させてから status:done / QC 依頼せよ
```

<!--
未完了の完了報告の再現例です。AIがstatus:doneを宣言しましたが、verify_resultはまだrun_nowのままで、post_stepsに指定されたdist/widget.jsも存在していません。done_gate.shはこれを検出してBLOCKします。エラーメッセージには欠落しているファイルと対応方法が明確に示されます。AIはこのメッセージを見て、まずテストを実行し、成果物を生成してから再度doneを宣言することになります。
-->

---

# done_gate が BLOCK する3つのパターン

| # | BLOCK条件 | エラーメッセージ | 対応 |
|---|----------|----------------|------|
| 1 | **post_steps 未完了** | marker ファイルが存在しない | 成果物を生成 |
| 2 | **verify_result ≠ pass** | 検証コマンドが未実行または失敗 | コマンドを実行してpassを確認 |
| 3 | **advisor 呼出 < 2回** | 実装前/完了前の呼出が不足 | advisor を呼び出す |

- **共通の設計思想**: 検査は **宣言型** (YAMLに書かれた条件を確認) であって、推測型ではない
- AIは「自分が何を完了すべきか」をYAMLで事前に宣言し、** gate はそれを機械的に照合**する

<!--
done_gateがBLOCKする3つのパターンをまとめました。1番目はpost_steps未完了で、指定されたファイルが存在しない場合です。2番目はverify_resultがpassでない場合で、検証コマンドがまだ実行されていないか失敗した場合です。3番目はadvisorの呼出が2回未満の場合で、実装前と完了前の必須呼出が欠けている場合です。共通する設計思想は宣言型であることです。AIがYAMLで事前に完了条件を宣言し、gateはそれを機械的に照合します。AIの主観的な判断に依存しないのがこの仕組みの強みです。
-->

---

# advisor 呼出回数の検証

**なぜ2回必要なのか**:

| タイミング | 目的 | 記録先 |
|-----------|------|--------|
| **実装前** (step 3.8) | 方針の妥当性を確認 | `logs/advisor_calls.log` |
| **完了前** (step 4.8) | 成果物の品質を確認 | 同上 |

**検証方法**:
- `logs/advisor_calls.log` から当該 task_id の行を `grep`
- 短縮形 (例: `1442_h1`) と完全形の両方で照合
- **2回未満** → BLOCK + 「実装前 + 完了前の必須呼出」を促す

<!--
advisorの呼出回数を検証する仕組みです。なぜ2回必要かというと、実装前に方針の妥当性を確認し、完了前に成果物の品質を確認するためです。検証方法はadvisor呼出のログをgrepして、当該タスクの呼出回数を数えます。タスクIDは短縮形と完全形の両方で照合する工夫がされています。2回未満であればBLOCKされ、適切なタイミングでadvisorを呼び出すよう促されます。これにより「品質レビューを飛ばした完了報告」を防止します。
-->

---

# 実運用での調整ポイント

**条件の追加**:
- 新しい検査項目は done_gate.sh にブロックを追加
- 例: lint チェック・セキュリティスキャン・依存関係の更新確認

**条件の除外**:
- `verify:` 欄を書かない → 自動的にSKIP (opt-in設計)
- 特定タスクだけ検査を緩和したい場合に有効

**閾値の変更**:
- advisor最低呼出回数の調整 (現状: 2回)
- verify のタイムアウト秒数の調整 (デフォルト: 60秒・最大: 120秒)

**ログの活用**:
- `logs/verify_*.log` — 各verifyコマンドの実行結果
- `logs/advisor_calls.log` — advisor呼出の全履歴

<!--
実運用での調整ポイントを解説します。条件の追加はdone_gate.shに新しい検査ブロックを追加するだけで済みます。例えばlintチェックやセキュリティスキャンを追加したい場合、スクリプトに追記するだけです。条件の除外はverify欄を書かないだけで自動的にSKIPされます。opt-in設計のおかげで柔軟に対応できます。閾値の変更も可能で、advisorの最低呼出回数やverifyのタイムアウト秒数を調整できます。ログも活用でき、verifyコマンドの実行結果やadvisor呼出の全履歴が残ります。
-->

---

# done_gate の設計思想 — まとめ

**3つの柱**:

1. **宣言型検証**: YAMLに完了条件を宣言 → gate が機械的に照合
2. **opt-in**: verify 欄がない場合は素通り → 段階的導入が可能
3. **自動连锁**: PostToolUse hook → verify_runner → done_gate の連鎖

> **本質**: AIの「主観的な完了」を「客観的な完了」に変換する仕組み

<!--
done_gateの設計思想を3つの柱でまとめます。1番目は宣言型検証です。YAMLに完了条件を宣言しておき、gateがそれを機械的に照合します。2番目はopt-in方式です。verify欄がない場合は素通りするので、段階的に導入できます。3番目は自動連鎖です。PostToolUse hookがverify_runnerを起動し、verify_runnerが検証結果を書き込み、done_gateがその結果を確認するという連鎖が自動的に回ります。本質は、AIの主観的な完了を客観的な完了に変換する仕組みであることです。
-->

---

# この章のまとめ

- **完了条件5項目** (存在・内容・品質・報告・事後手順) を機械的に検証する
- **done_gate.sh** は post_steps / verify_result / advisor呼出の3層を検査
- **PostToolUse hook** が verify_runner を自動起動 → `run_now` を `pass`/`fail` に更新
- **opt-in 設計** で段階的導入が可能 (verify 欄がない場合は素通り)
- **BLOCK メッセージ** が具体的な対応方法を指示 → AIは自力で修正可能

<!--
この章のまとめです。完了条件5項目を機械的に検証する仕組みを学びました。done_gate.shはpost_steps、verify_result、advisor呼出回数の3層を検査します。PostToolUse hookがverify_runnerを自動起動し、verify_resultを自動更新します。opt-in設計により段階的な導入が可能で、BLOCKメッセージが具体的な対応方法を指示するため、AIは自力で問題を修正できます。次章では、エラーが出ていないのに結果がおかしい「静かな失敗」を検出する仕組みを解説します。
-->

---

# 確認問題

**Q1**: done_gate.sh が exit 2 を返すとき、何を意味するか?
- A: タスクが正常に完了した
- B: 完了条件を満たさず、done を BLOCK した
- C: スクリプトがクラッシュした

**Q2**: verify 欄を task YAML に書かなかった場合、どうなるか?
- A: 常に BLOCK される
- B: 検査をスキップして素通りする (opt-in)
- C: デフォルトのコマンドが自動実行される

**Q3**: PostToolUse hook (verify_runner) が verify_result: run_now を検出したとき、何をするか?
- A: メールで通知を送る
- B: verify.command を実行し、結果で verify_result を上書きする
- C: タスクを自動的に削除する

<!--
確認問題です。Q1、done_gate.shがexit 2を返すとき、それは完了条件を満たさずdoneをBLOCKしたことを意味します。Q2、verify欄を書かなかった場合、検査をスキップして素通りします。これがopt-in設計です。Q3、PostToolUse hookがverify_result: run_nowを検出したとき、verify.commandを実行し、その結果でverify_resultをpassまたはfailに上書きします。自動検証の連鎖がここで完結します。
-->

---

<!-- _class: cover -->

# 第11章 完了!
## AIの「完了報告」を機械的に検証する仕組みを理解したか?

**到達点チェック**:
- ✅ 完了条件5項目の設計思想を説明できる
- ✅ done_gate.sh の検査フローを理解している
- ✅ PostToolUse hook の登録方法を説明できる
- ✅ verify_runner の自動検証仕組みを理解している
- ✅ 実運用での調整ポイントを説明できる

**次章**: silent fail 検出ハーネス — エラーなし ≠ 成功 を見抜く

<div class="meta">
講師: なぎなた
</div>

<!--
第11章完了です。AIの完了報告を機械的に検証する仕組みを理解できたでしょうか。到達点を振り返りましょう。完了条件の設計思想、done_gate.shの検査フロー、PostToolUse hookの登録方法、verify_runnerの仕組み、実運用での調整ポイントの5つを理解できていれば完璧です。次章では、もっと厄介な問題「エラーが出ていないのに結果がおかしい」という静かな失敗を検出する仕組みを解説します。引き続き学んでいきましょう。
-->
