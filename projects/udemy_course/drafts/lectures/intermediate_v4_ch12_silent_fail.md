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

# 自動検査ラインで見抜く「静かな失敗」
## エラーなし ≠ 成功 — Silent Fail検出パターン

<div class="meta">
中級編 v4 — 第12章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第12章へようこそ。テーマは「静かな失敗」の検出です。エラーログに何も出ていないのに、結果がおかしい。これがSilent Failです。最も危険なタイプの失敗です。この章では、沈黙の失敗を自動検出する仕組みの設計パターンを解説します。40分間、一緒に学んでいきましょう。なぎなたと申します。
-->

---

## この章で出てくる用語

> この章で初めて登場する用語を先にまとめます。安心して読み進めてください。

| 用語 | 読み方 | この章での意味 |
|------|--------|----------------|
| **Silent Fail** | サイレント・フェイル | エラーメッセージが出ないのに、結果が間違っている失敗（静かな失敗） |
| **自動検査ライン（Guardrails）** | — | エージェントの出力が正しいか自動チェックする仕組み |
| **inotifywait** | イノティファイ・ウェイト | Linuxでファイルの作成・変更・削除をリアルタイム検知するツール |
| **Exclusion Filter** | — | 監視システム自身の書込を無視して、無限ループを防ぐ仕組み |
| **daemon** | デーモン | バックグラウンドで常に動き続けるプログラム |

---

## この章で学ぶこと

1. **Silent Fail** の正体を説明し、3つの実例を挙げられる
2. **自動検査ライン** の3種類（出力検査 / 実行監視 / ループ防止）を理解する
3. **inotifywait** によるファイルイベント監視の仕組みを設計できる
4. **Exclusion Filter** で自己ループを防ぐ設計ができる
5. **常駐監視daemon** の構成方法を理解する

<!--
この章では5つの到達点を目指します。Silent Failの正体を理解し、自動検査ラインの3種類を把握します。inotifywaitによるファイル監視、Exclusion Filterによる自己ループ防止、常駐daemonの構成までをカバーします。
-->

---

# 「エラーなし」≠「成功」

> 「ログにエラーが1行も出ていない。でも、出力ファイルが空だった。」
> — これが **silent fail（静かな失敗）** です。

- **通常のエラー**: エラーメッセージが出る → 気づける → 直せる
- **silent fail**: エラーメッセージが出ない → 気づかない → **被害が拡大**する
- AIエージェント開発では特にsilent failが起きやすい
  - エージェントが「完了しました」と報告しても、**実際には未完了**のケースがある

<!--
つかみのスライドです。エラーログに何も出ていないのに、結果がおかしい。これがsilent failです。通常のエラーはメッセージが出るので気づけますが、silent failはメッセージが出ないため、気づかない間に被害が拡大します。エージェント開発では特にこの問題が起きやすいです。
-->

---

# 自動検査ライン（Guardrails）の3種類

> AIの出力が「正しいか」を自動でチェックする仕組みを **自動検査ライン（Guardrails）** と呼びます

**日常の例え**: 工場の出荷検査を思い浮かべてください
- **出荷品質検査** → 出力の中身が正しいか（ファイルサイズ、必須項目の有無）
- **製造ライン監視** → 製造工程が正しく動いているか（ファイルの作成・変更をリアルタイム監視）
- **検査の検査** → 検査ツール自身が誤動作していないか（無限ループ防止）

| 検査の種類 | 役割 | この章での実装 |
|------------|------|--------------|
| **出力検査（Output Guardrails）** | 出力の妥当性検証 | ファイルサイズ・内容チェック |
| **実行監視（Process Guardrails）** | 実行プロセスの監視 | inotifywait常駐監視 |
| **ループ防止（Feedback Guardrails）** | 自己ループの防止 | Exclusion Filter |

> AIは毎回違う答えを出す可能性があります。自動検査ラインで「期待する結果」の枠を決め、外れたら即座に検出する — この設計思想を「囲い込み設計」と呼びます

