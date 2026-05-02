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

# MCP (Model Context Protocol)
## AIの記憶を拡張する仕組み

<div class="meta">
初級編 — 第6章 (約 30 min)<br><br>
講師: 村上誠治 (なぎなた)
</div>

<!--
スピーカーノート:
こんにちは。この動画は初級編第6章「MCP — Model Context Protocol」です。これまでの章で、プロンプトの書き方、CLAUDE.md、hook、そして簡単な自動化を学んできました。この章では、AIに「記憶」と「外部ツール」を接続する仕組み、MCPについて解説します。30分で、MCPの基本概念と接続手順をしっかり理解しましょう。
-->

---

## 🎯 この章で学ぶこと

1. **MCP（Model Context Protocol）とは何か** を説明できる
2. **MCPが解決する問題** を理解する
3. **memory MCP** でセッションを跨ぐ記憶を実現できる
4. **MCPなし/あり** の違いをBefore/Afterで説明できる
5. **代表的なMCPサーバー** を知り、自分に合うものを選べる

<!--
この章のゴールは5つ。一番大切なのは「MCPが何を解決するのか」を理解することです。AIは便利ですが、セッションを終えると記憶がリセットされます。MCPはその問題を解決します。最後まで見ていただければ、「なぜMCPが必要なのか」「どう使うのか」が明確に理解できます。
-->

---

# MCPとは — AIに「プラグイン」を追加する仕組み

> 🪞 AIとの会話が終わるたびに、記憶がリセットされていたら？

**MCP = Model Context Protocol**:
- Anthropic社が策定した **オープン規格**
- AIモデルと **外部ツール・データソース** を接続する仕組み
- ブラウザの拡張機能のように、AIに **新しい能力** を追加できる

> 💡 MCP = 「AI版プラグインシステム」と考えると分かりやすい

<!--
MCPは、Anthropic社 — つまりClaudeの開発元 — が作ったオープンな規格です。ブラウザに拡張機能を追加すると新しいことができるようになりますよね。MCPも同じで、AIに新しいツールやデータソースを接続できるようにします。たとえば「データベースにアクセスする」「ファイルシステムを操作する」「記憶を保持する」など。この「プラグインのような仕組み」がMCPです。
-->

---

# なぜMCPが必要なのか

**AIの限界（MCPなし）**:
- セッションを終えると **記憶がリセット** される
- 外部データベースに **直接アクセスできない**
- ファイルシステムの **自由な読み書きが制限** される

**MCPで解決できること**:
- セッションを跨いで **記憶を保持**（memory MCP）
- 外部APIやデータベースに **接続**（各種MCPサーバー）
- AIの能力を **用途に合わせて拡張**

<!--
「セッションを終えると記憶がリセットされる」— これが一番の問題です。毎回同じ説明を繰り返すのは非効率。MCPのmemoryサーバーを使えば、前回の会話内容を引き継げるようになります。また、データベースや外部APIにアクセスするMCPサーバーもあり、用途に合わせてAIの能力を拡張できます。
-->

---

# MCPの仕組み — クライアント・サーバーモデル

```
Claude Code (クライアント)
  +-- MCP Server A (memory)    <->  ファイル/DB
  +-- MCP Server B (github)    <->  GitHub API
  +-- MCP Server C (postgres)  <->  PostgreSQL
```

**3つの構成要素**:
1. **ホスト** — Claude CodeなどのAIアプリケーション
2. **クライアント** — ホスト内でMCPサーバーと通信
3. **サーバー** — 外部ツールへのアクセスを提供

<!--
MCPはシンプルなクライアント・サーバーモデルです。Claude Codeがクライアントになり、MCPサーバーと通信します。サーバー側はデータベースやファイルシステム、外部APIなど、さまざまなデータソースにアクセスします。この仕組により、AIが外部世界とやり取りできるようになります。
-->

---

# 代表的なMCPサーバー

| サーバー | 役割 | 用途例 |
|---------|------|--------|
| **memory** | 記憶の永続化 | セッション間で情報を引き継ぐ |
| **filesystem** | ファイル操作 | 指定ディレクトリの読み書き |
| **github** | GitHub連携 | Issue/PRの作成・確認 |
| **postgres** | DB操作 | SQLクエリの実行 |
| **brave-search** | Web検索 | 最新情報の取得 |

> これらはすべて **コミュニティまたは公式** が提供するOSS

<!--
代表的なMCPサーバーを5つ紹介します。memoryは記憶の永続化、filesystemはファイル操作、githubはGitHub連携、postgresはデータベース、brave-searchはWeb検索。これらはすべてオープンソースで無料で使えます。この中で最も基本的なのがmemoryサーバーです。次のスライドで詳しく解説します。
-->

