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

# silent fail 検出ハーネス
## 沈黙を破る監視員

<div class="meta">
中級編 v4 — 第12章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第12章へようこそ。テーマは「silent fail検出ハーネス」です。エラーログに何も出ていないのに、結果がおかしい。これが静かな失敗、silent failです。一番危険なタイプの失敗です。この章では、沈黙を破る監視員の仕組みを解説します。40分間、一緒に学んでいきましょう。なぎなたと申します。
-->

---

## この章で学ぶこと [L6: Create]

1. **silent fail** の正体を説明し、3つの実例を挙げられる
2. **ログから候補を抽出** するgrepパターンを設計できる
3. **inotifywait監視daemon** の仕組みを説明できる
4. **exclusion filter** で自己フィードバックループを防ぐ設計ができる
5. **systemd user service** 化して常駐監視を構成できる

<!--
この章では5つの到達点を目指します。Bloomの分類で言えばCreateレベル、最高到達度です。silent failの正体を理解するだけでなく、実際に検出する仕組みを設計できるようになります。具体的には、ログから候補を抽出する方法、inotifywaitによるファイル監視、exclusion filterによる自己ループ防止、そしてsystemdを使った常駐化までをカバーします。
-->

---

# 「エラーなし」≠「成功」

> 「ログにエラーが1行も出ていない。でも、出力ファイルが空だった。」
> — これが **silent fail（静かな失敗）** です。

- **通常のエラー**: エラーメッセージが出る → 気づける → 直せる
- **silent fail**: エラーメッセージが出ない → 気づかない → **被害が拡大**する
- AI開発では特にsilent failが起きやすい
  - AIが「完了しました」と報告しても、**実際には未完了**のケースがある

<!--
つかみのスライドです。エラーログに何も出ていないのに、結果がおかしい。これがsilent failです。通常のエラーはメッセージが出るので気づけますが、silent failはメッセージが出ないため、気づかない間に被害が拡大します。AI開発では特にこの問題が起きやすいです。AIが「完了しました」と報告しても、実際には未完了というケースがあるのです。
-->

---

# silent fail 事例3選

### 事例1: 「空ファイル成功」
- AIがファイルを出力 → 中身が空 → **exit code 0（成功）**
- 検出方法: ファイルサイズが0バイトかチェック

### 事例2: 「部分成功」
- 100件中60件だけ処理 → 残り40件はスキップ → **ログにエラーなし**
- 検出方法: 期待件数と実際の件数を比較

### 事例3: 「古い成果物の再利用」
- AIが新規作成を指示されたが、**既存ファイルをそのまま放置**
- 検出方法: ファイルの更新日時を確認

<!--
silent failの典型的な事例を3つ紹介します。1つ目は空ファイル成功です。AIがファイルを出力したものの、中身が空で、exit codeは0、つまり成功扱いになります。2つ目は部分成功です。100件処理するはずが60件だけで終わり、残りはスキップされていますが、ログにエラーは出ません。3つ目は古い成果物の再利用です。AIが新規作成を指示されたのに、既存ファイルをそのまま放置しているケースです。いずれもエラーログには何も出ないため、監視仕組みがないと発見できません。
-->

---

# ログから候補を抽出する — grepパターン設計

**アプローチ**: 「成功すべきだったが、成功していない」兆候をgrepで探す

| 兆候 | grepパターン | 検出内容 |
|------|-------------|---------|
| 空ファイル | `wc -c` = 0 | 出力ファイルが0バイト |
| 件数不足 | `grep -c` < 期待値 | 処理件数が期待より少ない |
| 古い成果物 | `find -mtime` | 最終更新が古すぎる |
| キーワード不在 | `grep -c '必須語'` = 0 | 成果物に必須情報が含まれない |

> **設計のコツ**: 「成功とは何か」を定義し、その逆をgrepで探す

<!--
ログからsilent failの候補を抽出する方法です。基本的な考え方は、「成功すべきだったが、成功していない」兆候をgrepで探すことです。空ファイルならwc -cで0バイトを検出、件数不足ならgrep -cで期待値と比較、古い成果物ならfind -mtimeで更新日時をチェックします。設計のコツは、「成功とは何か」を明確に定義し、その逆をgrepで探すことです。
-->

---

# inotifywait — ファイルイベントをリアルタイム監視

**inotifywait** = Linuxのinotify APIを使ったファイルイベント監視ツール

