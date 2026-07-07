現在の作業状態を引き継ぎファイルに保存します。compactの代替としても使用可能。

以下の手順で実行してください：

1. 自分のagent_idを確認する:
   `tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}'`

2. タイムスタンプを取得し、直近のhandoffファイルを確認する:
   `date "+%Y%m%d-%H%M"`
   `ls queue/handoff/{agent_id}_*.md 2>/dev/null | sort | tail -1`

   **直近のhandoffが30分以内なら、新ファイルを作らずそのファイルをEditで更新せよ**（ファイル乱立防止。rehydrateは最新1枚しか読まないため、分散すると引き継ぎ漏れが起きる）。timestampフィールドだけ現在時刻に更新する。30分より古い場合のみ新規作成。

3. 以下の内容でhandoffファイルを作成してください:
   保存先: queue/handoff/{agent_id}_{YYYYMMDD-HHMM}.md

```markdown
# Handoff: {agent_id} @ {YYYYMMDD-HHMM}

## Agent
- agent_id: {agent_id}
- timestamp: {YYYYMMDD-HHMM}
- trigger: manual

## 会話サマリー（自分の言葉で要約）
**この会話で何が起きたかを3-5文で要約せよ。compaction後の自分が読んで状況を復元できるレベルで。**

例: 「殿の指示で_sVuKf5Zu4Aの竹取物語シーンと鼻歌シーンの漫画ショートを制作中。竹取物語は殿選定済み・P10タイムスタンプ修正版再生成待ち。鼻歌はDemucsボーカル+16dB版再生成待ち。極小MENはpanels JSONの文脈を殿と修正中（偽装死の正しい文脈に書き換え済み）。3Dシアター再現はv8でおんりーのscaleが未修正。」

## 殿との決定事項
**殿が判断・決定・修正した内容を全て記録。これが最も重要。会話を遡って原文ベースで正確に。推測で書くな。**

### 確定した構成・セリフ
（殿が確認済みの構成表・セリフ修正を正確に記載）

例:
- 竹取物語P1: 「おもれえ」（「おもれ」から修正）
- 鼻歌P1: 「ぱーぱぱっぱー♪」（「ランランラン」ではない）

### 殿の文脈説明
（殿がゲームの仕組みや動画の背景を教えてくれた内容）

例:
- 極小MENの偽装死: ベッドでリスポ更新→わざと高所落下→死亡ログ1回のみ→他メンバーが勘違いして自殺

### 殿がNGを出した内容
（やり直しの経緯・理由。同じ轍を踏まないため必須）

例:
- 3D悪だくみv1-v4: MEN体崩壊→方式A(.blend再インポート)で解決
- 鼻歌10セット再作成: 殿が「再作成不要」と言ったのに3回指示出した→反省

## 実行中バックグラウンドプロセス
**/clear後も生き続けるプロセスを必ず記録。復帰後の自分はこれを知らないと通知の意味が分からない。なければ「なし」と書く。**

| プロセス | 起動コマンド/スクリプト | ログ/出力先 | 完了・通知時の次アクション |
|---------|------------------------|------------|---------------------------|
| 例: DL再試行ループ | work/chara_zukan/dl_retry_loop.sh (30分毎×10回) | stdout(task通知) | 完了→build_final_v4.py実行 |

## 進行中タスク詳細
**cmd IDだけでなく、どこまで進んで何が残っているかを具体的に。**

| cmd | 内容 | 状態 | 次のアクション |
|-----|------|------|--------------|
| cmd_927 | シアター再現 | v8殿確認中。おんりーscale未修正 | scale=0.3に修正 |

## 足軽・軍師の状態
（shogun/karoのみ記載。ashigaru/gunshiはこのセクション省略可）

| agent | 状態 | 作業内容 |
|-------|------|---------|
| karo | idle | — |
| ashigaru3 | 作業中 | 極小MEN10セット再生成 |

## 殿への未回答・保留事項
（殿に聞かれて答えていないこと、後で対応すること）

## Affected Files
- 最近変更したファイル（git diff --name-only HEAD~5）
- 殿が直接編集したファイル（tono_select等）

## Next Actions（優先順）
1. {最優先}
2. {次}
3. {次}
```

4. **以下を必ず実行して情報を収集:**
   - `git diff --name-only HEAD~5` で最近の変更ファイル
   - 進行中cmd: `curl -s -w "\nHTTP %{http_code}\n" "http://192.168.2.4:8770/api/cmd_list?status=in_progress&slim=1"`
   - エージェント状態（shogun/karoのみ）: `curl -s -w "\nHTTP %{http_code}\n" "http://192.168.2.4:8770/api/agent_health"`（pane captureは最終手段）
   - バックグラウンドプロセス: 自分がこのセッションで起動した常駐/ループ処理を思い出し、`pgrep -af <script名>` で生存確認して表に記録
   - `dashboard.md` の🚨要対応を確認

5. **保存後、/clearする前に未読inboxを処理する:**
   `curl -s -w "\nHTTP %{http_code}\n" "http://192.168.2.4:8770/api/inbox_messages?agent={agent_id}&unread=1&limit=20"`
   未読があれば処理して `POST /api/inbox_mark_read` で既読化。未読を残したまま/clearすると、復帰後に古い未読を再ロードしてcontextを浪費する。

6. 保存後、ファイルパスを報告。