---

# memory MCP — セッションを跨ぐ記憶

**MCPなしの場合**:
- セッション終了 → 記憶リセット
- 次回また **同じ説明** を最初から
- 過去の **文脈が一切引き継がれない**

**memory MCPありの場合**:
- セッション終了後も **記憶が保持される**
- 次回起動時に **前回の文脈を自動参照**
- AIが **自分で覚えるべきことを判断** して保存

> ⚡ 「毎回説明し直す」手間がなくなる = 生産性の大幅向上

<!--
memory MCPの核心は「セッションを跨いで記憶を保持する」ことです。MCPなしでは、Claude Codeを終了するとそれまでの会話内容がすべて消えます。次回起動時にまた同じことを説明する必要がある。memory MCPを使えば、AIが自分で「これは覚えておくべきだ」と判断して記憶を保存します。次回起動時には、その記憶を自動的に読み込んで文脈を引き継ぎます。
-->

---

# memory MCP の動作イメージ

**1回目のセッション**:
```
あなた: "私はReact開発者で、TypeScriptを使っています"
AI:     → memory MCP に「React + TS開発者」と保存
```

**2回目のセッション（別の日）**:
```
AI:     → memory MCP から記憶を読み込み
        「React + TS開発者」という情報を事前に把握
あなた: "コンポーネントを作って"
AI:     → 最初からTS前提で回答
```

> 💡 毎回「私はTypeScriptを使っています」と言う必要がなくなる

<!--
具体例で説明します。1回目のセッションで「React開発者でTypeScriptを使っている」と伝えます。AIはmemory MCPにこの情報を保存します。翌日、新しいセッションを開始すると、AIは自動的に記憶を読み込みます。「React + TS開発者」という情報を事前に把握しているので、「コンポーネントを作って」と頼むと、最初からTypeScript前提で回答してくれます。毎回前提条件を説明し直す手間がなくなります。
-->

---

# MCPの設定手順

**Step 1: MCPサーバーを追加**:
```
claude mcp add memory -s user \
  -- npx -y @modelcontextprotocol/server-memory
```

**Step 2: 設定ファイルを確認**:
```
cat ~/.claude/settings.json
```
↓ MCPエントリが追加されていればOK

**Step 3: セッションを開始**:
- Claude Codeを再起動 → MCPサーバーが自動接続
- `/mcp` コマンドで接続状態を確認

<!--
設定は3ステップです。まずコマンド1行でMCPサーバーを追加します。このコマンドは設定ファイルに必要な情報を自動的に書き込みます。次に設定ファイルを確認し、正しくエントリが追加されているか確認します。最後にClaude Codeを再起動すると、MCPサーバーが自動的に接続されます。/mcpコマンドで接続状態を確認できます。
-->

---

# 設定ファイルの中身

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

**各フィールドの意味**:
- `mcpServers` — MCPサーバーの定義をまとめるセクション
- `memory` — サーバーの名前（任意の名前を付けられる）
- `command` — サーバーを起動するコマンド
- `args` — コマンドに渡す引数

<!--
設定ファイルの中身はシンプルです。mcpServersセクションの中に、サーバー名、起動コマンド、引数を指定します。memoryサーバーの場合、npxコマンドでパッケージを実行するだけです。この設定があれば、Claude Code起動時に自動的にMCPサーバーが立ち上がります。
-->

---

# Before / After 比較

| 項目 | MCPなし | memory MCPあり |
|------|---------|---------------|
| セッション間の記憶 | リセットされる | 保持される |
| 前提条件の説明 | 毎回必要 | 初回のみ |
| プロジェクトの文脈 | 毎回説明 | 自動参照 |
| 好みや制約の記憶 | されない | 永続化される |

> 📊 MCPありの場合、**セッション開始時の準備時間がゼロに**

<!--
Before/Afterの比較です。MCPなしだと、セッションごとに記憶がリセットされ、前提条件を毎回説明する必要があります。memory MCPありだと、一度伝えた情報が保持され、次回以降は自動的に参照されます。セッション開始時の準備時間が実質ゼロになる。これがMCPの最大の実用価値です。
-->

---

# MCPサーバーの選び方

**選ぶ基準**:
1. **公式提供**かコミュニティ提供か — 信頼性の目安
2. **スター数・活発度** — GitHubで確認
3. **セキュリティ** — 機密データにアクセスする場合は慎重に

**代表的なカテゴリ**:

