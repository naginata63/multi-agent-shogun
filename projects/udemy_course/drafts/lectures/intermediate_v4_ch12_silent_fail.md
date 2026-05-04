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

# Guardrails 設計: Silent Fail 検出パターン
## エラーなし ≠ 成功 を見抜く監視仕組み

<div class="meta">
中級編 v4 — 第12章 (約 40 min)<br>

「AI開発の3階層 — プロンプト/コンテキスト/ハーネス エンジニアリング完全解説」<br><br>
講師: なぎなた
</div>

<!--
スピーカーノート:
中級編第12章へようこそ。テーマはGuardrails設計とSilent Fail検出です。エラーログに何も出ていないのに、結果がおかしい。これが静かな失敗、silent failです。最も危険なタイプの失敗です。この章では、Bounded Deterministic Workflowsの考え方に基づき、沈黙の失敗を検出するGuardrailsの設計パターンを解説します。40分間、一緒に学んでいきましょう。なぎなたと申します。
-->

---

## この章で学ぶこと [L3: Apply + Create]

1. **Silent Fail** の正体を説明し、3つの実例を挙げられる
2. **Guardrails** の概念とBounded Deterministic Workflowsを理解する
3. **inotifywait** によるファイルイベント監視の仕組みを設計できる
4. **Exclusion Filter** で自己フィードバックループを防ぐ設計ができる
5. **常駐監視daemon** の構成方法を理解する

<!--
この章では5つの到達点を目指します。Silent Failの正体を理解し、Guardrailsの概念を把握します。inotifywaitによるファイル監視、Exclusion Filterによる自己ループ防止、常駐daemonの構成までをカバーします。
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

# Guardrails と Bounded Deterministic Workflows

**Guardrails** = エージェントの出力が期待範囲内にあることを検証する仕組み

**Bounded Deterministic Workflows** = 非決定的なAIの動作を、決定的な境界(bound)で囲む設計思想

| 設計パターン | 役割 | この章での実装 |
|------------|------|--------------|
| **Output Guardrails** | 出力の妥当性検証 | ファイルサイズ・内容チェック |
| **Process Guardrails** | 実行プロセスの監視 | inotifywait常駐監視 |
| **Feedback Guardrails** | 自己ループの防止 | Exclusion Filter |

> GuardrailsはCI/CDの**テストスイート**と同じ — 期待する振る舞いを宣言し、違反を自動検出する

<!--
GuardrailsとBounded Deterministic Workflowsの概念です。Guardrailsはエージェントの出力が期待範囲内にあることを検証する仕組みで、Output、Process、Feedbackの3種類があります。Bounded Deterministic Workflowsは、非決定的なAIの動作を決定的な境界で囲む設計思想です。CI/CDのテストスイートと同じ考え方で、期待する振る舞いを宣言し、違反を自動検出します。
-->

---

# Silent Fail 事例3選

### 事例1: 「空ファイル成功」
- エージェントがファイルを出力 → 中身が空 → **exit code 0（成功）**
- 検出: ファイルサイズが0バイトかチェック

### 事例2: 「部分成功」
- 100件中60件だけ処理 → 残り40件はスキップ → **ログにエラーなし**
- 検出: 期待件数と実際の件数を比較

### 事例3: 「古い成果物の再利用」
- エージェントが新規作成を指示されたが、**既存ファイルをそのまま放置**
- 検出: ファイルの更新日時を確認

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

# Process Guardrails — inotifywait監視

**inotifywait** = Linuxのinotify APIを使ったファイルイベント監視ツール

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
Process Guardrailsの実装です。inotifywaitを使うと、ファイルの作成、変更、削除などのイベントをリアルタイムで検出できます。これをdaemon化すれば、バックグラウンドで常時監視が可能になり、エージェントがファイルを出力した瞬間に内容をチェックできます。
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
Feedback GuardrailsであるExclusion Filterの仕組みです。チェックスクリプトが結果をファイルに書き出すと、inotifywaitがその変更を検出し、無限ループに陥ります。除外パターンを設定して、特にチェック結果ファイルのパターンを除外することが重要です。基本的な原則として、監視対象と監視結果の出力先は必ず分離する必要があります。
-->

---

# 常駐監視daemonの構成

**目標**: ログイン時に自動起動し、常時バックグラウンドで監視

```
# ~/.config/systemd/user/silent-fail-watcher.service
[Unit]
Description=Silent Fail Watcher (Output Guardrails)

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
監視daemonをsystemd user serviceとして登録する方法です。ログイン時に自動起動し、常時バックグラウンドで動作します。Restartをon-failureに設定すれば、異常終了時も自動再起動します。有効化はsystemctl、状態確認はstatus、ログ確認はjournalctlで行います。
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
  # Output Guardrail 1: file size
  size=$(wc -c < "$filepath")
  if [ "$size" -eq 0 ]; then
    echo "WARN: empty file - $filepath" >> "$LOG_FILE"
  fi
  # Output Guardrail 2: required keyword
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
- **Guardrails** は3種類: Output / Process / Feedback
- **Bounded Deterministic Workflows**: 非決定的なAIを決定的な境界で囲む
- **inotifywait**: ファイルイベントをリアルタイム監視するProcess Guardrails
- **Exclusion Filter**: 自己フィードバックループ防止が必須 (Feedback Guardrails)
- **systemd user service**: 常駐daemonとして安定運用

<!--
この章のまとめです。Silent Failは最も危険な失敗形態で、Guardrailsの3種類で検出します。Bounded Deterministic Workflowsの考え方に基づき、inotifywaitによるProcess Guardrails、Exclusion FilterによるFeedback Guardrails、そしてsystemdによる常駐化までを学びました。
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
確認問題です。Q1、Silent Failが危険な理由は、ログにエラーが出力されないため気づかない間に被害が拡大するからです。Q2、Exclusion Filterが必要な理由は、チェック結果の書込をinotifywaitが検出し、無限ループに陥るのを防ぐためです。Q3、常時稼働にはsystemd user serviceが最適です。
-->

---

<!-- _class: cover -->

# 第12章 完了!
## Guardrails で Silent Fail を検出する仕組みを理解したか?

**到達点チェック**:
- ✅ Silent Failの事例を3つ挙げられる
- ✅ Guardrailsの3種類 (Output/Process/Feedback) を説明できる
- ✅ inotifywait監視の仕組みを設計できる
- ✅ Exclusion Filterで自己ループを防止できる
- ✅ 常駐監視daemonの構成方法を理解している

**次章**: Phase間ゲートと cmd intake ハーネス

<div class="meta">
講師: なぎなた
</div>

<!--
第12章完了です。GuardrailsでSilent Failを検出する仕組みを理解できたでしょうか。到達点を振り返りましょう。事例3選、Guardrailsの3種類、inotifywait監視、Exclusion Filter、常駐daemon構成の5つを理解できていれば完璧です。次章ではPhase間ゲートとcmd intakeハーネスを解説します。
-->
