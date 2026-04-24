# H_post_step_completion_detector 設計 doc (L5・設計のみ・実装は別 cmd)

**cmd**: cmd_1449 領域 E / **subtask_id**: subtask_1449_e
**起草**: 軍師 (gunshi) / **起草日**: 2026-04-24
**提案 trigger**: cmd_1446 qc_1446_resume MAJOR finding F1 (家老 QC 発出タイミング尚早)

---

## 結論 (先置き)

**新ハーネスを新設するのではなく、既存 H1 `scripts/done_gate.sh` を拡張する**。

- task YAML の `verify:` 欄と同位置に `post_steps:` 欄を新設 (list of marker file paths)
- `done_gate.sh` に「全 marker 存在確認」を 1 段追加 (≤20 行 diff)
- `task_yaml_schema.md §2` に post_steps spec を追加
- 新 `.sh` ファイルは作らない (advisor binary 指摘を反映)

家老直実行タスクも gunshi.yaml / karo.yaml に task_id + verify + post_steps を書けば H1 が発火するため trigger 点差は schema で吸収可能。

---

## (a) 背景と目的

### 事案 (cmd_1446 qc_1446_resume MAJOR F1)
家老は 2026-04-24 20:39 に `git filter-repo` + `git gc --aggressive --prune=now` + `git remote add origin` + `post_size.log 書出し` + `HEAD verify` + `blob check` の一本 shell script を起動した。20:51 に `push.log` が生成され、12 分後の 21:03 に家老は軍師へ **QC 発出**。しかし同時刻時点で `git gc --aggressive` (PID 1738388) は継続中で、`post_size.log` は未生成だった。

軍師は BLOCKED_WAITING_FOR_GC 判定で返却し、家老は 1 分後 (21:09 gc 完了直後) に再 QC 依頼を発出。最終的に PASS 締結したが、**「push 成功 = cmd 完了」と誤認する規律問題** が根底にあった。

### 正直な根本原因分析
- **First-order cause**: 家老の inline shell script で「起動 = 完了」と誤認
- **True fix**: bash の foreground 同期実行 or `wait` の徹底
- **本ハーネスの役割**: **defense in depth** であり root cause fix ではない

### 目的 (狭く定義)
家老が足軽 or 軍師に QC 依頼を発出する前、および足軽/軍師が自己 status:done を宣言する前に、「**当該 task YAML で宣言された全 post-step marker file が物理存在すること**」を機械的に強制する。marker file が 1 件でも欠落していれば BLOCK する。

### 非目的 (スコープ外)
- ❌ Step 間の自動進行 (auto-advance) — scope creep。inotify 常駐監視は別タスクでも良いが本ハーネスでは不要。
- ❌ Phase 間殿承認ゲート — H9 `phase_gate_checker.sh` の責務。重複しない。
- ❌ 実行中の process 監視 (lsof/ps) — marker 存在でのみ判定 (ファイル I/O 済 = 完了の proxy)。

### 前提条件 (prerequisite)
本ハーネスの完全な効果を得るには、**家老 self-task workflow の整備**が必要 (家老直実行 cmd を queue/tasks/karo.yaml に task として登録する運用変更)。現状、cmd_1446 のような家老直実行は task YAML が書かれず実行されるケースが多い。本設計はこの運用変更を前提とし、整備コスト (≈1h) を §(e) 工数見積に含める。運用変更抜きで本ハーネスを入れても足軽/軍師の自己 status:done 宣言時にしか発火せず、cmd_1446 型の直接防御にはならない。

---

## (b) 要件定義

### R1. Schema 拡張 (task YAML)
既存 `verify:` 欄と同位置に `post_steps:` 欄を追加:

```yaml
- task_id: <id>
  parent_cmd: <cmd>
  status: assigned
  verify:
    command: "bash scripts/verify_xxx.sh"
  verify_result: pass
  post_steps:
    - work/cmd_1446/post_size.log      # gc 完了 marker
    - work/cmd_1446/push.log           # push 完了 marker
    - work/cmd_1446/filter_repo.log    # filter-repo 完了 marker
```

