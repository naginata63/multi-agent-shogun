# cmd_1673 API前提未更新ルール監査 (read-only)

- **作成**: 2026-05-09 08:35 JST / 軍師
- **対象**: CLAUDE.md / instructions/*.md / shared_context/**/*.md / memory/**/*.md / scripts/hooks 配下 / .claude/settings.json
- **観点**: cmd_1494 (SQLite dual-path / API一元化) 後に **API 前提に未更新で残っている旧ルール** を網羅検出
- **制約**: コード/ルール修正なし (read-only sweep)

---

## サマリ (severity 別件数)

| Severity | 件数 |
|----------|------|
| CRITICAL | 2 |
| HIGH     | 7 |
| MEDIUM   | 5 |
| LOW      | 5 |
| **合計** | **19** |

最大の構造的問題: `instructions/generated/` 配下 (codex/copilot/kimi 系) が **API 化前 (bash inbox_write.sh / YAML 直編集を primary とする) のスナップショット** のまま放置。Claude CLI 以外の CLI で起動したエージェントは旧経路に流れる。

---

## CRITICAL (2件)

### C001 — `instructions/generated/` ディレクトリ全体が API 化前のスナップショット

**file:line**:
- `instructions/generated/shogun.md:178,184,187,190,285,295,469,629,640`
- `instructions/generated/kimi-ashigaru.md:115,121,124,127,222,232,406`
- `instructions/generated/codex-ashigaru.md:115,121,124,127,222,232,406`
- `instructions/generated/copilot-ashigaru.md:115,121,124,127,222,232,406`
- `instructions/generated/gunshi.md:210,216,219,222,317`
- `instructions/generated/karo.md:312,320,329`
- `instructions/generated/copilot-karo.md:312,320,329,433-434,490,515,674`
- `instructions/generated/codex-shogun.md:194,202,211,729`
- `instructions/generated/kimi-gunshi.md:226,234,243,347-348,404,429,588,834`
- (他多数・generated 配下全7-8 ファイル)

**旧ルール引用**:
```
bash scripts/inbox_write.sh karo "cmd_048を書いた。実行せよ。" cmd_new shogun
bash scripts/inbox_write.sh karo "足軽5号、任務完了。報告YAML確認されたし。" report_received ashigaru5
queue/tasks/ashigaru{YOUR_NUMBER}.yaml    ← Read only this
```

**推奨改訂案**:
1. `instructions/generated/` 配下の再生成スクリプト (`scripts/build_instructions.sh` 等) を確認し、テンプレートを `instructions/{role}.md` の最新版から派生させる
2. 派生時に「primary = API curl, fallback = bash inbox_write.sh」順に並べ替え
3. 当面 codex/copilot/kimi CLI を使う予定がなければ `instructions/generated/` を削除 or リネーム (例: `instructions/generated.deprecated/`) して誤参照を防ぐ

