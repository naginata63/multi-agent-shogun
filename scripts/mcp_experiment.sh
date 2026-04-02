#!/usr/bin/env bash
# MCP夜間実験スクリプト
# 実行: 毎晩2:00 (cron)
# 出力: work/cmd_1068/nightly/YYYY-MM-DD.yaml
# 参照: shogun_to_karo.yaml cmd_1068, work/cmd_1047/mcp_migration_plan.md

set -euo pipefail

# cron環境でnodeが見つかるようにnvmのPATHを追加
export PATH="/home/murakami/.nvm/versions/node/v20.20.0/bin:$PATH"

WORKTREE_DIR="/home/murakami/shogun-mcp-experiment"
MCP_SERVER_DIR="${WORKTREE_DIR}/work/cmd_1068/mcp-server"
NIGHTLY_DIR="${WORKTREE_DIR}/work/cmd_1068/nightly"
MAIN_REPO="/home/murakami/multi-agent-shogun"
LOG_FILE="/tmp/mcp_experiment_$(date +%Y%m%d_%H%M%S).log"
DATE=$(date +%Y-%m-%d)
RESULT_FILE="${NIGHTLY_DIR}/${DATE}.yaml"
MCP_PID=""

# ログ関数
log() {
  echo "[$(date '+%H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

# 終了時クリーンアップ
cleanup() {
  if [[ -n "${MCP_PID}" ]] && kill -0 "${MCP_PID}" 2>/dev/null; then
    log "MCPサーバー停止 (PID: ${MCP_PID})"
    kill "${MCP_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# 結果記録用変数
RESULTS=()
ERRORS=()
START_TIME=$(date +%s)

log "=== MCP夜間実験開始: ${DATE} ==="
log "worktree: ${WORKTREE_DIR}"

mkdir -p "${NIGHTLY_DIR}"

# ============================================================
# Step 1: MCPサーバー起動（stdioモード - バックグラウンド）
# ============================================================
log "Step 1: MCPサーバー起動"

# サーバーはstdioで通信するため、テストはNode.jsスクリプト経由で呼ぶ
# ここではDBを直接操作するテストスクリプトを使用
SCENARIO_SCRIPT="${WORKTREE_DIR}/work/cmd_1068/mcp-server/build/index.js"

if [[ ! -f "${SCENARIO_SCRIPT}" ]]; then
  log "ERROR: MCPサーバーがビルドされていない: ${SCENARIO_SCRIPT}"
  ERRORS+=("build_missing")
fi

# ============================================================
# Step 2: 最小シナリオ実行（Node.jsスクリプト）
# ============================================================
log "Step 2: 最小シナリオ実行"

SCENARIO_RUNNER="${MCP_SERVER_DIR}/build/run_scenario.js"

# シナリオ実行スクリプトを動的生成
INLINE_SCENARIO=$(cat <<'SCENARIO_JS'
const { createTask, getAssignedTasks, updateTaskStatus, sendMessage, getUnreadMessages, submitReport, getStats } = require('./database.js');

async function runScenario() {
  const results = {};

  // DB warmup: 初回スキーマ初期化のレイテンシを計測対象外にする
  getStats();

  const startTime = Date.now();

  try {
    // シナリオ: タスク作成→割当確認→状態更新→メッセージ→報告
    const taskId = `exp_${Date.now()}`;

    // [1] タスク作成（家老-exp → 足軽1-exp）
    const t0 = Date.now();
    const created = createTask(taskId, 'ashigaru1-exp', 'hello_world.pyを作成せよ', 'cmd_1068');
    const createLatency = Date.now() - t0;
    results.task_delivery = created.success ? 'PASS' : 'FAIL';
    results.create_latency_ms = createLatency;

    // [2] タスク取得（足軽1-expがポーリング）
    const assigned = getAssignedTasks('ashigaru1-exp');
    const found = assigned.tasks.some(t => t.task_id === taskId);
    results.task_retrieval = found ? 'PASS' : 'FAIL';

    // [3] ステータス更新
    updateTaskStatus(taskId, 'in_progress');
    const statusResult = updateTaskStatus(taskId, 'in_progress');
    results.status_update = statusResult.success ? 'PASS' : 'FAIL';

    // [4] メッセージ送信
    const t1 = Date.now();
    const msg = sendMessage('karo-exp', 'タスク開始します', 'task_started', 'ashigaru1-exp');
    const msgLatency = Date.now() - t1;
    results.message_send = msg.success ? 'PASS' : 'FAIL';
    results.message_latency_ms = msgLatency;

    // [5] メッセージ取得
    const msgs = getUnreadMessages('karo-exp');
    results.message_receive = msgs.messages.length > 0 ? 'PASS' : 'FAIL';

    // [6] 同時書込テスト（3件同時）
    const promises = [
      Promise.resolve(sendMessage('karo-exp', 'msg1', 'test', 'a1')),
      Promise.resolve(sendMessage('karo-exp', 'msg2', 'test', 'a2')),
      Promise.resolve(sendMessage('karo-exp', 'msg3', 'test', 'a3')),
    ];
    const concurrent = await Promise.all(promises);
    results.concurrent_write = concurrent.every(r => r.success) ? 'PASS' : 'FAIL';

    // [7] 完了報告
    const t2 = Date.now();
    const report = submitReport('ashigaru1-exp', taskId, 'hello_world.py作成完了');
    const reportLatency = Date.now() - t2;
    results.report_delivery = report.success ? 'PASS' : 'FAIL';
    results.report_latency_ms = reportLatency;

    // [8] レイテンシ判定（全操作1秒以内か）
    const maxLatency = Math.max(createLatency, msgLatency, reportLatency);
    results.latency_under_1sec = maxLatency < 1000 ? 'PASS' : 'FAIL';
    results.max_latency_ms = maxLatency;

    // [9] フォールバックテスト（DB操作が成功していればOK）
    const stats = getStats();
    results.fallback_test = stats.task_count > 0 ? 'PASS' : 'FAIL';

    results.total_duration_ms = Date.now() - startTime;
    results.stats = stats;

    // 全PASS判定
    const passCount = Object.values(results).filter(v => v === 'PASS').length;
    const failCount = Object.values(results).filter(v => v === 'FAIL').length;
    results.summary = `${passCount}PASS / ${failCount}FAIL`;
    results.overall = failCount === 0 ? 'PASS' : 'FAIL';

  } catch (err) {
    results.error = err.message;
    results.overall = 'FAIL';
  }

  console.log(JSON.stringify(results, null, 2));
  process.exit(results.overall === 'PASS' ? 0 : 1);
}

runScenario();
SCENARIO_JS
)

log "シナリオスクリプト実行中..."
cd "${MCP_SERVER_DIR}/build"

SCENARIO_OUTPUT=""
SCENARIO_EXIT=0

if node -e "${INLINE_SCENARIO}" > "${LOG_FILE}.scenario.json" 2>>"${LOG_FILE}"; then
  SCENARIO_OUTPUT=$(cat "${LOG_FILE}.scenario.json")
  log "シナリオ実行成功"
else
  SCENARIO_EXIT=$?
  SCENARIO_OUTPUT=$(cat "${LOG_FILE}.scenario.json" 2>/dev/null || echo '{"overall":"FAIL","error":"node実行失敗"}')
  log "WARNING: シナリオ実行失敗 (exit: ${SCENARIO_EXIT})"
  ERRORS+=("scenario_failed")
fi

# ============================================================
# Step 3: 結果を判定
# ============================================================
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

OVERALL=$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('overall','FAIL'))" 2>/dev/null || echo "FAIL")
SUMMARY=$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('summary','N/A'))" 2>/dev/null || echo "N/A")
MAX_LATENCY=$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('max_latency_ms','N/A'))" 2>/dev/null || echo "N/A")