<!--
自動検査ラインの3種類を解説します。工場の出荷検査に例えると分かりやすいです。出荷品質検査で出力の中身を確認し、製造ライン監視で工程をリアルタイム監視し、検査の検査でツール自身の誤動作を防ぎます。AIは毎回違う答えを出す可能性があるため、自動検査ラインで「期待する結果」の枠を決めておくことが重要です。
-->

---

# Silent Fail 事例3選

### 事例1: 「空ファイル成功」
- エージェントがファイルを出力 → 中身が空 → **exit code 0（成功）**
- 検出方法: ファイルサイズが0バイトかチェック（→ 出力検査で対応）

### 事例2: 「部分成功」
- 100件中60件だけ処理 → 残り40件はスキップ → **ログにエラーなし**
- 検出方法: 期待件数と実際の件数を比較（→ 出力検査で対応）

### 事例3: 「古い成果物の再利用」
- エージェントが新規作成を指示されたが、**既存ファイルをそのまま放置**
- 検出方法: ファイルの更新日時を確認（→ 出力検査で対応）

<!--
silent failの典型的な事例3選です。1つ目は空ファイル成功で、中身が空でもexit code 0で成功扱いになります。2つ目は部分成功で、一部だけ処理して残りをスキップしていますがログにエラーは出ません。3つ目は古い成果物の再利用です。いずれもエラーログには何も出ないため、Guardrailsがなければ発見できません。
-->

---

# Output Guardrails — grepパターン設計

**アプローチ**: 「成功すべきだったが、成功していない」兆候をgrepで探す

| 兆候 | 検出パターン | 内容 |
|------|-------------|------|
| 空ファイル | `wc -c` = 0 | 出力ファイルが0バイト |
| 件数不足 | `grep -c` < 期待値 | 処理件数が期待より少ない |
| 古い成果物 | `find -mtime` | 最終更新が古すぎる |
| キーワード不在 | `grep -c '必須語'` = 0 | 成果物に必須情報が含まれない |

> **設計のコツ**: 「成功とは何か」を定義し、その逆を検出パターンで探す

<!--
Output Guardrailsのgrepパターン設計です。基本的な考え方は「成功の定義の逆」を検出することです。空ファイル、件数不足、古い成果物、キーワード不在の4つのパターンで検出します。設計のコツは、まず「成功とは何か」を明確に定義し、その逆をgrepで探すことです。
-->

---

# 実行監視 — inotifywait（イノティファイ・ウェイト）によるファイル監視

> **inotifywait** は、Linuxに標準搭載されているファイル監視ツールです
> （Windows/macOSの方は、後述のWSL推奨または代替ツールをご利用ください）

- **監視できるイベント**:
  - `create` — ファイルが作成された
  - `modify` — ファイルが変更された
  - `delete` — ファイルが削除された

- **基本的な使い方**:
  ```
  inotifywait -m -e create,modify \
    --format '%w%f %e' /path/to/watch/
  ```

- **daemon化**すれば、バックグラウンドで常時監視可能

<!--
実行監視の実装です。inotifywaitはLinuxに標準搭載されているファイル監視ツールで、ファイルの作成、変更、削除などのイベントをリアルタイムで検出できます。Windows/macOSの方はWSLの利用を推奨しています。これをdaemon化すれば、バックグラウンドで常時監視が可能になり、エージェントがファイルを出力した瞬間に内容をチェックできます。
-->

---

# 監視daemonの全体フロー

```
ファイル変更イベント
    ↓
inotifywait が検出
    ↓
★ Exclusion Filter ★ ← Feedback Guardrails
    ↓ (通過)
Output Guardrails 実行
  - ファイルサイズ確認
  - 必須キーワード確認
  - 期待件数確認
    ↓
結果に応じて通知
  - OK → ログに記録
  - NG → WARN通知を送信
```

