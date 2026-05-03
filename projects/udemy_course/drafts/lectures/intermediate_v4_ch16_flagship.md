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

# 三層アーキテクチャ実装パターン
## L1 + L2 + L3 が繋がるクライマックス

<div class="meta">
中級編 v4 — 第16章 (約 45 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第16章へようこそ。この章は本講座のクライマックスです。ここまでL1プロンプト層、L2コンテキスト層、L3ハーネス層を別々に学んできましたが、この章では3つの層が1つのhookスクリプトに統合される様子を45分かけて一行ずつ解剖します。講師のなぎなたと申します。最も重要な章ですので、集中して取り組みましょう。
-->

---

## この章で学ぶこと [L6: Create]

1. **3層統合の必要性** を、具体的な問題設定から説明できる
2. **L1層** のmem-searchクエリ生成ルールを読解できる
3. **L2層** の4系統自動記録の設計意図を説明できる
4. **L3層** のPreToolUse hookの発火仕組みを理解する
5. **fallback設計** 3点の役割を説明し、統合hook全体図を描ける

<!--
この章では5つの到達点を目指します。まず3層統合が必要な理由を具体的な問題から理解します。次にL1層のmem-searchクエリ生成、L2層の4系統自動記録、L3層のPreToolUse hook発火をそれぞれ読解します。そして、fallback設計3点と5ファイル構成の統合hook全体図を理解します。Bloomの分類で言えばL6 Create、これまでの学びを統合して新しい設計を理解するレベルです。
-->

---

# 「同じ失敗を繰り返している」 — 3層で解決する

> 「タスクを起票したのに、過去に同じ失敗をしたことを検索し忘れて、また同じ罠に落ちた」
> — この現象は、**L1・L2・L3がバラバラ** だから起きる。

- **L1だけ**: 「過去事例を検索して」と毎回指示する → 忘れる
- **L2だけ**: 過去事例は記録されている → 検索クエリを生成しない
- **L3だけ**: hookは発火する → 何を検索すべきか分からない

> **3層統合** だけが、この問題を解決する。

<!--
つかみです。AIにタスクを依頼したのに、過去に同じ失敗をしたことを検索し忘れて、また同じ罠に落ちた経験はありませんか。これはL1、L2、L3がバラバラに動いているから起きる現象です。L1だけで指示しても忘れるし、L2だけで記録しても検索しないし、L3だけでhookを設定しても検索クエリが分かりません。3層が統合されて初めて、この問題が解決します。この章では、その統合の仕組みをコードレベルで読解します。
-->

---

# 解決の全体像 — cmd_intake_hook.sh

**5ファイル構成の3層統合hook**:

| ファイル | 担当層 | 役割 |
|---------|--------|------|
| `cmd_intake_hook.sh` | **L3** | PreToolUse hook本体・全体制御 |
| `mem_search.sh` | **L1** | クエリ生成・名詞抽出・検索実行 |
| `auto_record.sh` | **L2** | 4系統add_observations自動記録 |
| `audit_log.sh` | **fallback** | 実行ログの監査証跡 |
| `session_ingest.sh` | **fallback** | SessionStart時の未処理キュー消化 |

- hook発火 → L1がクエリ生成 → L2が結果を記録 → fallbackが安全網
- **5ファイルが連携** して「過去事例検索忘れ」をゼロにする

<!--
解決の全体像です。cmd_intake_hook.shという1つのhookスクリプトが、5つのファイルで構成されています。L3のhook本体が全体を制御し、L1のmem_search.shがクエリを生成し、L2のauto_record.shが結果を記録します。さらにaudit_log.shが監査証跡を残し、session_ingest.shがセッション開始時に未処理のキューを消化します。この5ファイルが連携して、過去事例の検索忘れをゼロにする仕組みです。
-->

---

# L1層: mem-searchクエリ生成ルール

**mem_search.sh** — AIの「検索意図」をクエリに変換:

1. **入力**: タスク説明文のテキスト
2. **名詞抽出**: テキストからキーワードを抽出
3. **クエリ生成**: 抽出したキーワードでmem-search APIを呼ぶ

```
# クエリ生成の核心 (概念コード)
keywords=$(echo "$task_text" | extract_nouns)
results=$(mem-search search "$keywords")
```

- **ポイント**: プロンプト設計(L1)が「何を検索するか」を決める
- 抽出ルールは `awk` ベース — MeCab等の重い依存なし

<!--
L1層のmem_search.shの解説です。このファイルの役割は、タスク説明文からキーワードを抽出し、mem-search APIへの検索クエリを生成することです。処理は3ステップで、テキスト入力、名詞抽出、クエリ生成です。名詞抽出にはawkベースの軽量なルールを使い、MeCabのような重い依存はありません。ここがL1プロンプト層の役割で、「何を検索するか」を決めるのがプロンプト設計の本質です。
-->

---

# L2層: 4系統自動記録設計

**auto_record.sh** — 検索結果を永続コンテキストに自動保存:

| 系統 | 記録内容 | タイミング |
|------|---------|-----------|
| **系統1** | タスク起票内容 | hook発火時 |
| **系統2** | mem-search検索結果 | 検索完了時 |
| **系統3** | 過去事例との類似度判定 | 類似事例検出時 |
| **系統4** | 実行結果の要約 | タスク完了時 |

- **重要**: 記録は `add_observations` API経由 — L2コンテキスト層の自動注入
- 4系統すべてが **自動実行** — 手動操作なし

<!--
L2層のauto_record.shの解説です。このファイルは、4つの系統で情報を自動記録します。系統1はタスク起票内容、系統2はmem-searchの検索結果、系統3は過去事例との類似度判定、系統4は実行結果の要約です。すべてadd_observations API経由でL2コンテキスト層に自動注入されます。手動操作は一切不要で、hookが発火すれば自動的に記録が走ります。これがL2コンテキスト層の力です。
-->

---

# L3層: PreToolUse hookの発火仕組み

**cmd_intake_hook.sh** — hook登録と発火の仕組み:

```
# settings.json への登録
{
  "hooks": {
    "PreToolUse": [{
      "command": "bash cmd_intake_hook.sh",
      "matcher": "Write|Edit"
    }]
  }
}
```

- **発火タイミング**: Write または Edit ツールが呼ばれる直前
- **判定フロー**:
  1. ツール呼出を検知 → タスク説明文を取得
  2. mem_search.sh に渡して過去事例を検索
  3. auto_record.sh で結果を記録
  4. 類似事例があれば警告を表示

- **L3の本質**: 開発者が意識しなくても安全装置が働く

<!--
L3層のcmd_intake_hook.shの解説です。settings.jsonにPreToolUse hookとして登録します。WriteまたはEditツールが呼ばれる直前に発火します。発火すると、タスク説明文を取得し、mem_search.shに渡して過去事例を検索し、auto_record.shで結果を記録します。類似事例が見つかれば警告を表示します。L3ハーネス層の本質は、開発者が意識しなくても安全装置が働くことです。
-->

---

# 3層連携の流れ — 実行シーケンス

**hook発火から記録完了まで**:

1. **[L3]** Write/Edit 呼出検知 → hook発火
2. **[L1]** タスク説明文 → 名詞抽出 → クエリ生成
3. **[L1]** mem-search API実行 → 過去事例を取得
4. **[L2]** 4系統 add_observations で結果を自動記録
5. **[L3]** 類似事例あり → 警告表示 / なし → 通常続行
6. **[fallback]** audit_log.sh に実行証跡を記録

> 6ステップが **自動実行** — 開発者は何もしなくてよい

<!--
3層が連携する実行シーケンスの全体像です。L3のhookが発火し、L1がクエリを生成して検索を実行し、L2が結果を自動記録し、L3が類似事例の有無で警告表示を判断し、最後にfallbackが監査ログに証跡を残します。この6ステップがすべて自動で実行されます。開発者は何も意識する必要がありません。これが3層統合の威力です。
-->

---

# fallback設計 3点 — 安全網の仕組み

### 1. 監査ログ (audit_log.sh)
- すべてのhook実行をJSON形式で記録
- 後から「何が起きたか」を追跡可能

### 2. pending queue
- mem-search APIが応答できない場合、キューに積んで後で再実行
- ネットワーク障害時にデータを消失しない

### 3. SessionStart ingest (session_ingest.sh)
- 新しいセッション開始時に未処理のpending queueを消化
- セッションを跨いでも記録漏れなし

> **fallback = 「最悪のケース」に備える設計** — 正常系だけでなく異常系も考える

<!--
3つのfallback設計の解説です。1つ目の監査ログは、すべてのhook実行をJSON形式で記録し、後から追跡可能にします。2つ目のpending queueは、mem-search APIが応答できない場合にキューに積んで後で再実行します。ネットワーク障害が起きてもデータを消失しません。3つ目のSessionStart ingestは、新しいセッション開始時に未処理のキューを消化します。セッションをまたいでも記録漏れがありません。fallbackは最悪のケースに備える設計で、正常系だけでなく異常系も考えるのが本格的なハーネス設計の証です。
-->

---

# 5ファイル構成 — 統合hook全体図

| コンポーネント | 層 | 入力 | 出力 |
|--------------|---|------|------|
| **cmd_intake_hook.sh** | L3 | ツール呼出イベント | 制御フロー・警告 |
| **mem_search.sh** | L1 | タスク説明文 | 検索クエリ・結果 |
| **auto_record.sh** | L2 | 検索結果・実行結果 | add_observations |
| **audit_log.sh** | fallback | 実行ログ | JSON証跡 |
| **session_ingest.sh** | fallback | pending queue | 未処理キュー消化 |

> **設計原則**: 各ファイルは **単一責任** — 1ファイル1層・層を跨ぐ依存は最小限

<!--
5ファイル構成の全体図です。cmd_intake_hook.shがL3の制御フローを担当し、mem_search.shがL1のクエリ生成、auto_record.shがL2の記録、audit_log.shが監査証跡、session_ingest.shがpending queueの消化を担当します。設計原則は単一責任です。1つのファイルが1つの層を担当し、層を跨ぐ依存は最小限に抑えています。これにより、1つの層に変更があっても他の層への影響を最小限にできます。
-->

---

# 設計原則 3点 — 再利用可能なhook設計

1. **単一責任の原則**: 1ファイル = 1層の役割に分割
   - 変更容易性: L1のクエリルールだけ変更可能

2. **冪等性**: 何度実行しても同じ結果
   - 2回hookが発火しても重複記録しない

3. ** graceful degradation**: 部分障害で全体が止まらない
   - mem-search APIが落ちてもfallbackが記録を保証

> この3原則は **どのようなhook設計にも適用** できる普遍パターン

<!--
3つの設計原則です。1つ目の単一責任の原則は、1つのファイルが1つの層の役割を担当することです。これにより、L1のクエリルールだけを変更したい場合に他のファイルを触る必要がありません。2つ目の冪等性は、何度実行しても同じ結果になることです。hookが2回発火しても重複記録されません。3つ目のgraceful degradationは、部分障害で全体が止まらないことです。mem-search APIが落ちても、fallbackが記録を保証します。この3原則は、どのようなhook設計にも適用できる普遍的なパターンです。
-->

---

# この章のまとめ

- **3層統合** は「過去事例検索忘れ」をゼロにする — 単独層では解決不能
- **L1** (mem_search.sh): クエリ生成・名詞抽出が「検索意図」を形にする
- **L2** (auto_record.sh): 4系統自動記録が「永続コンテキスト」を更新する
- **L3** (cmd_intake_hook.sh): PreToolUse hookが「安全装置」として発火する
- **fallback 3点**: 監査ログ + pending queue + SessionStart ingest で異常系をカバー
- **設計原則**: 単一責任・冪等性・graceful degradation

<!--
この章のまとめです。3層統合によって過去事例の検索忘れをゼロにできます。単独の層では解決できない問題も、3層を組み合わせれば解決できます。L1が検索意図を形にし、L2が永続コンテキストを更新し、L3が安全装置として発火します。fallbackの3点で異常系もカバーします。そして設計原則の単一責任、冪等性、graceful degradationは、どんなhook設計にも使える普遍パターンです。
-->

---

# 確認問題

**Q1**: 3層統合hookでL1層を担当するファイルはどれか？
- A: cmd_intake_hook.sh
- B: mem_search.sh
- C: auto_record.sh

**Q2**: fallback設計のpending queueの役割は何か？
- A: 検索結果をキャッシュする
- B: APIが応答できない場合に後で再実行する
- C: セッションをまたいで会話を継続する

**Q3**: 3層統合hookの設計原則として正しいものはどれか？
- A: 1ファイルにすべての層を実装する
- B: 各ファイルは単一責任で1層を担当する
- C: fallbackは省略してもよい

<!--
確認問題です。Q1、3層統合hookでL1層を担当するファイルはmem_search.shです。クエリ生成と名詞抽出を行います。Q2、pending queueの役割は、APIが応答できない場合にキューに積んで後で再実行することです。ネットワーク障害時のデータ消失を防ぎます。Q3、設計原則として正しいのは、各ファイルは単一責任で1つの層を担当することです。1ファイルにすべてを実装するのは推奨されません。fallbackは省略すべきではありません。
-->

---

<!-- _class: cover -->

# 第16章 完了!
## 3層が繋がった — これが本講座のクライマックス

**到達点チェック**:
- ✅ 3層統合が必要な理由を説明できる
- ✅ L1 mem-searchクエリ生成を読解できる
- ✅ L2 4系統自動記録の設計を理解している
- ✅ L3 PreToolUse hookの仕組みを説明できる
- ✅ fallback設計3点と全体図を描ける
- ✅ 設計原則3点を他のhook設計に適用できる

**次章**: 総合解説 Part 1 — 3階層統合の設計思想

<div class="meta">
講師: なぎなた
</div>

<!--
第16章完了です。3層が繋がる体験はできましたか。到達点を振り返りましょう。3層統合の必要性、L1のクエリ生成、L2の自動記録、L3のhook発火、fallback設計、設計原則の6つを理解できていれば完璧です。この章は本講座のクライマックスであり、ここまでの学びがすべて統合されました。次章では、この3階層統合の設計思想をさらに深く掘り下げます。引き続き学んでいきましょう。
-->
