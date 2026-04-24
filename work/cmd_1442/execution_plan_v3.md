# cmd_1442 execution_plan_v3.md (殿号令「進軍せよ」採用版)

全12ハーネス採用確定。殿追加指示 5 件 (H2拡張 / H3+H8 登録自動化 / H10改 H1 統合 / H11 レビュー方式 / H12 透明性) 全反映。cmd_1443 起票テンプレ付き。

- **作成**: 2026-04-24 / gunshi (subtask_1442_execplan_v3)
- **前身**: work/cmd_1442/harness_proposal.md (commit 95895ce)
- **採用根拠**: 殿号令 18:39 + 採用履歴 18:23〜18:38 (dashboard.md L40-51 より確定)
- **次工程**: 家老が本 md を元に cmd_1443 を shogun_to_karo.yaml に起票 → Wave A/B/C 順で足軽分散発令

---

## 0. v2 → v3 改訂差分 (必読)

| # | 差分 | v2 (harness_proposal.md) | v3 (本書) | 根拠 (dashboard.md L40-51) |
|---|------|--------------------------|----------|--------------------------|
| Δ1 | H1 に H10改 統合 | H1 = 完了後 curl・H10 = 独立 advisor 呼出率 | **H1 吸収型**: 完了後 curl + `scripts/done_gate.sh` + advisor 呼出率メトリクス・即時阻止型 hook (追加1-2h) | L47「H10改 ✅採用(18:33) H1統合 即時阻止型」 |
| Δ2 | H2 対象拡張 | dashboard.md 残骸のみ | **+MCPダッシュボード (http://192.168.2.7:8770/) 残骸もクリア対象** | L41「H2 ✅採用+拡張(18:24) +MCPダッシュボード残骸」 |
| Δ3 | H3+H8 機能拡張 | mem-search hit 結果の cmd 内コメント挿入のみ | **+4系統 (cmem obs / MCP entity / feedback_*.md / dashboard archive) に自動 add_observations** | L42「H3+H8 ✅採用+登録自動化(18:25) +4系統自動add_observations」 |
| Δ4 | H11 実装形式 | 殿激怒→memory 自動追加 (曖昧) | **`.claude/commands/lord-angry.md` slash 実装・slash 実行時に下書き→将軍レビュー→commit の半自動** | L48「H11 ✅採用(18:34) レビュー方式」 |
| Δ5 | H12 透明性拡充 | cron インベントリ md のみ | **各 cron に目的/所管/停止影響明記 + nightly_audit 健全性 + quarterly review 義務化** | L49「H12 ✅採用(18:36) 透明性必須」 |
| Δ6 | H6 除外確定 | 既存資産重複で格下げ保留 | **除外** (cmd_1443 対象外) | harness_proposal.md §2 で既決 |

---

## 1. 採用12ハーネス (最終仕様・実装 10 subtask)

H10 は H1 に統合・H3+H8 は 1 subtask にバンドル → 実装 subtask 数 = **10件**。

### 採用リスト

| ID | ハーネス名 | 対応 cluster | Wave | 実装主体 |
|----|-----------|-------------|------|----------|
| H1 (+H10改) | 完了後 curl 自動 + `scripts/done_gate.sh` (即時阻止型) + advisor 呼出率メトリクス | (a) | **A** | shell hook + PostToolUse |
| H2 | dashboard 残骸 lifecycle hook (**+ MCP web UI 残骸対象**) | (b) | **A** | shell cron + 既存 H16 nightly_audit 拡張 |
| H3+H8 | cmd 起票時 mem-search 自動 + hit 0 警告 + **4系統自動 add_observations** | (e) | **A** | PreToolUse hook + cmem_search.sh 拡張 |
| H4 | silent fail log watcher → ntfy | (c) | **A** | shell daemon (inbox_watcher と同パターン) |
| H7 | hotfix 3回→skill 提案 cron | (d) | **A** | weekly cron + claude-mem 集計 |
| H5 | cmd YAML lint (PreToolUse) | (b)(d) | **B** | posttool_yaml_check.sh 拡張 (yq) |
| H9 | Phase間殿ゲート必須化 | メタ | **B** | shogun_to_karo.yaml schema 拡張 + ntfy 強制 |
| H11 | `.claude/commands/lord-angry.md` slash (レビュー方式) | 全般 | **B** | slash command 新設 |
| H12 | `shared_context/cron_inventory.md` (透明性) + quarterly review | メタ | **B** | md 新設 + nightly_audit 健全性 |
| H13 | 月次 feedback レビュー cron | (e) | **C** | monthly cron + dashboard連携 |
| ~~H6~~ | (除外) | — | — | 既存 feedback_llm_selection_rule.md + execution_plan_v2 モデル指定列で既充足 |
| ~~H10~~ | (H1 に統合・独立 subtask なし) | — | — | done_gate.sh 内で advisor 呼出率を同時計測 |

---

## 2. Wave 分配 (確定)

### Wave A (今夜〜今週・並列発令推奨・5 subtask)

| subtask_id (v3命名) | ハーネス | 担当候補 | 所要時間 | 依存 | 並列可否 | advisor | git push |
|--------------------|---------|---------|---------|------|---------|---------|---------|
| **cmd_1443_p01** | H1 (+H10改) | 足軽3号 | 3-5h (追加 1-2h含) | なし | 並列可 | 実装前後必須 | 家老 |
| **cmd_1443_p02** | H2 拡張 | 足軽1号 | 3h | なし | 並列可 | 実装前後必須 | 家老 |
| **cmd_1443_p03** | H3+H8 拡張 | 足軽7号 | 2-3h | なし | 並列可 | 実装前後必須 | 家老 |
| **cmd_1443_p04** | H4 | 足軽3号 (p01 後) or 並列別足軽 | 2-3h | H7 ntfy wrapper (既存) | 並列可 | 実装前後必須 | 家老 |
| **cmd_1443_p05** | H7 | 足軽2号 | 2-3h | なし | 並列可 | 実装前後必須 | 家老 |

### Wave B (今週後半・並列発令・4 subtask)

| subtask_id | ハーネス | 担当候補 | 所要時間 | 依存 | 並列可否 | advisor | git push |
|-----------|---------|---------|---------|------|---------|---------|---------|
| **cmd_1443_p06** | H5 | 足軽4号 | 30min | p01 完了後 (pretool_check 整合) | 並列可 | 実装前のみ | 家老 |
| **cmd_1443_p07** | H9 | 足軽4号 | 1h | なし | 並列可 (shogun_to_karo.yaml 編集のみ) | 実装前後必須 | 家老 |
| **cmd_1443_p08** | H11 slash | 足軽5号 | 1h | なし | 並列可 (slash command 新規) | 実装前後必須 | 家老 |
| **cmd_1443_p09** | H12 cron inventory | 足軽7号 (p03 後) or 並列別足軽 | 1h | なし | 並列可 | 実装前後必須 | 家老 |

### Wave C (2週内・1 subtask)

| subtask_id | ハーネス | 担当候補 | 所要時間 | 依存 | 並列可否 | advisor | git push |
|-----------|---------|---------|---------|------|---------|---------|---------|
| **cmd_1443_p10** | H13 月次 feedback レビュー cron | 足軽5号 | 30min | Wave B 完了後 (cron系統一整理後) | 並列可 | 実装前のみ | 家老 |

**合計**: 10 subtask / 総工数 ~16-20h / 足軽並列最大5人 (1号/2号/3号/4号/5号+7号)

---

## 3. 殿追加指示 5件 反映仕様

### Δ1: H1 吸収型 (H10改 統合・即時阻止型)

**実装**: `scripts/done_gate.sh` 新設 (shell) + PostToolUse hook 登録

```bash
#!/bin/bash
# scripts/done_gate.sh - 完了後 curl/ブラウザ verify + advisor 呼出率計測
# 使い方: PostToolUse hook から subtask 完了宣言時に呼ばれる

TASK_YAML="$1"       # 完了 subtask の YAML path
VERIFY_CMD=$(yq '.verify' "$TASK_YAML")  # タスク定義の verify コマンド抽出
ADVISOR_LOG=logs/advisor_calls.log  # H10 統合

# 1. advisor 呼出率検証
ADVISOR_COUNT=$(grep -c "$TASK_ID" "$ADVISOR_LOG")
[ "$ADVISOR_COUNT" -lt 2 ] && {
  echo "BLOCK: advisor 呼出 $ADVISOR_COUNT 回 (必須 2 回)" >&2
  exit 1
}

# 2. verify コマンド実行 → 失敗なら done 宣言を阻止
bash -c "$VERIFY_CMD" || {
  echo "BLOCK: verify 失敗" >&2
  exit 1
}
```

**既存資産活用**: shogun-screenshot skill + posttool_cmd_check.sh を呼出。

### Δ2: H2 拡張 (MCP ダッシュボード残骸対象)

**実装**: `scripts/dashboard_lifecycle.sh` 新設
- **対象1**: `dashboard.md` 🚨要対応 セクション (既存)
- **対象2 (新規)**: MCP ダッシュボード (`http://192.168.2.7:8770/`) の残骸検出 → curl /api/tasks で status=done 扱いの項目を抽出 → ntfy_send で家老に削除依頼通知
- **実行**: 既存 H16 nightly_audit に統合 (時刻 2:02 で dashboard + MCP 同時 audit)

### Δ3: H3+H8 拡張 (4系統自動 add_observations)

**実装**: `scripts/cmd_intake_hook.sh` 新設 (shogun_to_karo.yaml PreToolUse)

cmd 起票時に以下を自動実行:
1. cmd 本文からキーワード抽出 (`awk` で `[a-zA-Z_]+` + 日本語名詞)
2. `cmem_search.sh "$keyword"` 呼出
3. **4系統 add_observations (新規)**:
   - (i) **cmem obs** = claude-mem API `/api/observations` へ POST (cmd_id + キーワード + hit 結果)
   - (ii) **MCP entity** = `mcp__memory__add_observations` で `rule_yaml_first` entity に cmd 記録追記
   - (iii) **feedback_*.md** = 殿激怒キーワードを正規表現検出・hit 時 lord-angry slash (H11) 呼出
   - (iv) **dashboard archive** = dashboard_archive/ に cmd 追加行を自動 append
4. hit 0 件時: cmd 内コメントに `⚠️ mem-search hit=0・新規実装の可能性` 警告注入

### Δ4: H11 レビュー方式 (`.claude/commands/lord-angry.md`)

**実装**: slash command 新設 `/lord-angry <発言抜粋>`

動作:
1. 殿激怒発言を引数受領
2. LLM 推論 (Sonnet) で以下を自動生成 (**下書き**):
   - `memory/feedback_{slug}.md` 草稿 (frontmatter 含む)
   - `memory/MEMORY.md` 追記候補 1 行
3. **レビュー方式**: slash 実行者 (将軍 or 家老) に草稿を表示・「承認 (y) / 修正 (e) / 破棄 (n)」選択肢表示
4. 承認時のみ commit・破棄時は no-op・修正時は vi 起動
5. auto-commit は不可 (F002 違反回避)

### Δ5: H12 透明性 (`shared_context/cron_inventory.md`)

**実装**: md 新設 + 各 cron entry に 3 フィールド必須:
- **目的**: 何をするか
- **所管**: 担当エージェント (家老/軍師/足軽N)
- **停止影響**: 停止時に何が壊れるか

**追加ハーネス**:
1. `scripts/cron_health_check.sh` 新設 (時間 cron・全 cron ログ末尾 tail → ERROR/FAIL grep → ntfy)
2. `shared_context/cron_inventory.md` に quarterly review 義務化 (四半期ごと軍師が棚卸し・死文化検知)
3. 既存 nightly_audit に cron_inventory.md ↔ 実 crontab 整合チェック追加

---

## 4. cmd_1443 起票テンプレ (家老向け・YAML block)

家老は以下のテンプレを `queue/shogun_to_karo.yaml` 末尾に追記し、cmd_1443 として発令する。

```yaml
- id: cmd_1443
  status: in_progress
  timestamp: "2026-04-24T18:45:00+09:00"
  priority: high
  purpose: |
    cmd_1442 採用12ハーネス (H6除外・H10=H1統合・H3+H8=1 subtask・実装10件) の足軽分散発令。
    殿号令「進軍せよ」18:39 を受理。仕組み改善 10 subtask で事故再発防止 + 運用効率向上を図る。
  acceptance_criteria:
    - "10 subtask 全完了 (Wave A=5 / B=4 / C=1)"
    - "軍師 QC 全 subtask PASS"
    - "殿追加指示 5件 (H2拡張/H3+H8 登録自動化/H10改H1統合/H11 レビュー/H12 透明性) 反映確認"
    - "git commit + push 家老主導"
  command: |
    軍師 execution_plan_v3.md (commit 未commit・本cmd発令と同時 commit) を参照し、以下 10 subtask を順次発令せよ:

    【Wave A (5件・今夜〜今週・並列発令可)】
    - cmd_1443_p01: H1 (+H10改) 完了後curl + done_gate.sh + advisor 呼出率 → 足軽3号・3-5h
    - cmd_1443_p02: H2 拡張 dashboard + MCPダッシュボード残骸 → 足軽1号・3h
    - cmd_1443_p03: H3+H8 拡張 mem-search + 4系統自動 add_observations → 足軽7号・2-3h
    - cmd_1443_p04: H4 silent fail log watcher → 足軽3号 (p01後) or 別足軽並列・2-3h
    - cmd_1443_p05: H7 hotfix 3回→skill 提案 cron → 足軽2号・2-3h

    【Wave B (4件・今週後半・並列発令可)】
    - cmd_1443_p06: H5 cmd YAML lint (pretool/posttool) → 足軽4号・30min (p01後)
    - cmd_1443_p07: H9 Phase間殿ゲート → 足軽4号・1h
    - cmd_1443_p08: H11 .claude/commands/lord-angry.md slash (レビュー方式) → 足軽5号・1h
    - cmd_1443_p09: H12 shared_context/cron_inventory.md (透明性) + cron_health_check.sh → 足軽7号 (p03後) or 別並列・1h

    【Wave C (1件・2週内)】
    - cmd_1443_p10: H13 月次 feedback レビュー cron → 足軽5号・30min (Wave B完了後)

    各 subtask は:
    - target_path 必須 (家老 5点セット遵守・pretool_check 事故防止)
    - advisor 呼出 2回 (実装前+完了前) 必須
    - git push は家老が cmd 完了時に一括
    - テスト手順を steps に明記 (curl 動作確認等)
    - 新規 .py 禁止 (shell/hook/既存 skill 拡張のみ)
    - 動画系除外 (cmd_1441 方針継続)

    軍師 QC (10 subtask 分) は各 subtask 完了時点で都度実施。Wave A/B/C 完了時点で全体統括 QC 1 回。
  notes:
    - "発令順序は Wave A → Wave B → Wave C。Wave 内は並列可"
    - "cmd_1443_p03 (H3+H8) と cmd_1443_p09 (H12) は足軽7号担当ゆえ時系列分離推奨"
    - "cmd_1443_p04 (H4) は cmd_1443_p07 H9 ntfy 整備と独立 (既存 ntfy.sh でも可)"
    - "4系統 add_observations (H3+H8) の 4系統 = cmem obs / MCP entity / feedback_*.md / dashboard archive・順序は docstring に明示"
    - "H10 は H1 に統合・独立 subtask なし (advisor 呼出率ロジックは done_gate.sh 内)"
    - "H6 は除外 (既存 feedback_llm_selection_rule.md + execution_plan_v2 モデル指定列で既充足)"
```

---

## 5. 各 subtask YAML テンプレ雛形 (家老向け・1件サンプル)

家老は以下の形式で各 subtask YAML を `queue/tasks/{ashigaru_N}.yaml` 末尾に追記する。

```yaml
# cmd_1443_p01 H1 (+H10改) サンプル
- task_id: cmd_1443_p01
  parent_cmd: cmd_1443
  bloom_level: L5
  status: assigned
  target_path: /home/murakami/multi-agent-shogun/scripts/done_gate.sh
  timestamp: "2026-04-24T18:50:00+09:00"
  description: "H1 完了後curl自動 + scripts/done_gate.sh (即時阻止型) + advisor 呼出率メトリクス統合 (H10改吸収)"
  steps: |
    advisor()(前) →
    Step1: scripts/done_gate.sh 新設 (shell・yq 依存)
    Step2: PostToolUse hook 登録 (.claude/settings.json)
    Step3: task YAML に verify: 欄追加の schema 文書化 (shared_context/task_yaml_schema.md 更新)
    Step4: advisor 呼出ログ logs/advisor_calls.log 自動収集 (advisor_proxy.py 拡張)
    Step5: 動作確認 (サンプル task で verify 失敗 → done 阻止動作確認)
    advisor()(完了前) →
    Step6: git add scripts/done_gate.sh shared_context/task_yaml_schema.md + commit
    Step7: inbox_write gunshi QC依頼
  acceptance_criteria:
    - "scripts/done_gate.sh 作成・PostToolUse hook 動作確認"
    - "task YAML に verify: 欄追加できる schema 文書化"
    - "advisor 呼出 < 2 回で done 阻止確認"
    - "verify コマンド失敗で done 阻止確認"
    - "既存 subtask の done 動作を壊していない (regression 確認)"
    - "git commit 済み"
  notes:
    - "殿追加指示: H10 改 H1 統合・即時阻止型 (dashboard L47)"
    - "新規 .py 禁止・shell のみ"
    - "advisor() 2回呼出必須"
    - "**後方互換**: task YAML に verify: 欄が存在しない場合は従来通り done 許可 (done_gate.sh は verify 欄のみ検査・欄不在 = skip)。既存全 subtask の regression 回避必須"
    - "完了後: bash scripts/inbox_write.sh gunshi '足軽3号、cmd_1443_p01完了。' report_received ashigaru3"
```

他 9 subtask も同形式で家老が起票する (省略・対応するハーネス名・target_path・steps・acceptance に合わせて調整)。

---

## 6. 同一ファイル編集の直列化 (v3 更新)

複数 subtask が同一ファイル編集対象 → 家老が順次発令 or batch 化。

| ファイル | 編集 subtask | 推奨順序 |
|---------|-------------|---------|
| `.claude/settings.json` (hooks) | p01 (PostToolUse) + p03 (PreToolUse) + p04 (daemon?) + p06 (PostToolUse lint) | **p01→p03→p04→p06** (PostToolUse/PreToolUse 別 keys ゆえ衝突少) |
| `scripts/cmem_search.sh` | p03 (4系統 add_obs) | 単独 |
| `shogun_to_karo.yaml` schema | p07 (H9 lord_preconditions 欄) | 単独 |
| `shared_context/task_yaml_schema.md` | p01 (verify:) + p07 (lord_preconditions:) | **p01 → p07** |
| `shared_context/cron_inventory.md` | p09 (H12) + p10 (H13) | **p09 → p10** |
| 既存 cron 追加 | p05 (hotfix) + p09 (cron_health) + p10 (月次 feedback) | **p05 → p09 → p10** |

---

## 7. QC観点 (軍師用・各 subtask 完了時)

各 subtask の QC でチェックする項目:
1. **target_path 明記**: 家老 5点セット遵守 (pretool_check 事故防止)
2. **advisor 呼出 2回**: advisor_calls.log で自動検証 (p01 done_gate.sh 以降は機械検証可)
3. **verify コマンド実行ログ**: 各 subtask の動作確認 (実ファイル curl 等)
4. **殿追加指示整合**: Δ1-Δ5 の仕様が反映されているか実装コード目視
5. **regression**: 既存機能 (inbox_write / ntfy / cron 等) を壊していないか

全体統括 QC (Wave A/B/C 完了時):
- 10 subtask 全 PASS
- 期待効果メトリクス測定 (1週後):
  - 殿激怒事象発生数
  - hotfix 独立発明数
  - mem-search 活用率
  - dashboard 残骸滞留時間
  - silent fail 発覚遅延
  - advisor 呼出履行率

---

## 8. 中断耐性 (advisor 推奨)

本 execution_plan_v3.md は section 単位で commit 可能な構成。途中中断時は:
- 既に書いた section まで commit → 残 section は別 subtask で継続
- 家老未発令 state で殿方針変更が入っても差分更新で対応可

---

## 9. 北極星アラインメント (v3)

- **短期寄与**: Wave A 5件で殿激怒減少 (H1) + 既存資産活用 (H3+H8 4系統自動) + silent fail 即検知 (H4)
- **中長期寄与**: Wave B+C で運用全体の健全性向上 (H12 cron 透明性 + H13 feedback 健全性)
- **リスク**: 
  - Wave A 5件並列は足軽5名同時稼働・各 advisor 呼出の順序性に注意 (H10改メトリクスが H1 実装完了後から有効)
  - H11 slash の lord-angry コマンドは殿の発言に能動反応する設計ゆえ、将軍レビュー必須を厳守
  - cron 追加系 (H7/H12/H13) が crontab ノイズ化しないよう H12 透明性 md で一元管理必須

---

## 10. 次工程フロー

1. **本 md commit** (軍師・本 subtask 完了): `git add -f work/cmd_1442/execution_plan_v3.md && git commit`
2. **家老 cmd_1443 起票** (本 md §4 テンプレを shogun_to_karo.yaml 末尾に追記 + status:in_progress)
3. **Wave A 並列発令** (家老が足軽1-3-5-7号 + 2号 に subtask YAML 発令 + inbox_write)
4. **足軽実装 → 軍師 QC** (各 subtask 完了毎)
5. **Wave B → C 順次発令** (Wave A 完了後)
6. **全体統括 QC** (Wave A/B/C 完了時・メトリクス測定 1週後)

---

以上、execution_plan_v3.md 完成。殿追加指示 5件全反映・12ハーネス採用 (実装 10 subtask) ・cmd_1443 起票テンプレ付。家老は本書を元に進軍されたし。