**影響評価**: HIGH。codex/copilot/kimi 経由で家老/軍師/足軽を起動した場合、`Step 4: Read queue/tasks/ashigaru{N}.yaml → determine current task` 等の旧手順に流れ、API 経由の整合性 (cancelled_subtasks 自動伝播・dual-path lock 等) が機能しない。`memory/MEMORY.md` 記載「API 不信からの fallback 禁止 (家老が以下をすると殿激怒)」と generated/* の手順が真っ向対立。

---

### C002 — `instructions/ashigaru.md:322` が `queue/shogun_to_karo.yaml` 直 Read を要求

**file:line**: `instructions/ashigaru.md:322`

**旧ルール引用**:
> Purpose validation: Read `parent_cmd` in `queue/shogun_to_karo.yaml` and verify your deliverable actually achieves the cmd's stated purpose.

**推奨改訂案**:
```diff
- Read `parent_cmd` in `queue/shogun_to_karo.yaml`
+ Fetch parent_cmd via `curl -s http://192.168.2.4:8770/api/cmd_detail?id=<parent_cmd>` and read `lord_original` / `purpose` / `acceptance_criteria` fields.
```

**影響評価**: HIGH。`shogun_to_karo.yaml` は 2026-04-25 段階で 3267 行・190KB に肥大化済 (memory/note_neta.md L351)。足軽が purpose validation のために YAML 全文 Read すると 2-3万 token 消費・OOM リスク。API なら 1cmd 単発の json で 1KB 以下。

---

## HIGH (6件)

### H001 — `instructions/ashigaru.md` の workflow ステップが YAML 直 read/write 前提

**file:line**:
- `L41`: `target: "queue/tasks/ashigaru{N}.yaml"` (step: read_yaml)
- `L84`: `method: "bash scripts/inbox_write.sh"` (step: inbox_write)
- `L89`: `target: "queue/inbox/ashigaru{N}.yaml"` (step: check_inbox)
- `L107`: `task: "queue/tasks/ashigaru{N}.yaml"` (files セクション)
- `L168`: `queue/tasks/ashigaru{YOUR_NUMBER}.yaml    ← Read only this` (Self-Identification)

**旧ルール引用**: workflow YAML front matter が API ではなく直 path を primary 経路として明記。

**推奨改訂案**: workflow セクションに **dual-path 注釈** を追加。例:
```yaml
- step: 2
  action: read_yaml
  target: queue/tasks/ashigaru{N}.yaml
  api_alternative: "curl /api/task_list?agent=ashigaru{N}&limit=5"
  note: "Self-recovery (Session Start / /clear) は YAML 直読み許可 (CLAUDE.md L116)。タスク中の他エージェント状態確認は API 経由。"
```

**影響評価**: HIGH。`step: 9 inbox_write` の `method: "bash scripts/inbox_write.sh"` が primary として機械可読 YAML に書かれており、SDK/codegen が API 経路を生成しない。

---

### H002 — `instructions/gunshi.md` も同様の YAML primary 記述

**file:line**:
- `L41`: `target: queue/tasks/gunshi.yaml` (read_yaml)
- `L66`: `method: "bash scripts/inbox_write.sh"` (inbox_write)
- `L70`: `target: queue/inbox/gunshi.yaml` (check_inbox)
- `L80-82`: `files: task: queue/tasks/gunshi.yaml ... inbox: queue/inbox/gunshi.yaml`
- `L228-231`: `queue/tasks/gunshi.yaml ← Read only this` 等

**旧ルール引用**: ashigaru と同形式。

**推奨改訂案**: ashigaru と同じく api_alternative 注記を追加。`Report Notification Protocol (API 推奨・cmd_1494)` セクション (L362) は既に API 推奨済だが workflow YAML 上部と矛盾。

**影響評価**: HIGH。

---

### H003 — `shared_context/agent_common.md` §6 (/clear Recovery) で inbox を YAML 直読み

**file:line**: `shared_context/agent_common.md:74`

**旧ルール引用**:
> 4. `queue/inbox/{self}.yaml` → 未読メッセージを処理

**推奨改訂案**:
```diff
- 4. `queue/inbox/{self}.yaml` → 未読メッセージを処理
+ 4. `GET /api/inbox_messages?agent={self}&unread=1&limit=20` → 未読メッセージを処理
+    (障害時 fallback: `queue/inbox/{self}.yaml` 直読み)
+    処理後 `POST /api/inbox_mark_read` で既読化必須 (cmd_1495)
```

**影響評価**: HIGH。Session Start hook (本セッション冒頭) では「Step 0: SSE Monitor + GET /api/inbox_messages?unread=1 で catch-up」を要求している一方、agent_common.md は YAML を指す。CLAUDE.md L143「inbox Processing (cmd_1495)」では API 経路が確定済。共通骨子と最新ルールが乖離。

---

### H004 — `shared_context/agent_common.md` §5 (Compaction Recovery) で task YAML を直 Read

**file:line**: `shared_context/agent_common.md:67`

**旧ルール引用**:
> 2. 自分の task YAML を Read → `assigned` なら作業再開

**推奨改訂案**: H003 と同様に api_alternative 注記。CLAUDE.md L113-117 で「自分の状態回復は YAML 直読み継続」とポリシー明記されているため、ここでは "self-recovery 用途" であることを明示すれば maintain 可能。

**影響評価**: MEDIUM-HIGH。CLAUDE.md ポリシーと共通骨子が同じ allowance を別文言で言うため運用混乱の温床。

---

### H005 — `shared_context/procedures/document_design.md:9` が `queue/shogun_to_karo.yaml` 直読みを要求

**file:line**: `shared_context/procedures/document_design.md:9`

**旧ルール引用**:
> 1. `queue/shogun_to_karo.yaml` でparent_cmdの全commandを必ず読め（要約ではなく原文）

**推奨改訂案**:
```diff
- 1. `queue/shogun_to_karo.yaml` でparent_cmdの全commandを必ず読め
+ 1. `curl /api/cmd_detail?id=<parent_cmd>` で `lord_original` / `purpose` / `acceptance_criteria` を取得・原文読み (要約ではなく原文)
```

**影響評価**: HIGH。C002 と同根。190KB YAML を全 Read する手順は context 浪費の主因。

---

### H007 — `shared_context/procedures/*.md` の手順書群が `bash scripts/inbox_write.sh` を primary 例示

**file:line**:
- `shared_context/procedures/stt_pipeline.md:94`
- `shared_context/procedures/youtube_upload.md:39`
- `shared_context/procedures/manga_panel_gen.md:71`
- `shared_context/procedures/clip_concat.md:70`
- `shared_context/procedures/panel_review_html.md:83`
- (他 30 ファイル前後・grep ヒット 36 ファイルから API 言及済 2 ファイル除外)

**旧ルール引用** (代表):
```bash
bash scripts/inbox_write.sh karo \
  "..." report_received ashigaru{N}
```

**推奨改訂案**: 各手順書末尾の「家老通知」セクションを `curl -s -X POST -H 'Content-Type: application/json' -d '{"to":"karo","from":"ashigaru{N}","type":"report_received","message":"..."}' http://192.168.2.4:8770/api/inbox_write` に置換。bash 直叩きは fallback 表記に格下げ。

**影響評価**: HIGH。procedures は足軽が日次タスクで参照する手順書で、ここが旧経路 primary だと API 化が浸透しない。cmd_1673a (instructions 書き換え) の follow-up に procedures 一括置換 cmd を含めるべき。

---

### H006 — `instructions/karo.md:213` の "inbox nudge を待つ" 文言が watcher 旧経路依存

**file:line**: `instructions/karo.md:213`

**旧ルール引用**:
> foreground sleep / capture-pane / polling 禁止 (F004): dispatch 後は idle で inbox nudge を待つ

**推奨改訂案**:
```diff
- dispatch 後は idle で inbox nudge を待つ
+ dispatch 後は idle で SSE Monitor (Step 0) または inbox_watcher (legacy) 経由の通知を待つ
```

**影響評価**: HIGH。現行 cmd_1648/1649 では SSE Monitor 経路が主・inbox_watcher は補完 (Session Start hook の文言通り)。家老の文言を update せねば SSE への移行判断 (Phase 3) で混乱。

---

## MEDIUM (5件)

### M001 — CLAUDE.md `/clear Recovery` Step 4/4.5 が YAML 直読みのまま

**file:line**: `CLAUDE.md:94-95`

**旧ルール引用**:
> Step 4: Read queue/tasks/{your_id}.yaml → 末尾のstatus:assignedタスクを探す。
> Step 4.5: Read queue/inbox/{your_id}.yaml → unread messages があれば処理

**推奨改訂案**: CLAUDE.md L113-117 で既に「self-recovery 用途は YAML 直読み」と allowance 明記。ただし Step 4.5 の `queue/inbox/*.yaml` は cmd_1495 後 SQLite primary に移行しており、API 経由が正規。
```diff
+ Step 4.5: Read queue/inbox/{your_id}.yaml (or `curl /api/inbox_messages?agent=...&unread=1`) → unread messages があれば処理
```

**影響評価**: MEDIUM。Step 0 (SSE) で同等処理が済むため二重化される懸念。

---

### M002 — `scripts/precompact_hook.sh` が `shogun_to_karo.yaml` を直 yaml.safe_load

**file:line**: `scripts/precompact_hook.sh:88-89, 200, 238, 259`

**旧ルール引用**:
```bash
# ─── Active cmds from shogun_to_karo.yaml (shogun/karo) ───
CMD_QUEUE="$SCRIPT_DIR/queue/shogun_to_karo.yaml"
```

**推奨改訂案**: hook は context-tight & 高頻度実行のため API 起動コスト懸念あるが、`curl --max-time 2 /api/cmd_list?status=in_progress&slim=1` で代替可能。timeout=5 (settings.json) で十分間に合う。

**影響評価**: MEDIUM。precompact 時の active_cmds 表示が dashboard.md と不整合になる可能性 (YAML 編集 lag)。

---

### M003 — `shared_context/procedures/dashboard_api_usage.md:103` が「段階的 curl 経由へ」と曖昧

**file:line**: `shared_context/procedures/dashboard_api_usage.md:103`

**旧ルール引用**:
> 既存スクリプトの `yaml.safe_load(queue/shogun_to_karo.yaml)` は **段階的に curl 経由へ**置換

**推奨改訂案**: 「段階的」が無期限。期限と移行担当 (家老 or 軍師 cmd 起票) を明記:
```diff
- 既存スクリプトの `yaml.safe_load(queue/shogun_to_karo.yaml)` は **段階的に curl 経由へ**置換
+ 既存スクリプト (precompact_hook.sh / cron 配下 / nightly_audit.sh 等) の yaml.safe_load 直読みは 2026-Q3 までに curl 経由へ全置換。残務は `cmd_1673` follow-up にて家老が起票。
```

**影響評価**: MEDIUM。「段階移行」が温存され、dual-path 整合崩壊事故の温床に。

---

### M004 — `instructions/karo.md:178-198` API ルール記述は完備だが Tier 表との対比が片寄り

**file:line**: `instructions/karo.md:178-198`

**現状**: 「家老が以下をすると殿激怒」リスト (L195-198) で `Read queue/tasks/*` `cat queue/reports/*` 等を禁止。同等の禁止リストが ashigaru.md / gunshi.md には**ない**。役職ごとに API 強制度合いがばらつく。

**推奨改訂案**: ashigaru.md / gunshi.md にも「これをすると殿激怒」リストの role-specific 版を追加 (足軽は self-task の自己回復用 YAML Read は OK・他エージェント状態 cat は NG 等の境界線を明記)。

**影響評価**: MEDIUM。

---

### M005 — `shared_context/task_yaml_schema.md:194,197` の CHK4/CHK7 が YAML 直編集前提

**file:line**: `shared_context/task_yaml_schema.md:194,197`

**旧ルール引用**:
- CHK4: `shogun_to_karo.yaml 将軍編集` (新規 cmd 起票に lord_original 欄必須)
- CHK7: `queue/tasks/{ashigaru*,gunshi}.yaml 編集` (新規 task_id に 9 必須フィールド欠落 BLOCK)

**推奨改訂案**: 起票が `POST /api/cmd_create` / `POST /api/task_create` に移行 (CLAUDE.md L114・karo.md L184)。CHK4/CHK7 は emergency fallback (API down 時の手書き YAML) のセーフティネットとして役割再定義し、その旨を明記。

**影響評価**: MEDIUM。

---

## LOW (4件)

### L001 — `instructions/ashigaru.md:208` / `gunshi.md:387` の例示順序が API 後・bash 先

**file:line**: 
- `instructions/ashigaru.md:208` (Report Notification Protocol)
- `instructions/gunshi.md:387` (同)

**旧ルール引用**: API curl サンプルの直後に「bash 直叩き (障害時フォールバックのみ)」サンプルが続く。fallback 明記済だが、視覚的に2サンプル並列で誤読リスク。

**推奨改訂案**: bash サンプルを `<details><summary>障害時 fallback (通常運用では使うな)</summary>...` で折りたたむ or 末尾に移動。

**影響評価**: LOW。

---

### L002 — `memory/feedback_shogun_to_karo_status_update.md` が YAML 直編集前提の運用

**file:line**: `memory/feedback_shogun_to_karo_status_update.md:7,13`

**旧ルール引用**:
> cmd完了時は必ずshogun_to_karo.yamlのstatusをdoneに更新せよ
> 2. shogun_to_karo.yamlの当該cmdのstatusをpending/in_progress → doneに更新

**推奨改訂案**: cmd 完了 status 更新は `POST /api/cmd_complete` (or `/api/cmd_status_change`) で SQLite + YAML dual-path 自動同期される (server.py L3120 周辺)。memory は historical record として残しつつ「現状: API 経由で自動同期・手動 YAML 編集不要」の追記を上部に。

**影響評価**: LOW (手動 YAML 編集しなければ事故にならない)。

---

### L003 — `memory/feedback_ntfy_per_cmd.md:10` が shogun_to_karo.yaml 自動更新前提

**file:line**: `memory/feedback_ntfy_per_cmd.md:10`

**旧ルール引用**:
> ntfy送信時にshogun_to_karo.yamlのstatus自動done更新を実装した

**推奨改訂案**: 実装は API 経由に移行済 (cmd_1494)。memory に「現在は API 経由で同期」追記。

**影響評価**: LOW。

---

### L005 — `instructions/shogun.md:178` の "write YAML → inbox_write" 表現が API 化前の流れを示唆

**file:line**: `instructions/shogun.md:178`

**旧ルール引用**:
> Lord: command → Shogun: write YAML → inbox_write → END TURN

**推奨改訂案**:
```diff
- Lord: command → Shogun: write YAML → inbox_write → END TURN
+ Lord: command → Shogun: POST /api/cmd_create (lord_original 必須) → END TURN  (家老通知は API が自動送信)
```

**影響評価**: LOW (将軍は本文中で `POST /api/cmd_create` を別所で記載済・Workflow 概要図のみ古い)。

---

### L004 — `memory/note_neta.md:351` が「shogun_to_karo.yaml 3267行・190KB肥大化」を記録

**file:line**: `memory/note_neta.md:351`

**旧ルール引用**:
> shogun_to_karo.yaml 3267行・190KB肥大化→cmd_rotate.sh作成を家老に委任

**推奨改訂案**: cmd_rotate.sh が作成されたか・現在の YAML サイズはいくらか家老が確認 (`wc -l queue/shogun_to_karo.yaml`)。SQLite primary 化後は YAML rotation 不要かもしれない。

**影響評価**: LOW (情報メモ・直接ルール違反なし)。

---

## 全体所見

1. **API 化は完成している** (cmd_1494 で SQLite primary・dual-path 自動同期確立)。問題は **ドキュメント/instructions の追従不足** であり、コード自体に旧ルール残骸はほぼない。
2. **最大ボトルネック**: `instructions/generated/` 配下が 2026-02 頃のスナップショットで停止。codex/copilot/kimi CLI を実用化する前に再生成 or 削除判断要。
3. **構造的改善案**:
   - `instructions/{role}.md` の workflow YAML front matter を **API primary** に書き換え (`api_alternative` ではなく `legacy_path`)
   - `shared_context/agent_common.md` §5/§6 の self-recovery 手順を「API で確認 → fallback YAML」順に
   - `instructions/generated/` を削除 or `.deprecated` リネーム (実害ファイルだが家老/殿判断要)
4. **follow-up cmd 推奨**:
   - **cmd_1673a**: instructions/{ashigaru,gunshi,shogun}.md の workflow YAML front matter を API primary に書き換え
   - **cmd_1673b**: shared_context/agent_common.md §5/§6 を API primary に書き換え
   - **cmd_1673c**: instructions/generated/ の存続/削除を殿判断で確定 (codex/copilot/kimi CLI 利用予定の有無確認)
   - **cmd_1673d**: shared_context/procedures/document_design.md / task_yaml_schema.md / dashboard_api_usage.md の "段階移行" 文言に期限を入れる

---

## Sweep Coverage (AC#2 全 sweep 確認の透明化)

| 対象群 | sweep 方法 | 検査結果 |
|--------|-----------|----------|
| `CLAUDE.md` (1ファイル・394行) | 14パターン直接 grep + 手読み | finding: M001 / その他全項目 API 移行済 |
| `instructions/{shogun,karo,ashigaru,gunshi}.md` (4ファイル・約 80KB) | 各役割 × 14パターン grep | finding: C002 / H001 / H002 / H006 / shogun.md L178 (L005) |
| `instructions/git_safety.md` | grep | clean |
| `instructions/generated/*.md` (8 ファイル) | 全件 grep | finding: C001 (ディレクトリ全体・stale) |
| `instructions/{cli_specific,common,roles}/` | grep | clean (一部 roles/karo_role.md に旧表現残るが karo.md と内容重複) |
| `shared_context/agent_common.md` | 全文読み + grep | finding: H003 / H004 |
| `shared_context/procedures/*.md` (57 ファイル) | grep `inbox_write\.sh\|queue/tasks\|queue/inbox\|yaml.safe_load.*shogun_to_karo` | hit 36 ファイル → finding: H005 / H007 (旧 inbox_write.sh primary 例示が広範囲) / M003 (dashboard_api_usage.md "段階移行") |
| `shared_context/{task_yaml_schema,qc_template,cron_inventory}.md` | grep | finding: M005 (task_yaml_schema.md) |
| `memory/MEMORY.md` + `memory/feedback_*.md` (約 25 ファイル) | grep `shogun_to_karo\|inbox_write\.sh` | finding: L002 / L003 / L004 (historical 記述・直接ルール違反なし) |
| `.claude/settings.json` | hooks セクション全件目視 | clean (PreToolUse/Stop/SessionStart hook が pretool_check.sh / stop_hook_inbox.sh / sessionstart_hook.sh を呼出・hook script 側で API パターン保護) |
| `.claude/settings.local.json` | 全文目視 | clean (730 bytes・personal allowlist のみ) |
| `scripts/sessionstart_hook.sh` | 全文目視 (60行+α) | clean (tmux self-id + GEMINI_API_KEY check のみ) |
| `scripts/stop_hook_inbox.sh` | 全文目視 (50行サンプル) | clean (inbox 既読チェックは inotify 経路だが API primary 移行は別 cmd・1648/1649) |
| `scripts/precompact_hook.sh` | grep | finding: M002 (yaml.safe_load 直読み 4箇所) |
| `scripts/pretool_check.sh` (39KB) | grep `api/inbox_write\|api/cmd_create\|api/task_create\|api/cmd_cancel\|api/` | clean (CHK12/CHK13/CHK14 が API 経路を保護) |
| `scripts/nightly_audit.sh` | grep | clean (L40-43 で curl /api/inbox_write primary・bash fallback) |
| `scripts/cron_health_check.sh` | grep | clean (旧パターン非該当) |

**Coverage 比率**: 対象 7群・調査ファイル数 約 100超・finding 19件 (CRITICAL 2 + HIGH 7 + MEDIUM 5 + LOW 5)。

---

## 検証手順 (家老向け)

1. `wc -l queue/reports/2026-05-09_cmd_1673_pre_api_rules_audit.md` (目視: 17件 finding)
2. `grep -c "^### " queue/reports/2026-05-09_cmd_1673_pre_api_rules_audit.md` (severity 別 finding 数 = CRITICAL2+HIGH6+MEDIUM5+LOW4 = 17)
3. 各 finding の `file:line` を `sed -n 'NUMBERp' <path>` で実引用と照合
4. read-only 遵守確認: `git status` で `instructions/` `shared_context/` `memory/` `scripts/` `.claude/` 配下に修正なし (本報告書のみ追加)