<!--
監視daemonの全体フローです。inotifywaitがファイル変更を検出し、Exclusion Filterを通過した後にOutput Guardrailsが実行されます。チェック内容はファイルサイズ、必須キーワード、期待件数です。OKならログ記録、NGならWARN通知を送信します。
-->

---

# Feedback Guardrails — Exclusion Filter

**問題**: チェックスクリプト自体がファイルを書き換えると、
inotifywaitがそれを検出 → 再度チェック → また書き換え... **無限ループ**

**解決策**: 除外パターンで自分自身の書込を無視する

```
# 除外パターンを配列で定義
EXCLUDE_PATTERNS=(
  "\.tmp"
  "\.log"
  "\.check_result_"
)

# 配列から正規表現を組み立ててinotifywaitに渡す
EXCLUDE_REGEX=$(IFS='|'; echo "(${EXCLUDE_PATTERNS[*]})")
inotifywait -m --exclude "$EXCLUDE_REGEX" \
  -e create,modify /path/to/watch/
```

> **原則**: 監視対象と監視結果の出力先は **必ず分離** する

<!--
Feedback GuardrailsであるExclusion Filterの仕組みです。チェックスクリプトが結果をファイルに書き出すと、inotifywaitがその変更を検出し、無限ループに陥ります。除外パターンを設定して、特にチェック結果ファイルのパターンを除外することが重要です。基本的な原則として、監視対象と監視結果の出力先は必ず分離する必要があります。
-->

---

# 常駐監視daemonの構成

**目標**: ログイン時に自動起動し、常時バックグラウンドで監視

> **注意**: 以下はLinux（systemd）の構成例です。Windowsの方は「タスクスケジューラ」、macOSの方は「launchd」で同等の設定が可能です

```
# ~/.config/systemd/user/silent-fail-watcher.service
# (Linux systemd の設定ファイル)

[Unit]
Description=Silent Fail Watcher (自動検査ライン)

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
監視daemonをsystemd user serviceとして登録する方法です。ログイン時に自動起動し、常時バックグラウンドで動作します。Restartをon-failureに設定すれば、異常終了時も自動再起動します。これはLinuxの構成例ですが、Windowsならタスクスケジューラ、macOSならlaunchdで同等の設定が可能です。
-->

---

# 実装例 — silent_fail_watcher.sh 骨格

```bash
#!/bin/bash
# 監視ディレクトリ（引数がなければ ./output を使用）
WATCH_DIR="${1:-./output}"
# ログファイルの場所
LOG_FILE="/tmp/silent_fail.log"

# inotifywaitで監視開始
# -m: 永続的に監視（終了しない）
# -e create,modify: 作成と変更イベントのみ監視
# --exclude: tmpとlogファイルを除外
# --format '%w%f': 出力形式を「ディレクトリパス+ファイル名」に
inotifywait -m -e create,modify \
  --exclude '(\.tmp|\.log)' \
  --format '%w%f' "$WATCH_DIR" | \
# パイプで1行ずつ処理
while read -r filepath; do
  # 出力検査1: ファイルサイズ確認
  # wc -c: バイト数を取得
  size=$(wc -c < "$filepath")
  # -eq 0: サイズが0（空ファイル）なら警告
  if [ "$size" -eq 0 ]; then
    echo "WARN: empty file - $filepath" >> "$LOG_FILE"
  fi
  # 出力検査2: 必須キーワード確認
  # grep -q: 見つかったら真、見つからなければ偽
  # !: 結果を反転（見つからなかった場合に警告）
  if ! grep -q 'required_header' "$filepath"; then
    echo "WARN: missing keyword - $filepath" >> "$LOG_FILE"
  fi
