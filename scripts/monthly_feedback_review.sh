#!/usr/bin/env bash
# monthly_feedback_review.sh - H13: memory/feedback_*.md 月次レビュー cron
# cmd_1443_p10 (cmd_1442 execution_plan_v3.md §2 H13)
#
# 目的: memory/feedback_*.md のうち 90日以上参照ゼロの stale feedback を検知し、
#       dashboard.md の「🔍 feedback レビュー推奨（月次検知）」セクションに追記 + ntfy 通知。
#
# 参照判定は 3 系統の OR (いずれか > 0 なら「参照あり」扱い):
#   1) git log --since="90 days ago" の commit message + body に slug 出現
#   2) queue/reports/*.yaml で mtime が 90日以内 かつ slug 出現
#   3) claude-mem (scripts/cmem_search.sh) で slug hit あり
#
# Usage:
#   bash scripts/monthly_feedback_review.sh              # normal run
#   bash scripts/monthly_feedback_review.sh --dry-run    # write nothing
#   bash scripts/monthly_feedback_review.sh \
#     --feedback-dir /tmp/fixtures --dashboard /tmp/dash.md \
#     --state-file /tmp/st.json --dry-run
#
# Options:
#   --feedback-dir DIR   feedback_*.md ディレクトリ
#                        (default: $HOME/.claude/projects/-home-murakami-multi-agent-shogun/memory)
#   --dashboard FILE     dashboard markdown (default: dashboard.md)
#   --state-file FILE    既通知 slug キャッシュ (default: logs/monthly_feedback_review_state.json)
#   --age-days N         stale とみなす age 閾値 日数 (default: 90)
#   --renotify-days N    同一 slug 再通知抑止期間 日数 (default: 30)
#   --reports-dir DIR    queue/reports ディレクトリ (default: queue/reports)
#   --no-cmem            claude-mem 照会を skip (fixture テスト用)
#   --no-ntfy            ntfy 送信を skip (dashboard/state は書く)
#   --dry-run            何も書かない (ログのみ)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FEEDBACK_DIR="$HOME/.claude/projects/-home-murakami-multi-agent-shogun/memory"
DASHBOARD="$ROOT/dashboard.md"
STATE_FILE="$ROOT/logs/monthly_feedback_review_state.json"
REPORTS_DIR="$ROOT/queue/reports"
AGE_DAYS=90
RENOTIFY_DAYS=30
USE_CMEM=1
NO_NTFY=0
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --feedback-dir) FEEDBACK_DIR="$2"; shift 2 ;;
    --dashboard)    DASHBOARD="$2"; shift 2 ;;
    --state-file)   STATE_FILE="$2"; shift 2 ;;
    --age-days)     AGE_DAYS="$2"; shift 2 ;;
    --renotify-days) RENOTIFY_DAYS="$2"; shift 2 ;;
    --reports-dir)  REPORTS_DIR="$2"; shift 2 ;;
    --no-cmem)      USE_CMEM=0; shift ;;
    --no-ntfy)      NO_NTFY=1; shift ;;
    --dry-run)      DRY_RUN=1; shift ;;
    -h|--help)      sed -n '2,32p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [ ! -d "$FEEDBACK_DIR" ]; then
  echo "[monthly_feedback_review] feedback dir not found: $FEEDBACK_DIR" >&2
  exit 1
fi

mkdir -p "$(dirname "$STATE_FILE")"
[ -f "$STATE_FILE" ] || echo '{"notified":{}}' > "$STATE_FILE"

NOW_EPOCH=$(date +%s)
AGE_SEC=$(( AGE_DAYS * 86400 ))
RENOTIFY_SEC=$(( RENOTIFY_DAYS * 86400 ))

# --- Collect stale slug candidates ---
CANDIDATES=$(mktemp)
trap 'rm -f "$CANDIDATES"' EXIT

shopt -s nullglob
for path in "$FEEDBACK_DIR"/feedback_*.md; do
  base=$(basename "$path")
  slug="${base#feedback_}"
  slug="${slug%.md}"
  [ -z "$slug" ] && continue

  mtime_epoch=$(stat -c %Y "$path")
  age_sec=$(( NOW_EPOCH - mtime_epoch ))
  if [ "$age_sec" -lt "$AGE_SEC" ]; then
    continue  # 新しい feedback は対象外
  fi

  # 1) git log 90日以内 に slug 出現?
  git_hits=0
  if [ -d "$ROOT/.git" ]; then
    gitlog=$(cd "$ROOT" && git log --since="$AGE_DAYS days ago" --pretty=format:'%s%n%b' 2>/dev/null || true)
    if printf '%s' "$gitlog" | grep -q -F "$slug"; then
      git_hits=1
    fi
  fi

  # 2) queue/reports の新しい yaml 内 slug 出現?
  report_hits=0
  if [ -d "$REPORTS_DIR" ]; then
    while IFS= read -r -d '' rpath; do
      if grep -q -F "$slug" "$rpath" 2>/dev/null; then
        report_hits=$(( report_hits + 1 ))
      fi
    done < <(find "$REPORTS_DIR" -name '*.yaml' -newermt "$AGE_DAYS days ago" -print0 2>/dev/null)
  fi

  # 3) claude-mem に slug hit あり? (best effort)
  cmem_hits=0
  if [ "$USE_CMEM" -eq 1 ]; then
    out=$(bash "$ROOT/scripts/cmem_search.sh" "$slug" 5 2>/dev/null || true)
    if [ -n "$out" ] && printf '%s' "$out" | grep -q -F "$slug"; then
      cmem_hits=1
    fi
  fi

  total=$(( git_hits + report_hits + cmem_hits ))
  if [ "$total" -eq 0 ]; then
    age_days=$(( age_sec / 86400 ))
    printf '%s\t%s\t%s\n' "$slug" "$age_days" "$path" >> "$CANDIDATES"
  fi