- 各 entry は **絶対パス or REPO_DIR 相対パス** の marker file
- **marker の意味** = 「当該 step が完了したときに書かれるファイル」(既存の work/<cmd>/<step>.log をそのまま流用・新 namespace 不要)
- 欄が不在 (nil or empty list) → 既存 opt-in 原則に従い skip (後方互換)

### R2. Gate 発火 trigger (primary)
`done_gate.sh` が呼ばれる以下 2 箇所で全 marker 存在確認を行う:
1. **自己 status:done 宣言時** (足軽/軍師): 既存 PostToolUse hook で発火
2. **家老→軍師 QC-request inbox_write 時** (新 trigger): `scripts/inbox_write.sh` に pre-write hook を追加し、家老が自分の task YAML (queue/tasks/karo.yaml・以後仕様追加必要) に post_steps を書いた場合に発火

trigger (1) は既存機構再利用・trigger (2) は cmd_1446 事案の直接対策。

### R3. BLOCK semantics 継承
既存 done_gate.sh の exit code 仕様を継承:
- exit 0 = OK (全 marker 存在 or post_steps 欄不在)
- exit 2 = BLOCK (stderr に欠落 marker list 出力・対応手順も出力)

### R4. Marker file の判定基準 + 意味論契約
- **存在判定のみ** (`[[ -f ]]` 相当) — size/content は問わない
- 理由: content を問うと検証仕様ごとに gate が肥大化。content 検証は `verify.command` (既存 H1) の責務。marker は「step が走った痕跡」の proxy。

**【重要・contract】**: marker は **「step の完了コードが最後に書くファイル」に限る**。中間生成物 (tmp_pack_*, .partial, .tmp, スケルトンファイル等) を marker に指定してはならない。`post_size.log` のように post-step の **最終出力** こそ適格。

- cmd_1446 事案の学習: `tmp_pack_TjMMCG` は gc **進行中** に 21:06 時点で存在していたが step は未完了だった。素朴な existence 検査で tmp_pack を marker にすれば false positive PASS が発生し、gate が「事故箇所を移す」だけで防御にならない。
- 運用側 (marker 宣言者) の責務: marker 選定時に「この file の mtime == step 完了時刻」が成立するか confirm する。具体的には:
  - ✅ OK: `du -sh ... | tee post_size.log` のような **step 終了直後に sync 書き出すログ**
  - ❌ NG: `git pack-objects` が中間的に書き出す `tmp_pack_*` や `.tmp` 拡張子ファイル
  - ✅ OK: `cp --finished-marker` 系の明示終端マーカー、`.done` / `.complete` suffix
- schema ドキュメント (task_yaml_schema.md §2.3) に本 contract を明記し、task YAML レビュー時に家老/軍師がチェックする運用化。

### R5. 後方互換性
- `post_steps:` 欄なし task → skip (既存 verify 欄 opt-in と同じ)
- 既存全 task YAML は無変更で動作

### R6. エラーメッセージ仕様
BLOCK 時の stderr:
```
BLOCK: <task_id> post_steps 未完了 (N 件欠落)
欠落 marker:
  - work/cmd_1446/post_size.log
  - work/cmd_1446/gc_done.log
対応: post-step を実行完了させてから status:done / QC 依頼せよ
log: logs/done_gate.log
```

---

## (c) アーキテクチャ: H1 拡張 vs 新ハーネス binary 判定

### 3-way 再構成の註記 (AC audit trail)
task YAML `steps` 欄は元来「同期監視 / 非同期 callback / polling+inotify」の impl 3-way trade-off を指定していた。**advisor pre-check で判断を再構成**: この 3-way は architectural question ではなく implementation detail と判定し、**「H1 拡張 / 新 script / daemon」の architectural binary** に再構成した。
- 旧 3-way (sync/async/inotify) は **方式 A (H1 拡張) 採用下では同期 `[[ -f ]]` に収束** する (trigger 時チェックのみ・watching 不要)。方式 C (daemon) を採用した場合のみ inotify vs polling の impl 3-way が生きる。
- 根拠: cmd_1446 事案は「gate で止めるだけで十分」= trigger 時の one-shot 存在チェックで defense 成立。watching/auto-advance は scope creep で非目的。
- AC discipline: 本註記で reframe を audit 可能化。task YAML 記載と設計 doc 記載の乖離は意図的・advisor 反映。

