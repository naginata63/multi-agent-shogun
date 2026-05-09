# Agent Common Rules

> **Lazy Load指示**: このファイルはタスク該当時のみ Read。Session Start では常時 Read しない。必要時にのみ参照せよ。

全エージェント共通ルール。各 `instructions/{role}.md` と併読すること。

---

## 1. Language & Tone

`config/settings.yaml` → `language` を確認:

- **ja**: 戦国風日本語のみ
- **Other**: 戦国風 + translation in parentheses

コード・YAML・技術文書の内容は正確に。戦国口調は会話・独り言のみ適用。
各役割の口調の詳細は `instructions/{role}.md` の persona セクションを参照。

---

## 2. Self-Identification (必須)

```bash
tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}'
```

- 出力から自分の ID を確認 (例: `ashigaru3` → 足軽3号)
- pane_index は再編成で変わるため **@agent_id** を使う
- 自分のファイルのみ読み書き。他エージェントのファイルは絶対に触らない
- 各役割のファイルパスは `instructions/{role}.md` を参照

---

## 3. Timestamp Rule

常に `date` コマンドを使用。推測禁止。

```bash
date "+%Y-%m-%dT%H:%M:%S"    # YAML (ISO 8601)
date "+%Y-%m-%d %H:%M"       # Dashboard API
```

---

## 4. Agent Self-Watch Phase Rules (cmd_107)

- **Phase 1**: startup 時 `process_unread_once` + inotify/event-driven monitoring + timeout fallback
- **Phase 2**: normal nudge suppressed (`disable_normal_nudge`); delivery confirmation must not depend on nudge
- **Phase 3**: `FINAL_ESCALATION_ONLY` — send-keys は最終回復のみ
- 評価指標: `unread_latency_sec` / `read_count` / `estimated_tokens`

---

## 5. Compaction Recovery 共通骨子

Compaction 後、CLAUDE.md の Session Start 手順を必ず実行:

1. 自己 ID 確認: `tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}'`
2. GET `/api/task_list?agent={self}&limit=5` → `assigned` タスク確認 (self-recovery 用途は YAML 直読みも許可・CLAUDE.md L116)
3. `context/{project}.md` を task の `project:` フィールド指定時のみ Read
4. MCP dashboard は補助情報。**API が一次情報**

役割固有の追加手順は各 `instructions/{role}.md` を参照。

---

## 6. /clear Recovery 共通骨子

/clear 後は CLAUDE.md の /clear Recovery 手順に従う:

1. `tmux display-message` で自己 ID 確認
2. `instructions/{role}.md` を Read (ルール変更反映用・**必須**)
3. `queue/tasks/{self}.yaml` → 末尾の `status:assigned` タスクを実行
4. GET `/api/inbox_messages?agent={self}&unread=1&limit=20` → 未読メッセージを処理
   (障害時 fallback: `queue/inbox/{self}.yaml` 直読み)
   処理後 `POST /api/inbox_mark_read` で既読化必須 (cmd_1495)

**禁止**: polling (F004), 人間直接連絡 (F002)。
task YAML のみを信頼。/clear 前の記憶は消滅。

---

## 7. セマンティック検索 (Gemini Embedding 2)

Grep/Glob に加えて `semantic_search.py` を活用:
- キーワード不明時・意味で検索したい時に有効

```bash
# 基本検索
source ~/.bashrc && python3 scripts/semantic_search.py query "検索キーワード"

# ソース絞り込み (scripts/srt/memory/context/git/logs等)
source ~/.bashrc && python3 scripts/semantic_search.py query "話者識別" --source scripts

# JSON出力 (プログラムから利用)
source ~/.bashrc && python3 scripts/semantic_search.py query "テスト" --json
```

インデックスは git commit 時に自動更新。手動更新: `python3 scripts/semantic_search.py update`

---

## 8. SSE Monitor 30秒 Warm-up ルール (cmd_1650)

**SSE Monitor は起動直後 30 秒間、接続確立と server 側の event flush に時間がかかる warm-up 期間を持つ。この間の メッセージ取りこぼしを補完すること:**

**Warm-up期間の対応**:

1. **Session Start 時**（sessionstart_hook.sh が Monitor を自動起動）
   - Monitor 起動直後 1 秒以内に届いたメッセージは race condition で取りこぼし可能性あり (cmd_1649 実証 60%)
   - **即座に** `GET /api/inbox_messages?agent={self}&unread=1&limit=20` で catch-up 取得
   - API から取得したメッセージを処理してから、通常の Monitor event 待ちに入る

2. **Monitor stream 終了時** (EOF 受信、server restart 等)
   - 自動再起動：`pgrep -a curl | grep "agent={self}"` で既存 Monitor 確認 → 無ければ1本起動
   - 起動後、同じく catch-up GET で warm-up 期間の取りこぼしを補完

3. **検証方法**:
   ```bash
   # Monitor 稼働確認
   pgrep -a curl | grep "agent=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}')"
   # → 0 件なら Monitor 未起動、1 件以上なら稼働中
   ```

**理由**: curl -N 接続確立 + server 側の SSE event flush に最大 30 秒かかることが実証済み (cmd_1669 実証)。
初期メッセージが届かない = Monitor が稼働していないのではなく、単に warm-up 期間中。
catch-up GET で確実にメッセージを受信できる。

---

## 8. Dashboard API 利用 (cmd_1494) 概要

cmd/inbox/task 系の操作は **HTTP API 経由を第一選択**。
YAML 直読み・bash inbox_write.sh 直叩きは段階的廃止。
詳細: `shared_context/procedures/dashboard_api_usage.md`

主なエンドポイント (LAN内・192.168.2.4:8770・認証なし):

| 動作 | エンドポイント |
|------|----------------|
| cmd 一覧 (filter/keyword) | `GET /api/cmd_list?status=&q=&limit=` |
| cmd 詳細 (1件) | `GET /api/cmd_detail?id=cmd_XXX` |
| 戦況集計 + 検出ルール | `GET /api/dashboard` |
| エージェント生存 | `GET /api/agent_health` |
| inbox メッセージ送信 | `POST /api/inbox_write` |
| cmd 起票 | `POST /api/cmd_create` |

各役割固有の利用パターンは `instructions/{role}.md` を参照。

---

## 9. Shout Mode (echo_message)

タスク完了後、DISPLAY_MODE を確認:

```bash
tmux show-environment -t multiagent DISPLAY_MODE
```

- **DISPLAY_MODE=shout**: 最後の tool call として Bash echo を実行
  - task YAML に `echo_message` があればそれを使用
  - なければ戦国風の戦功報告を1行で composing
  - echo 後はテキスト出力禁止 (❯ プロンプトの上に残す)
  - Plain text + emoji。罫線/box 禁止
- **DISPLAY_MODE=silent または未設定**: echo しない。skip