- **監視できるイベント**:
  - `create` — ファイルが作成された
  - `modify` — ファイルが変更された
  - `delete` — ファイルが削除された
  - `moved_to` — ファイルが移動された
- **基本的な使い方**:
  ```
  inotifywait -m -e create,modify \
    --format '%w%f %e' /path/to/watch/
  ```

- **daemon化**すれば、バックグラウンドで常時監視可能

<!--
inotifywaitは、Linuxのinotify APIを使ったファイルイベント監視ツールです。ファイルの作成、変更、削除、移動などのイベントをリアルタイムで検出できます。基本的な使い方は、監視対象ディレクトリとイベント種別を指定するだけです。これをdaemon化すれば、バックグラウンドで常時監視が可能になります。AIがファイルを出力した瞬間に検出し、すぐに内容をチェックする仕組みを作れます。
-->

---

# 監視daemonの仕組み — 全体フロー

```
ファイル変更イベント
    ↓
inotifywait が検出
    ↓
★ exclusion filter ★ ← ここが重要
    ↓ (通過)
チェックスクリプト実行
  - ファイルサイズ確認
  - 必須キーワード確認
  - 期待件数確認
    ↓
結果に応じて通知
  - OK → ログに記録
  - NG → WARN通知を送信
```

<!--
監視daemonの全体フローを図解します。ファイル変更イベントをinotifywaitが検出し、exclusion filterを通過した後にチェックスクリプトが実行されます。チェック内容は、ファイルサイズ、必須キーワード、期待件数などです。結果がOKならログに記録、NGならWARN通知を送信します。ここで特に重要なのがexclusion filterです。次のスライドで詳しく解説します。
-->

---

# exclusion filter — 自己フィードバックループの防止

**問題**: チェックスクリプト自体がファイルを書き換えると、
inotifywaitがそれを検出 → 再度チェック → また書き換え... **無限ループ**

**解決策**: 除外パターンで自分自身の書込を無視する

```
# exclusion filterの例
EXCLUDE_PATTERNS=(
  "*.tmp"
  "*.log"
  ".check_result_*"  # チェック結果ファイル
  "~*"
)

# inotifywaitに除外を渡す
inotifywait -m --exclude '(\.tmp|\.log|\.check_result_)' \
  -e create,modify /path/to/watch/
```

> **原則**: 監視対象と監視結果の出力先は **必ず分離** する

<!--
exclusion filterは、自己フィードバックループを防ぐための重要な仕組みです。チェックスクリプトが結果をファイルに書き出すと、inotifywaitがそのファイル変更を検出し、再度チェックを実行してしまい、無限ループに陥ります。これを防ぐために、除外パターンを設定します。特にチェック結果ファイルのパターンを除外することが重要です。基本的な原則として、監視対象と監視結果の出力先は必ず分離する必要があります。
-->

---

# systemd user service化 — 常駐daemonとして運用

**目標**: ログイン時に自動起動し、常時バックグラウンドで監視

```
# ~/.config/systemd/user/silent-fail-watcher.service
[Unit]
Description=Silent Fail Watcher

[Service]
ExecStart=/path/to/silent_fail_watcher.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

- **有効化**: `systemctl --user enable silent-fail-watcher`
- **状態確認**: `systemctl --user status silent-fail-watcher`
- **ログ確認**: `journalctl --user -u silent-fail-watcher -f`

<!--
監視daemonをsystemd user serviceとして登録すれば、ログイン時に自動起動し、常時バックグラウンドで動作します。serviceファイルの書き方は標準的なsystemdの形式です。ExecStartに監視スクリプトのパスを指定し、Restartをon-failureに設定すれば、異常終了時も自動再起動します。有効化はsystemctl --user enableで、状態確認はstatus、ログ確認はjournalctlで行います。
-->

---

# 検出から通知までのフロー

| 段階 | 処理 | 出力 |
|------|------|------|
| 1. 検出 | inotifywaitがイベント取得 | イベント情報 |
| 2. フィルタ | exclusion filterで除外判定 | 監視対象のみ通過 |
| 3. チェック | ルールベースの検証 | OK/NG判定 |
| 4. 通知 | NGの場合にアラート送信 | WARN通知 |
| 5. 記録 | 全結果をログに保存 | 監査ログ |

**通知手段の選択肢**:
- `ntfy` — HTTPベースの軽量通知
- `Slack Webhook` — チーム内共有
- `mail` — 緊急度が高い場合

<!--
検出から通知までのフローを5段階で整理します。検出、フィルタ、チェック、通知、記録の順です。検出はinotifywaitが担当し、フィルタで監視対象以外を除外します。チェックはルールベースの検証で、NGの場合のみ通知を送信します。通知手段は複数あり、プロジェクトに合わせて選べます。ntfyはHTTPベースの軽量通知、Slack Webhookはチーム内共有に便利です。全結果は監査ログとして記録し、後から振り返れるようにします。
-->

---

# 実装例 — silent_fail_watcher.sh 骨格

```bash
#!/bin/bash
WATCH_DIR="${1:-./output}"
LOG_FILE="/tmp/silent_fail.log"