### 検討 2 方式

#### 方式 A: H1 (done_gate.sh) 拡張 **← 推奨**
- `done_gate.sh` に 10-20 行追加 (post_steps 読取 + exists loop + BLOCK)
- schema は `verify:` と同列追加 (task_yaml_schema.md §2)
- trigger 点 = 既存 done_gate.sh 発火点 (PostToolUse + 新追加の inbox_write pre-hook)

**利**:
- 新ファイルなし・保守コスト最小
- 既存 BLOCK semantics・advisor 2 回ルール と統合的に動作
- opt-in 原則継承で後方互換性ゼロリスク
- H1 は既に「task 完了前の gate」として確立 → post_steps は「task 完了の一部」ゆえ責務整合

**害**:
- 家老直実行タスク用の task YAML 整備要 (queue/tasks/karo.yaml の spec 追加・家老-self task の運用ルール化)

#### 方式 B: 新ファイル `scripts/post_step_gate.sh`
- `done_gate.sh` と並列の新スクリプト
- `inbox_write.sh` に pre-hook で呼出

**利**:
- trigger 点を inbox_write に限定できる (関心分離)
- done_gate.sh を触らずに済む

**害**:
- 新ファイル + 新 log + 新 test の追加コスト
- H1 と H_post_step の実装重複 (YAML 読取ロジック・BLOCK 出力フォーマット)
- advisor binary 指摘「done_gate.sh が既に verify + schema 持つ・拡張で十分」に反する
- 軍師自身の cmd_1442 H6 棄却理由 (既存資産重複による新ファイル回避) と同じ論理で却下される

#### 方式 C: inotify 常駐監視 + 自動進行
- daemon として post_steps を watch・全 marker 揃ったら次 step 自動起動

**利**:
- 真の自動化 (人間が忘れない)

**害**:
- scope creep (設計 doc 範囲外・非目的に明記)
- daemon の lifecycle 管理 (systemd 必要)
- race condition 設計の複雑化
- F004 (polling loop) の境界判定が微妙 (inotifywait 自体は event-driven だが service 化すると待機 loop に近づく)
- cmd_1446 事案は「marker 生成前の QC 発出」ゆえ、gate で止めるだけで十分 (auto-advance は overkill)

### 判定: **方式 A (H1 拡張) 採用**

根拠:
1. AC 明示要件「新ハーネス正当化」を H1 拡張で回避できる = 最小介入
2. 責務整合: H1 = task 完了前 gate / H_post_step = task 完了の一部 = 同じ責務
3. cmd_1442 H6 棄却の precedent (既存資産重複は避ける) を自己適用
4. advisor 指摘「schema 吸収で trigger 点差を解消可能」に合致

### 却下理由の記録 (advisor 指摘の「rejected alternatives を skimp するな」反映)
方式 B 却下: 重複実装・cmd_1442 H6 棄却原則と矛盾
方式 C 却下: scope creep・非目的・F004 境界問題

---

## (d) 既存ハーネス (H9 / H1) との関係

| ハーネス | 粒度 | 判断主体 | trigger | 目的 |
|---------|------|---------|---------|------|
| **H9** phase_gate_checker.sh | Phase (粗粒度) | **殿 (人間)** | 家老の手動呼出 | Phase 間 OK/NG/修正 の人間判断ゲート |
| **H1** done_gate.sh (現行) | Task (中粒度) | **機械** | PostToolUse hook | verify pass + advisor 2回 の自動検証 |
| **H1** done_gate.sh **拡張後** | Task + post_steps (細粒度) | **機械** | PostToolUse + inbox_write pre-hook | + 全 post-step marker 存在確認 |

階層:
```
Phase 完了 → H9 殿判断ゲート (人間 OK/NG)
   └─ Wave 内 cmd 完了 → H1 done_gate (verify + advisor + post_steps)
         └─ task 内 step 完了 → post_steps marker (H1 の検査対象)
```

