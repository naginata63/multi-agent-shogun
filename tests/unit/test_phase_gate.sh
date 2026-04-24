#!/usr/bin/env bash
# test_phase_gate.sh — cmd_1443 p07 H9 phase_gate_checker.sh unit tests
#
# 検査対象:
#   1. --help / --scan / 通常モード が正しく exit code と出力を返す
#   2. scan モードで多 Phase cmd の phase_gate 未宣言を PHASE_GATE_WARNING として検出
#   3. scan モードで phase_gate: required 宣言済 cmd は警告しない
#   4. scan モードで単 Phase cmd は警告しない (false positive 回避)
#   5. 通常モードで dashboard.md 🚨セクション末尾に追記される
#   6. 通常モードで実 dashboard/ntfy を触らず test 環境内で完結する

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$SCRIPT_DIR/scripts/phase_gate_checker.sh"
PASS=0
FAIL=0

run_case() {
    local name="$1"; shift
    local expect="$1"; shift
    local out actual
    out=$("$@" 2>&1)
    actual=$?
    if [ "$actual" -eq "$expect" ]; then
        echo "PASS: $name (exit=$actual)"
        PASS=$((PASS+1))
    else
        echo "FAIL: $name (expect=$expect actual=$actual)"
        echo "  output: $out"
        FAIL=$((FAIL+1))
    fi
}

[ -x "$SCRIPT" ] || { echo "ERROR: $SCRIPT not executable"; exit 1; }

TMP=$(mktemp -d "${TMPDIR:-/tmp}/phase_gate_test.XXXXXX")
trap "rm -rf '$TMP'" EXIT

# ═══ Case 1: --help ═══
run_case "--help → exit 0" 0 bash "$SCRIPT" --help

# ═══ Case 2: 引数なし → exit 2 (usage) ═══
run_case "引数なし → exit 2" 2 bash "$SCRIPT"

# ═══ Case 3: --scan で多 Phase cmd 未宣言検出 ═══
cat > "$TMP/multi_phase.yaml" << 'YAMLEOF'
commands:
- id: cmd_9001
  command: |
    Phase 1: 準備
    Phase 2: 実装
    Phase 3: 確認
- id: cmd_9002
  command: |
    Wave A: 同時発令
    Wave B: 後続発令
  phase_gate: required
- id: cmd_9003
  command: |
    単純タスク(Phase なし)
YAMLEOF

out=$(bash "$SCRIPT" --scan --yaml "$TMP/multi_phase.yaml" 2>&1)
echo "--- scan output ---"
echo "$out"
echo "---"
if echo "$out" | grep -q 'PHASE_GATE_WARNING: cmd_9001'; then
    echo "PASS: scan detected cmd_9001 (Phase 1,2,3 未宣言)"
    PASS=$((PASS+1))
else
    echo "FAIL: scan should detect cmd_9001"
    FAIL=$((FAIL+1))
fi

if echo "$out" | grep -q 'PHASE_GATE_WARNING: cmd_9002'; then
    echo "FAIL: scan should NOT warn cmd_9002 (phase_gate: required 宣言済)"
    FAIL=$((FAIL+1))
else
    echo "PASS: scan skipped cmd_9002 (declared)"
    PASS=$((PASS+1))
fi

if echo "$out" | grep -q 'PHASE_GATE_WARNING: cmd_9003'; then
    echo "FAIL: scan should NOT warn cmd_9003 (Phase キーワード 0 個)"
    FAIL=$((FAIL+1))
else
    echo "PASS: scan skipped cmd_9003 (単 Phase・false positive 回避)"
    PASS=$((PASS+1))
fi

# ═══ Case 4: dashboard.md 🚨セクション末尾追記 (test 環境内) ═══
# REPO_DIR 置換のため SCRIPT を temp にコピーして DASHBOARD/NTFY を上書き
MOCK_REPO="$TMP/mock_repo"
mkdir -p "$MOCK_REPO/scripts" "$MOCK_REPO/queue" "$MOCK_REPO/logs"

# shogun_to_karo.yaml 準備 (cmd 実在チェック通過用)
cat > "$MOCK_REPO/queue/shogun_to_karo.yaml" << 'YAMLEOF'
commands:
- id: cmd_9999
  command: |
    Phase 1: 開始
    Phase 2: 完了
  phase_gate: required
YAMLEOF

# dashboard.md 準備
cat > "$MOCK_REPO/dashboard.md" << 'MDEOF'
# 📊 戦況報告