done
```

> ※本講座サンプル実装 — 実際のプロジェクトでは監視ディレクトリ・除外パターン・チェック内容を環境に合わせて調整します

<!--
実際の監視スクリプトの骨格です。inotifywaitで監視ディレクトリのcreateとmodifyイベントを監視し、tmpファイルとlogファイルを除外します。ファイルサイズと必須キーワードの2つのOutput Guardrailsを実装しています。この骨格に件数チェックや更新日時チェックを追加していくことで、プロジェクトに合わせたGuardrailsを構築できます。
-->

---

# 検出から通知までのフロー

| 段階 | 処理 | 出力 |
|------|------|------|
| 1. 検出 | inotifywaitがイベント取得 | イベント情報 |
| 2. フィルタ | Exclusion Filterで除外判定 | 監視対象のみ通過 |
| 3. チェック | Output Guardrailsの検証 | OK/NG判定 |
| 4. 通知 | NGの場合にアラート送信 | WARN通知 |
| 5. 記録 | 全結果をログに保存 | 監査ログ |

**通知手段の選択肢**:
- `ntfy` — HTTPベースの軽量通知
- `Slack Webhook` — チーム内共有
- `mail` — 緊急度が高い場合

<!--
検出から通知までの5段階フローです。検出、フィルタ、チェック、通知、記録の順です。通知手段は複数あり、プロジェクトに合わせて選べます。全結果は監査ログとして記録し、後から振り返れるようにします。これがBounded Deterministic Workflowsの実践例です。
-->

---

# この章のまとめ

- **Silent Fail** はエラーなしで発生する最も危険な失敗形態
- **自動検査ライン** は3種類: 出力検査 / 実行監視 / ループ防止
- **inotifywait**: ファイルイベントをリアルタイム監視する（Linux専用）
- **Exclusion Filter**: 監視ツール自身の書込による無限ループ防止が必須
- **常駐daemon**: Linuxはsystemd / Windowsはタスクスケジューラ / macOSはlaunchdで構成

<!--
この章のまとめです。Silent Failは最も危険な失敗形態で、自動検査ラインの3種類で検出します。inotifywaitによる実行監視、Exclusion Filterによるループ防止、そしてsystemd等による常駐化までを学びました。
-->

---

# 確認問題

**Q1**: Silent Failが通常のエラーより危険な理由は？
- A: ログにエラーが出力されないため気づかない
- B: エラーメッセージが長すぎて読めない
- C: 修正に時間がかかるから

**Q2**: Feedback Guardrails (Exclusion Filter) が必要な理由は？
- A: 監視対象外のファイルを除外するため
- B: チェックスクリプト自身の書込による無限ループを防ぐため
- C: 通知を減らすため

**Q3**: 監視daemonを常時稼働させる方法は？
- A: cronに登録する
- B: systemd user serviceとして登録する
- C: ターミナルを開きっぱなしにする

<!--
確認問題です。Q1、Silent Failが危険な理由は、ログにエラーが出力されないため気づかない間に被害が拡大するからです。Q2、Exclusion Filterが必要な理由は、チェックスクリプトの結果書込をinotifywaitが検出し、無限ループに陥るのを防ぐためです。Q3、常時稼働にはLinuxならsystemd user serviceが最適です。Windowsならタスクスケジューラ、macOSならlaunchdになります。
-->

---

<!-- _class: cover -->

# 第12章 完了!
## Silent Failを検出する自動検査ラインを理解したか?

**到達点チェック**:
- ✅ Silent Failの事例を3つ挙げられる
- ✅ 自動検査ラインの3種類（出力検査/実行監視/ループ防止）を説明できる
- ✅ inotifywait監視の仕組みを設計できる
- ✅ Exclusion Filterで自己ループを防止できる
- ✅ 常駐監視daemonの構成方法を理解している

**次章**: Phase間ゲートと cmd intake ハーネス

<div class="meta">
講師: なぎなた
</div>

<!--
第12章完了です。Silent Failを自動検出する仕組みを理解できたでしょうか。到達点を振り返りましょう。事例3選、自動検査ラインの3種類、inotifywait監視、Exclusion Filter、常駐daemon構成の5つを理解できていれば完璧です。次章ではPhase間ゲートとcmd intakeハーネスを解説します。
-->