inotifywait -m -e create,modify \
  --exclude '(\.tmp|\.log)' \
  --format '%w%f' "$WATCH_DIR" | \
while read -r filepath; do
  # Check 1: file size
  size=$(wc -c < "$filepath")
  if [ "$size" -eq 0 ]; then
    echo "WARN: empty file - $filepath" >> "$LOG_FILE"
  fi
  # Check 2: required keyword
  if ! grep -q 'required_header' "$filepath"; then
    echo "WARN: missing keyword - $filepath" >> "$LOG_FILE"
  fi
done
```

<!--
実際の監視スクリプトの骨格を示します。inotifywaitで監視ディレクトリのcreateとmodifyイベントを監視し、tmpファイルとlogファイルを除外します。イベントを検出したら、まずファイルサイズをチェックし、0バイトならWARNを記録します。次に必須キーワードの有無をチェックし、欠落していればWARNを記録します。この骨格に、件数チェックや更新日時チェックを追加していくことで、プロジェクトに合わせた監視スクリプトを構築できます。
-->

---

# この章のまとめ

- **silent fail** はエラーなしで発生する最も危険な失敗形態
- **grepパターン設計**: 「成功の定義」の逆を探す
- **inotifywait**: ファイルイベントをリアルタイム監視
- **exclusion filter**: 自己フィードバックループ防止が必須
- **systemd user service**: 常駐daemonとして安定運用
- **検出→通知→記録** の5段階フローで運用する

<!--
この章のまとめです。silent failはエラーなしで発生するため、最も危険な失敗形態です。検出にはgrepパターンの設計が重要で、「成功の定義」の逆を探すアプローチを取りました。inotifywaitによるリアルタイム監視、exclusion filterによる自己ループ防止、systemd user serviceによる常駐化、そして5段階のフローでの運用までを学びました。これがL3ハーネス層の実践的な設計例です。
-->

---

# 確認問題

**Q1**: silent failが通常のエラーより危険な理由は？
- A: ログにエラーが出力されないため気づかない
- B: エラーメッセージが長すぎて読めない
- C: 修正に時間がかかるから

**Q2**: exclusion filterが必要な理由は？
- A: 監視対象外のファイルを除外するため
- B: チェックスクリプト自身の書込による無限ループを防ぐため
- C: 通知を減らすため

**Q3**: 監視daemonを常時稼働させる方法は？
- A: cronに登録する
- B: systemd user serviceとして登録する
- C: ターミナルを開きっぱなしにする

<!--
確認問題です。Q1、silent failが通常のエラーより危険な理由は、ログにエラーが出力されないため気づかない間に被害が拡大するからです。Q2、exclusion filterが必要な理由は、チェックスクリプト自身のファイル書込をinotifywaitが検出し、無限ループに陥るのを防ぐためです。Q3、監視daemonを常時稼働させるにはsystemd user serviceとして登録するのが最適です。ログイン時に自動起動し、異常終了時も再起動します。
-->

---

<!-- _class: cover -->

# 第12章 完了!
## 沈黙を破る監視員を設計できたか?

**到達点チェック**:
- ✅ silent failの事例を3つ挙げられる
- ✅ grepパターンで候補抽出を設計できる
- ✅ inotifywait監視の仕組みを説明できる
- ✅ exclusion filterで自己ループを防止できる
- ✅ systemd user service化ができる

**次章**: Phase間ゲートとcmd intakeハーネス

<div class="meta">
講師: なぎなた
</div>

<!--
第12章完了です。silent failを検出する監視員の仕組みを設計できましたか。到達点を振り返りましょう。事例3選、grepパターン設計、inotifywait監視、exclusion filter、systemd user service化の5つを理解できていれば完璧です。次章では、Phase間ゲートとcmd intakeハーネスを解説します。タスク起票時に自動で過去事例を検索する仕組みです。引き続き学んでいきましょう。
-->