## 🚨 要対応（殿の御判断必要）

### 🚨 既存のエントリ
- 既に何かある

## 📋 進行中

- cmd_xxx
MDEOF

# ntfy.sh をモック化 (no-op 返却)
cat > "$MOCK_REPO/scripts/ntfy.sh" << 'SHEOF'
#!/usr/bin/env bash
echo "MOCK_NTFY: $*" >> "$(dirname "$(dirname "$0")")/logs/ntfy_mock.log"
exit 0
SHEOF
chmod +x "$MOCK_REPO/scripts/ntfy.sh"

# phase_gate_checker.sh をコピー
cp "$SCRIPT" "$MOCK_REPO/scripts/phase_gate_checker.sh"
chmod +x "$MOCK_REPO/scripts/phase_gate_checker.sh"

# 実行
out=$(bash "$MOCK_REPO/scripts/phase_gate_checker.sh" cmd_9999 2 "Phase2 完了: マイグレーション成功" 2>&1)
rc=$?

if [ "$rc" -eq 0 ]; then
    echo "PASS: 通常モード exit 0"
    PASS=$((PASS+1))
else
    echo "FAIL: 通常モード exit $rc (expected 0)"
    echo "  output: $out"
    FAIL=$((FAIL+1))
fi

# dashboard.md に 🚨要対応セクション末尾に entry が追加され、かつ ## 📋 進行中 の前に入っているか
if grep -q "🚨 cmd_9999 Phase 2 完了・殿確認要" "$MOCK_REPO/dashboard.md"; then
    echo "PASS: dashboard.md に新規 entry 追記"
    PASS=$((PASS+1))
else
    echo "FAIL: dashboard.md に entry が追加されていない"
    echo "--- dashboard after ---"
    cat "$MOCK_REPO/dashboard.md"
    echo "---"
    FAIL=$((FAIL+1))
fi

# 挿入位置が 🚨セクション末尾 = ## 📋 進行中 の前にあるか
if python3 -c "
import sys
content = open('$MOCK_REPO/dashboard.md').read()
a = content.find('cmd_9999 Phase 2')
b = content.find('## 📋 進行中')
sys.exit(0 if 0 < a < b else 1)
"; then
    echo "PASS: 挿入位置が 🚨 セクション内・## 📋 進行中 の前"
    PASS=$((PASS+1))
else
    echo "FAIL: 挿入位置が正しくない"
    FAIL=$((FAIL+1))
fi

# ntfy モックが呼ばれたか
if [ -f "$MOCK_REPO/logs/ntfy_mock.log" ] && grep -q "cmd_9999" "$MOCK_REPO/logs/ntfy_mock.log"; then
    echo "PASS: ntfy モック呼出 OK"
    PASS=$((PASS+1))
else
    echo "FAIL: ntfy モックが呼ばれていない"
    FAIL=$((FAIL+1))
fi

# ═══ Case 5: cmd_id が yaml に無くても警告のみで実行継続 ═══
out=$(bash "$MOCK_REPO/scripts/phase_gate_checker.sh" cmd_unknown 1 "test" 2>&1)
rc=$?
if [ "$rc" -eq 0 ] && echo "$out" | grep -q "WARNING.*not found"; then
    echo "PASS: 不在 cmd_id は WARNING のみで exit 0 継続"
    PASS=$((PASS+1))
else
    echo "FAIL: 不在 cmd_id の扱いが想定外 (exit=$rc)"
    echo "  output: $out"
    FAIL=$((FAIL+1))
fi

# ═══ Case 6: --scan で単 Phase cmd を false positive しない ═══
cat > "$TMP/single_phase.yaml" << 'YAMLEOF'
commands:
- id: cmd_10001
  command: |
    Phase 1 だけ: ここは単一 Phase (キーワード 1 つのみ)
YAMLEOF
out=$(bash "$SCRIPT" --scan --yaml "$TMP/single_phase.yaml" 2>&1)
if echo "$out" | grep -q 'PHASE_GATE_WARNING'; then
    echo "FAIL: 単 Phase cmd も誤検知"
    FAIL=$((FAIL+1))
else
    echo "PASS: 単 Phase cmd (キーワード 1 つ) → 警告なし"
    PASS=$((PASS+1))
fi

echo ""
echo "── Summary ──"
echo "PASS: $PASS"
echo "FAIL: $FAIL"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