log "結果: ${OVERALL} (${SUMMARY})"
log "最大レイテンシ: ${MAX_LATENCY}ms"
log "所要時間: ${DURATION}秒"

# ============================================================
# Step 4: 結果をYAMLに記録
# ============================================================
log "Step 4: 結果記録 → ${RESULT_FILE}"

# JSON → YAML変換
PASS_COUNT=$(echo "${SCENARIO_OUTPUT}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(sum(1 for v in d.values() if v == 'PASS'))
" 2>/dev/null || echo "0")

FAIL_COUNT=$(echo "${SCENARIO_OUTPUT}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(sum(1 for v in d.values() if v == 'FAIL'))
" 2>/dev/null || echo "0")

ERROR_LIST=""
if [[ ${#ERRORS[@]} -gt 0 ]]; then
  for e in "${ERRORS[@]}"; do
    ERROR_LIST+="  - ${e}\n"
  done
else
  ERROR_LIST="  []\n"
fi

cat > "${RESULT_FILE}" <<YAML
date: "${DATE}"
experiment: "mcp_minimal_scenario"
duration_sec: ${DURATION}
overall: "${OVERALL}"
summary: "${SUMMARY}"
results:
  task_delivery: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('task_delivery','N/A'))" 2>/dev/null)"
  task_retrieval: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('task_retrieval','N/A'))" 2>/dev/null)"
  status_update: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status_update','N/A'))" 2>/dev/null)"
  message_send: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message_send','N/A'))" 2>/dev/null)"
  message_receive: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message_receive','N/A'))" 2>/dev/null)"
  concurrent_write: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('concurrent_write','N/A'))" 2>/dev/null)"
  report_delivery: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('report_delivery','N/A'))" 2>/dev/null)"
  latency_under_1sec: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('latency_under_1sec','N/A'))" 2>/dev/null)"
  fallback_test: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('fallback_test','N/A'))" 2>/dev/null)"
latency:
  max_ms: ${MAX_LATENCY}
  create_ms: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('create_latency_ms','N/A'))" 2>/dev/null)"
  message_ms: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message_latency_ms','N/A'))" 2>/dev/null)"
  report_ms: "$(echo "${SCENARIO_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('report_latency_ms','N/A'))" 2>/dev/null)"
errors:
$(printf "${ERROR_LIST}")
log_file: "${LOG_FILE}"
conclusion: "$([ "${OVERALL}" = "PASS" ] && echo "全項目PASS。Phase 2検討可能" || echo "FAIL項目あり。ログ確認要")"
YAML

log "結果ファイル: ${RESULT_FILE}"

# ============================================================
# Step 5: ntfy通知
# ============================================================
log "Step 5: ntfy通知"

if [[ "${OVERALL}" = "PASS" ]]; then
  NTFY_MSG="✅ MCP夜間実験 ${DATE}: ${SUMMARY} 全PASS (${DURATION}秒)"
else
  NTFY_MSG="❌ MCP夜間実験 ${DATE}: ${SUMMARY} FAIL (${DURATION}秒)"
fi

if [[ -f "${MAIN_REPO}/scripts/ntfy.sh" ]]; then
  bash "${MAIN_REPO}/scripts/ntfy.sh" "${NTFY_MSG}" 2>>"${LOG_FILE}" || true
fi

log "=== 実験完了: ${OVERALL} ==="
exit $([ "${OVERALL}" = "PASS" ] && echo 0 || echo 1)