H9 と H1 の責務は完全に分離 (人間判断 vs 機械判断)。本拡張は H1 内部の検査項目追加であり、H9 との relations は変わらない。

### 既存 `verify:` との違い
- `verify:` = step 終了後に走らせる **command** (content 検証)
- `post_steps:` = step 終了時に残る **marker file** (存在検証)
- 例: `verify: "grep -q '3.5G' work/cmd_1446/post_size.log"` (content) / `post_steps: ["work/cmd_1446/post_size.log"]` (existence)
- 共存可能: post_steps で「走った痕跡」を確認し、verify で「結果の正しさ」を確認

---

## (e) 実装方針

### 影響ファイル
1. **scripts/done_gate.sh** (現行 126 行) — ≤20 行追加
2. **shared_context/task_yaml_schema.md** — post_steps: 欄 spec 追加
3. **queue/tasks/karo.yaml** (新規 or 既存) — 家老 self-task 枠の整備 (運用ルール化)
4. **tests/done_gate_test.sh** (or equivalent) — post_steps 存在/欠落パターンの unit test 追加

### done_gate.sh 追加ロジック (擬似 diff)
```bash
# 既存の advisor count check の直後に追加:
#
# ── post_steps marker 存在チェック (H_post_step_completion_detector) ──
POST_STEPS_MISSING=$(TASK_YAML="$TASK_YAML" TASK_ID="$TASK_ID" \
  REPO_DIR="$REPO_DIR" python3 <<'PYEOF' 2>/dev/null
import os, re, sys
path = os.environ['TASK_YAML']
target = os.environ['TASK_ID']
repo = os.environ['REPO_DIR']
with open(path) as f:
    content = f.read()
blocks = re.split(r'(?=^- task_id:)', content, flags=re.MULTILINE)
for block in blocks:
    m = re.search(r'^- task_id:\s*(\S+)', block, re.MULTILINE)
    if not m or m.group(1).strip().strip('"').strip("'") != target:
        continue
    # post_steps block 抽出 (YAML list)
    ps_m = re.search(r'^\s+post_steps:\s*\n((?:\s+-\s+.+\n)+)', block, re.MULTILINE)
    if not ps_m:
        sys.exit(0)  # skip (opt-in)
    missing = []
    for line in ps_m.group(1).splitlines():
        lm = re.match(r'\s+-\s+(.+?)\s*(?:#.*)?$', line)
        if not lm: continue
        marker = lm.group(1).strip().strip('"').strip("'")
        abs_marker = marker if os.path.isabs(marker) else os.path.join(repo, marker)
        if not os.path.isfile(abs_marker):
            missing.append(marker)
    for m in missing:
        print(m)
    sys.exit(0)
PYEOF
)

if [ -n "$POST_STEPS_MISSING" ]; then
  echo "BLOCK: ${TASK_ID} post_steps 未完了 ($(echo "$POST_STEPS_MISSING" | wc -l) 件欠落)" >&2
  echo "欠落 marker:" >&2
  echo "$POST_STEPS_MISSING" | sed 's/^/  - /' >&2
  echo "対応: post-step を実行完了させてから status:done / QC 依頼せよ" >&2
  exit 2
fi
```

### inbox_write.sh pre-hook (trigger 2 対応) — **scope defer**

**決定**: trigger 2 (inbox_write 時 dry-run gate) は **本設計 doc の scope 外** とし、follow-up 設計 doc で詳細化する。

**理由** (advisor 指摘反映):
- どの task_id を dry-run gate するかの mechanism が非自明。候補:
  - (a) `inbox_write.sh` に新 `--task <id>` 引数追加 (caller に負担)
  - (b) ENV `DONE_GATE_TASK_ID` で渡す (忘却リスク)
  - (c) メッセージ content から regex で cmd_id 抽出 (脆弱・false positive 多い)
  - (d) `queue/tasks/karo.yaml` の最新 assigned task を自動選択 (複数同時進行で誤爆)