done
shopt -u nullglob

if [ ! -s "$CANDIDATES" ]; then
  echo "[monthly_feedback_review] no stale feedback (age>=${AGE_DAYS}d AND refs=0)" >&2
  exit 0
fi

# --- Dedupe against state file (renotify window) ---
ACTIONS=$(python3 - "$CANDIDATES" "$STATE_FILE" "$RENOTIFY_SEC" "$NOW_EPOCH" <<'PY'
import sys, json, os
cand_path, state_path, renotify_sec, now_epoch = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
with open(cand_path, encoding="utf-8") as f:
    cands = [line.rstrip("\n").split("\t") for line in f if line.strip()]
try:
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
except Exception:
    state = {"notified": {}}
notified = state.get("notified", {})
actions = []
for slug, age_days, path in cands:
    last = notified.get(slug)
    if last is not None and (now_epoch - int(last)) < renotify_sec:
        continue
    actions.append({"slug": slug, "age_days": int(age_days), "path": path})
json.dump({"actions": actions}, sys.stdout, ensure_ascii=False)
PY
)

TMP_ACTIONS=$(mktemp)
printf '%s' "$ACTIONS" > "$TMP_ACTIONS"

ACTION_COUNT=$(python3 -c 'import sys,json;print(len(json.load(open(sys.argv[1]))["actions"]))' "$TMP_ACTIONS")
if [ "$ACTION_COUNT" = "0" ]; then
  echo "[monthly_feedback_review] all candidates already notified within renotify window" >&2
  rm -f "$TMP_ACTIONS"
  exit 0
fi

echo "[monthly_feedback_review] stale feedback to notify: $ACTION_COUNT" >&2
python3 - "$TMP_ACTIONS" >&2 <<'PY'
import sys, json
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
for a in data["actions"]:
    print(f"  - {a['slug']} (age={a['age_days']}d)")
PY

if [ "$DRY_RUN" -eq 1 ]; then
  echo "[monthly_feedback_review] dry-run: no writes" >&2
  rm -f "$TMP_ACTIONS"
  exit 0
fi

# --- Update dashboard.md ---
python3 - "$TMP_ACTIONS" "$DASHBOARD" <<'PY'
import sys, json, datetime, os
actions_file, dash_path = sys.argv[1], sys.argv[2]
with open(actions_file, encoding="utf-8") as f:
    data = json.load(f)
if not os.path.exists(dash_path):
    # Create a minimal dashboard file so cron keeps working in test envs.
    with open(dash_path, "w", encoding="utf-8") as f:
        f.write("# Dashboard\n\n")
with open(dash_path, encoding="utf-8") as f:
    src = f.read()
heading = "### 🔍 feedback レビュー推奨（月次検知）"
idx = src.find(heading)
if idx < 0:
    src = src.rstrip() + "\n\n" + heading + "\n"
    idx = src.find(heading)
end_of_heading_line = src.find("\n", idx) + 1
today = datetime.date.today().isoformat()
new_lines = []
for a in data["actions"]:
    marker = f"monthly-feedback-review: {a['slug']}"
    if marker in src:
        continue
    line = (f"- **feedback_{a['slug']}.md**: {a['age_days']}日参照ゼロ → "
            f"陳腐化確認/削除検討 [{today}] "
            f"<!-- {marker} -->")
    new_lines.append(line)
if not new_lines:
    sys.exit(0)
insertion = "".join(l + "\n" for l in new_lines)
updated = src[:end_of_heading_line] + insertion + src[end_of_heading_line:]
with open(dash_path, "w", encoding="utf-8") as f:
    f.write(updated)
print(f"[monthly_feedback_review] dashboard.md updated (+{len(new_lines)} entries)", file=sys.stderr)
PY

# --- Send ntfy (1 summary message) ---
if [ "$NO_NTFY" -eq 0 ]; then
  SUMMARY=$(python3 - "$TMP_ACTIONS" <<'PY'
import sys, json
with open(sys.argv[1], encoding="utf-8") as f:
    d = json.load(f)
slugs = ", ".join(a["slug"] for a in d["actions"][:3])
rest = len(d["actions"]) - 3
tail = f" +他{rest}件" if rest > 0 else ""
print(f"🔍 stale feedback {len(d['actions'])}件検知: {slugs}{tail} → dashboard.md レビュー推奨")
PY
  )
  bash "$ROOT/scripts/ntfy.sh" "$SUMMARY" || true
else
  echo "[monthly_feedback_review] --no-ntfy: skip" >&2
fi

# --- Update state file ---
python3 - "$TMP_ACTIONS" "$STATE_FILE" "$NOW_EPOCH" <<'PY'
import sys, json
actions_file, state_path, now_epoch = sys.argv[1], sys.argv[2], int(sys.argv[3])
with open(actions_file, encoding="utf-8") as f:
    data = json.load(f)
try:
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
except Exception:
    state = {"notified": {}}
notified = state.get("notified", {})
for a in data["actions"]:
    notified[a["slug"]] = now_epoch
state["notified"] = notified
history = state.get("history", [])
import datetime
history.append({
    "at": datetime.datetime.fromtimestamp(now_epoch).isoformat(timespec="seconds"),
    "slugs": [a["slug"] for a in data["actions"]],
})
state["history"] = history[-100:]
with open(state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
PY

rm -f "$TMP_ACTIONS"
echo "[monthly_feedback_review] done" >&2
