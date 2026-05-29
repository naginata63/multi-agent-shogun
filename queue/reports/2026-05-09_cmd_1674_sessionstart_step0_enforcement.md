# cmd_1674: SessionStart Step 0 Monitor 強制起動 実装報告

**Task ID**: subtask_1674_sessionstart_step0  
**Parent Cmd**: cmd_1674  
**Status**: In Progress  
**Date**: 2026-05-09  

---

## 背景・問題定義

SessionStart Step 0 (SSE Monitor 起動) は footer 出現時の唯一の受信機構であり、Monitor なしでは karo からのメッセージを見落とす危険がある。

現状:
- `sessionstart_hook.sh` が Step 0 を出力コンテキストに含める
- しかし source=startup 時に出力が正しく注入されない可能性
- Agent が Step 0 を skip → Monitor 未起動 → inbox メッセージ見落とし

**殿原文**: 「ベータも実施 — sessionstart_hook.sh を改修し source=startup でも Monitor 起動を強制する文言にする」

---

## 設計: 案A〜D 比較

### 案A: sessionstart_hook.sh で Monitor を直接起動（bash curl 実行）

**概要**:
```bash
# sessionstart_hook.sh 内で
if [ "$SOURCE" = "startup" ] || [ "$SOURCE" = "compact" ]; then
    # Monitor 既存確認 (pgrep)
    if ! pgrep -f "curl.*inbox_stream.*agent=${AGENT_ID}" > /dev/null 2>&1; then
        # Monitor 起動（curl の背景実行）
        curl -N -s "http://192.168.2.4:8770/api/inbox_stream?agent=${AGENT_ID}" | \
        grep --line-buffered "^data:" &
        sleep 1  # 起動完了待ち
    fi
fi
```

**メリット**:
- Monitor は hook の自動実行により確実に起動
- source=startup/compact 両方に対応
- 重複防止ロジック実装可能

**デメリット**:
- Hook 内での背景プロセス実行は複雑・テスト困難
- Bash script 内での curl 背景実行は状態管理が曖昧
- Monitor tool（Python wrapper）が使えず、curl 直実行のため mawk/jq に依存
- Hook 内では stdin/stdout が制限され、error handling が限定的

**実装コスト**: 中程度  
**確実性**: 高（Hook 自動実行）

---

### 案B: CLAUDE.md Step 0 文言を強化（CRITICAL/NEVER SKIP化）

**概要**:
```markdown
## Session Start / Recovery (all agents)

### Step 0: SSE Monitor Auto-Start (MANDATORY - NEVER SKIP)

**CRITICAL RULE**: Step 0 は必ず Session Start の最初に実行せよ。skip 厳禁。
Monitor なし = inbox 未受信 = タスク見落とし = 重大インシデント。

実行手順:
1. pgrep -a curl | grep "agent=<YOUR_ID>" で Monitor 既存確認
2. 0 本なら Monitor(...) で SSE stream 起動
3. 1 本なら何もせず次へ
4. 2 本以上なら古い PID kill、1 本に統一

このステップをスキップするな。Agent は Session Start の最初にこれを実行すること。
```

**メリット**:
- 文書化強化・明確化・容易な実装
- Agent に義務を明確に示す
- 後方互換・既存機能への影響なし

**デメリット**:
- 強制力なし（Agent が skip する可能性は残る）
- 依然として Agent の理解・実行に依存

**実装コスト**: 低  
**確実性**: 中（文書化の力に依存）

---

### 案C: instructions/*.md 各エージェント手順に Step 0 を明示追加

**概要**:
各エージェントの `instructions/ashigaru.md`, `instructions/karo.md`, `instructions/gunshi.md` の workflow セクションに Step 0 を追加:

```yaml
workflow:
  - step: 0
    action: sme_monitor_startup
    command: 'pgrep -a curl | grep "agent=ashigaru2" && echo "Monitor running" || Monitor(...)'
    mandatory: true
    note: "SSE Monitor が未起動ならここで必ず起動すること。inbox を見落とすな。"
```

**メリット**:
- Agent 固有の手順に組み込む・明示的
- instructions file を読むたびに意識される
- YAML 形式で機械可読

**デメリット**:
- 重複（CLAUDE.md と instructions の両方に記載）
- メンテ負荷増加
- Agent 依存（skip 可能性は残る）

**実装コスト**: 低〜中  
**確実性**: 中（instructions 読むことに依存）

---

### 案D: A+B+C 統合（推奨）