- どれも一長一短・mechanism 決定は **本 doc の scope を超える深度** ゆえ follow-up に委ねる
- **本 doc の実装 cmd では trigger 1 (自己 status:done 宣言) のみ実装**
- trigger 2 は別 cmd (H_post_step_completion_detector v2 or 新 subtask_1449_e2) で spec 化

**暫定代替 (trigger 1 だけでも cmd_1446 型事故は部分的に防げる)**:
- 家老が自分の直実行 cmd を `queue/tasks/karo.yaml` に task として登録 (前提条件 §(a))
- 家老自身が `status:done` 宣言する段で done_gate.sh が発火
- → post_steps 欠落時は家老自身の done 宣言が BLOCK される
- → QC 依頼 (inbox_write) まで進まない (家老 self-discipline の補助)

cmd_1446 完全防御 (trigger 2) は follow-up doc で解決する。本 v1 は「家老 self-task workflow + trigger 1」で 80% カバーを狙う。

### schema 更新 (shared_context/task_yaml_schema.md)
```markdown
## §2.3 post_steps (任意)
長時間 post-step (gc/repack/大量ファイル生成/外部 API 完了待ち) を持つ task で、各 step の完了 marker を宣言する。
done_gate.sh が marker 存在をチェックし、1 件でも欠落していれば BLOCK する。

### 書式
```yaml
post_steps:
  - work/<cmd_id>/<step_name>.log
  - /absolute/path/to/marker
```

### marker の convention
- 既存の `work/<cmd_id>/<step>.log` 形式を推奨 (新 namespace 不在)
- 存在判定のみ (content 検証は `verify:` 欄の責務)

### 後方互換
欄なし → skip (opt-in)
```

### 所要工数 (見積)
- done_gate.sh diff + test: 1h
- ~~inbox_write.sh pre-hook~~: **scope defer** (follow-up doc)
- schema 更新 + docs: 30min
- 家老 self-task 枠整備: 1h
- **合計 2.5h** (LOW) ← scope defer により 1h 削減
- **follow-up cmd**: trigger 2 inbox_write pre-hook 設計 (別 cmd・≈2h 見積)

---

## (f) Acceptance Criteria (実装 cmd 発令時)

1. `scripts/done_gate.sh` に post_steps 存在確認ロジック追加 (diff ≤30 行)
2. `post_steps:` 欄なし task は skip (後方互換・既存全 task YAML で regression なし)
3. `post_steps:` 欄あり + 全 marker 存在 → exit 0
4. `post_steps:` 欄あり + 1 件以上欠落 → exit 2 + stderr に欠落 list 出力
5. `shared_context/task_yaml_schema.md` §2.3 spec 追加 (marker contract 含む・§R4)
6. ~~`scripts/inbox_write.sh` pre-hook (trigger 2)~~ → **scope defer** (follow-up doc)
7. `queue/tasks/karo.yaml` 家老 self-task 枠整備 (既存なら後方互換評価)
8. unit test: (a) post_steps 欄なし = skip (b) 全存在 = exit 0 (c) 部分欠落 = exit 2
9. 既存 task YAML での regression 全なし (verify/advisor 系 gate 動作不変)
10. advisor 2 回 (実装前 + 完了前) + commit 明示パス遵守
11. marker contract (§R4) を task_yaml_schema.md に明記・中間生成物 marker 指定の禁止事項含む

---

## (g) Implementation Checklist (実装担当者向け)