| カテゴリ | 例 | 向いている人 |
|---------|-----|------------|
| 記憶・永続化 | memory, knowledge-graph | 全開発者 |
| 開発ツール連携 | github, gitlab | チーム開発 |
| データベース | postgres, sqlite | バックエンド |
| Web・検索 | brave-search, fetch | 情報収集 |
| ファイル操作 | filesystem | 全開発者 |

<!--
MCPサーバーを選ぶ際は3つの基準を意識してください。まず公式提供かどうか — Anthropicや公式リポジトリが提供しているものは信頼性が高い。次にGitHubのスター数や開発の活発さ — 多くの人が使っているものは安心。最後にセキュリティ — データベースやファイルシステムにアクセスするサーバーは、権限設定に注意。カテゴリ別に見ると、記憶・永続化系はすべての開発者におすすめです。
-->

---

# MCP利用時の注意点

**セキュリティ**:
- MCPサーバーは **AIに権限を与える** という意味
- 信頼できないサーバーは追加しない
- 本番環境のDB接続は特に慎重に

**パフォーマンス**:
- MCPサーバーが多すぎると **起動が遅くなる**
- 必要なものだけ追加する

**トラブルシューティング**:
- `/mcp` でサーバーの状態確認
- エラー時は設定ファイルの `command` / `args` を確認

<!--
MCPを使う上で3つの注意点があります。セキュリティが一番重要。MCPサーバーを追加することは、AIに権限を与えることと同じです。信頼できないサーバーは絶対に追加しないでください。次にパフォーマンス。サーバーをたくさん追加すると起動が遅くなるので、必要なものだけに絞りましょう。トラブル時は/mcpコマンドでサーバーの状態を確認できます。
-->

---

# 📚 この章のまとめ

**理解できたこと**:
1. **MCP = AI版プラグインシステム** — 外部ツールを接続する規格
2. **memory MCP** — セッションを跨ぐ記憶を実現
3. **設定はコマンド1行** — `claude mcp add` で追加
4. **Before/After** — MCPなし/ありで生産性が大きく変わる
5. **選び方・注意点** — 信頼性・セキュリティ・必要最小限

> 🎯 MCPは「AIの能力を拡張する」ための標準的な仕組み

<!--
この章で学んだことを5つにまとめます。MCPはAI版のプラグインシステムです。memory MCPでセッション間の記憶が実現でき、設定はコマンド1行。MCPあり/なしで生産性が大きく変わります。そして信頼できるサーバーを必要最小限だけ追加するのがポイント。この5つが理解できていれば、第6章は完璧です。
-->

---

# 🔑 確認問題

**Q1**: MCPとは何の略で、何を解決する仕組みか？

**Q2**: memory MCPを使う最大のメリットは何か？

**Q3**: MCPサーバーを追加するコマンドを答えよ。

> 回答は次のスライドで

<!--
3つの確認問題です。MCPの正式名称と役割、memory MCPの最大メリット、そして追加コマンド。この3つに答えられれば、この章の内容はしっかり身についています。少し考えてから次のスライドを見てください。
-->

---

# 🔑 確認問題 — 回答

**A1**: **M**odel **C**ontext **P**rotocol。AIモデルに外部ツールやデータソースを接続するオープン規格。

**A2**: セッションを跨いで **記憶が保持される** こと。毎回同じ説明を繰り返す必要がなくなる。

**A3**:
```
claude mcp add memory -s user \
  -- npx -y @modelcontextprotocol/server-memory
```

<!--
回答です。A1: Model Context Protocolで、AIに外部ツールを接続する規格です。A2: 最大のメリットはセッションを跨いだ記憶の保持。A3: コマンドはこの通りです。すべて答えられましたか？自信がない場合は、該当スライドに戻って復習してください。
-->

---

<!-- _class: cover -->

# 第6章 完了 🎓
## 次は 終章「中級編への橋渡し」

<div class="meta">
✅ MCP（Model Context Protocol）とは何か<br>
✅ memory MCPでセッションを跨ぐ記憶を実現<br>
✅ MCPサーバーの設定手順<br>
✅ Before/After比較で生産性差を理解<br>
✅ MCPの選び方と注意点<br><br>
<b>次は終章「中級編への橋渡し」をお楽しみください</b>
</div>

<!--
ご視聴ありがとうございました。この章で、AIに外部ツールを接続する仕組み「MCP」の基本を理解できました。memory MCPで記憶を保持し、毎回の説明の手間を省ける。これが実務での生産性向上に直結します。次は終章で、初級編全体の振り返りと中級編への橋渡しを行います。ここまでお疲れさまでした。
-->