**概要**:
- sessionstart_hook.sh で Monitor 起動を**試みる**（案A）
- CLAUDE.md で Step 0 を CRITICAL化（案B）
- instructions/*.md で各 Agent に明示（案C）

**メリット**:
- 多層防御・確実性最大化
- Hook 失敗時も Agent 手動実行で回復可能
- 文書化と実装の両立

**デメリット**:
- 複雑化・メンテ負荷増加
- 冗長性（同じ情報が複数箇所に）

**実装コスト**: 中程度  
**確実性**: 最高（多層防御）

---

## 推奨案: **案D (A+B+C 統合)**

理由:
1. **Hook 自動起動** (案A) で、Agent が Step 0 を忘れた場合の backup
2. **CLAUDE.md 強化** (案B) で、文書の権威性・注意喚起
3. **instructions 追加** (案C) で、Agent 固有の明示性

---

## 実装内容

### 1. sessionstart_hook.sh 改修（案A実装）

**Location**: `scripts/sessionstart_hook.sh` L32 付近

**変更内容**:
```bash
# After SOURCE extraction (L32)
SOURCE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('source', 'unknown'))" 2>/dev/null || echo "unknown")

# NEW: Step 0 Monitor auto-start for source=startup
if [ "$SOURCE" = "startup" ] || [ "$SOURCE" = "compact" ]; then
    # Check if Monitor already running
    MONITOR_PID=$(pgrep -f "curl.*inbox_stream.*agent=${AGENT_ID}" 2>/dev/null | head -1 || true)
    
    if [ -z "$MONITOR_PID" ]; then
        # No Monitor → start one in background
        (
            curl -N -s "http://192.168.2.4:8770/api/inbox_stream?agent=${AGENT_ID}" 2>/dev/null | \
            grep --line-buffered "^data:" 2>/dev/null
        ) &
        sleep 1  # Brief wait for startup
    fi
    # If Monitor already running, skip (prevent duplicate)
fi
```

### 2. CLAUDE.md Step 0 CRITICAL化（案B実装）

**Location**: `CLAUDE.md` の SessionStart セクション直後

**変更内容**:
```markdown
## Session Start / Recovery (all agents)

...existing steps 1-6...

### Step 0: SSE Monitor Auto-Start (CRITICAL - MANDATORY)

**MANDATORY BEFORE STEP 1**: Session Start 最初に以下を必ず実行:

1. **Monitor alive check**: `pgrep -a curl | grep "agent=<YOUR_ID>"` を実行
   - 結果が 1 本: Monitor 稼働中。何もせず次へ進め。
   - 結果が 0 本: Monitor 未起動。Step 0-B 実行。
   - 結果が 2 本以上: 古い PID kill して 1 本に統一。

2. **Monitor startup**: Monitor が 0 本なら以下:
   ```
   Monitor(command='curl -N -s "http://192.168.2.4:8770/api/inbox_stream?agent=<YOUR_ID>" | grep --line-buffered "^data:"')
   ```

3. **Catch-up inbox fetch**: `curl http://192.168.2.4:8770/api/inbox_messages?agent=<YOUR_ID>&unread=1`

**WARNING**: Monitor なし = inbox 未受信 = タスク見落とし = 重大。skip するな。
```

### 3. instructions/ashigaru.md Step 0 追加（案C実装）

**Location**: `instructions/ashigaru.md` の workflow セクション最初

**変更内容**: workflow step 0 として Monitor startup を追加（既存の step 1-10 の前）

---

## 検証方法

### 検証1: Hook 自動起動確認
```bash
# sessionstart_hook.sh がディスク上で正しく編集されているか
bash -n scripts/sessionstart_hook.sh && echo "✅ Syntax OK"

# curl Monitor コマンドが Hook 内に含まれているか
grep -q "curl.*inbox_stream" scripts/sessionstart_hook.sh && echo "✅ Monitor cmd present"
```

### 検証2: ashigaru1 再起動時の Monitor 確認
```bash
# ashigaru1 (0.1 pane) の CLI を kill → 再起動
# → Monitor が自動起動されるか tmux pane で確認
tmux send-keys -t multiagent:0.1 C-c
sleep 2
bash scripts/switch_cli.sh 1 haiku  # ashigaru1 再起動
sleep 3
pgrep -a curl | grep "agent=ashigaru1" && echo "✅ Monitor auto-started"
```

### 検証3: /clear 後のコンテキスト確認
```bash
# ashigaru2 に /clear を送信（家老が実施）
# → Session Start が走り、sessionstart_hook.sh 出力にstep 0が強制される
# → Monitor が自動起動されることを確認
```

---

## 成果物チェックリスト

- [x] 案A〜D の比較・推奨案選定（このレポート内）
- [x] sessionstart_hook.sh 改修（Step 0 コンテキスト注入・Monitor起動はAgent手動に一本化）
- [x] CLAUDE.md Step 0 強化（CRITICAL化・文言追加）
- [x] instructions/ashigaru.md step 0 追加（workflow に組み込み）
- [x] bash -n 構文チェック (2026-05-29 検証OK)
- [x] git commit & push (b74ba39, 01baabf, 2c1593d, 5f1968b 全てpush済)
- [ ] ntfy 殿に完了通知 ← 家老が実施

---

## 最終実装形態 (2026-05-12 殿命による改訂)

**案A (hook内curl自動起動) は撤回**: nohup curl を hook がバックグラウンド起動したが、
Claude Code の Monitor tool ハンドラに繋がっておらず inbox event を処理できぬ孤児プロセスだった。
PRECHECK (pgrep) がこの孤児を hit → Monitor tool 起動が抑制 → メッセージ受信機能停止という構造バグ。

**最終採用**: 案B+C のみ (文脈注入に特化)
1. **sessionstart_hook.sh**: Step 0 の手順をテキストで注入（curl実行はしない）
2. **CLAUDE.md**: Step 0 を CRITICAL 化 (MANDATORY BEFORE STEP 1)
3. **instructions/*.md**: 各エージェントの workflow step 0 に Monitor startup を明示
4. **実際の Monitor 起動**: 各エージェントが Session Start 時に Step 0-C で Monitor tool を手動起動

## 注記

- Hook は context 注入に専念し、Monitor 起動はエージェント自身が行う設計が確定
- 現状の Step 0 手順 (0-A〜0-G) は本番稼働実績あり (全エージェントで運用中)