- [ ] **Pre**: `queue/tasks/gunshi.yaml` (L3253-) の subtask_1449_e task YAML + 本設計 doc を確認
- [ ] **Pre**: advisor() 実装前
- [ ] **Schema**: `shared_context/task_yaml_schema.md` §2.3 追加
- [ ] **Core**: `scripts/done_gate.sh` post_steps 検査ロジック追加 (≤20 行)
- [ ] **Hook**: `scripts/inbox_write.sh` pre-hook (qc_request/task_assigned 時)
- [ ] **Karo-self**: `queue/tasks/karo.yaml` 家老 self-task 枠整備 (spec + sample task)
- [ ] **Test**: unit test 3 パターン (skip / pass / block)
- [ ] **Regression**: 既存 task YAML サンプル 5 件で done_gate.sh 再走行 (verify pass 継続)
- [ ] **Doc**: CLAUDE.md or instructions/karo.md に family task YAML 書式例追加
- [ ] **Commit**: 明示パス add (`git add scripts/done_gate.sh scripts/inbox_write.sh shared_context/task_yaml_schema.md ...`・`git add .` 禁止)
- [ ] **Advisor** 完了前
- [ ] **Report**: ashigaru<N>_report_subtask_XXX.yaml に hotfix_notes/skill_candidate 含めて提出

### 優先順 (将来の実装 cmd 分解用)
1. schema + done_gate.sh 拡張 (最小機能) = 1.5h
2. inbox_write.sh pre-hook = 1h
3. karo.yaml 枠 + docs = 1h
4. test + regression = 30min

---

## Appendix A. cmd_1446 事案での適用シミュレーション

### 仮に本ハーネスが当時存在していたら
家老の cmd_1446 task YAML (仮):
```yaml
- task_id: cmd_1446_d9
  parent_cmd: cmd_1446
  status: in_progress
  post_steps:
    - work/cmd_1446/backup_size.log    # backup 完了
    - work/cmd_1446/filter_repo.log    # filter-repo 完了
    - work/cmd_1446/push.log           # push 完了
    - work/cmd_1446/post_size.log      # gc 完了 (← 本件の key marker)
```

家老が 21:03 に軍師 QC 依頼を `inbox_write.sh karo→gunshi qc_request` で発出すると:
- pre-hook が done_gate.sh を dry-run で呼出
- post_size.log が未生成 → `exit 2 BLOCK`
- inbox_write 自体を拒否 (メッセージ書き込み前)
- 家老へ "BLOCK: cmd_1446_d9 post_steps 未完了 (1 件欠落): work/cmd_1446/post_size.log" を返却
- 家老は gc 完了を待ち、post_size.log 生成確認後に再発出 → 通過

= cmd_1446 MAJOR F1 事案の自動予防が実現。

### Root cause との関係 (再掲)
本ハーネスは**規律問題の完全解決ではない**。家老が `post_steps:` 欄の宣言を忘れれば gate は発火しない。しかし:
1. schema 強制 (task_yaml_schema.md) で書き忘れ検知は可能
2. 家老が一度経験すれば今後は宣言する motivation が強化される (cmd_1446 事案の教訓)
3. gate 発火時の stderr メッセージが家老の規律を矯正する (教育効果)

**=> defense in depth として機能する。根本解決は家老の "script 起動 = 完了" 誤認を正す規律改善だが、本ハーネスはそれを補強する安全網。**

---

## Appendix B. 関連 cmd との依存関係

- **cmd_1442 execution_plan_v3.md**: 本ハーネスは H14/H15 merge の延長線上 (既存資産拡張原則に合致)
- **cmd_1443 H1 (done_gate.sh)**: 本ハーネスの拡張母体
- **cmd_1443 H7 (hotfix_trend_detector.sh)**: destructive 操作の trending 検知と本ハーネスの gate 発火は補完関係
- **cmd_1443 H9 (phase_gate_checker.sh)**: 粒度が異なる (Phase > post_step)・重複なし
- **cmd_1446 qc_1446_resume**: 本ハーネス提案の trigger 事案

---

## 変更履歴
- 2026-04-24 v1: 軍師 subtask_1449_e 初版設計 (advisor 2 回実施・H1 拡張採用)
  - advisor 作業前: binary 判定 (H1 拡張 vs 新 script) と trigger placement (A/B/C) の架構提示
  - advisor 設計完成前: 3 点指摘反映
    (1) §(c) 3-way reframe 註記追加 (task YAML steps vs 設計 doc の差の audit 可能化)
    (2) §(b) R4 marker 意味論契約追加 (中間生成物 tmp_pack_* 等を marker に指定禁止)
    (3) §(e) inbox_write pre-hook は scope defer・follow-up doc で詳細化
