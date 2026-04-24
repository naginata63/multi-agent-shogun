#!/usr/bin/env bash
# hotfix_trend_detector.sh - H7: hotfix 3回→skill 自動提案 cron
# cmd_1443_p05 (cmd_1442 execution_plan_v3.md §2 H7)
#
# Scan queue/reports/ashigaru*_report_*.yaml + claude-mem hotfix_notes,
# cluster similar hotfixes (Jaccard >= 0.5 OR shared file path),
# and when a cluster reaches >=3 hits, append to dashboard.md skill候補 +
# send ntfy. Idempotent via logs/hotfix_trend_state.json.
#
# Usage:
#   bash scripts/hotfix_trend_detector.sh              # normal run
#   bash scripts/hotfix_trend_detector.sh --dry-run    # no dashboard/ntfy writes
#   bash scripts/hotfix_trend_detector.sh \
#     --reports-dir work/cmd_1443_p05/fixtures \
#     --state-file /tmp/hftest.json --dashboard /tmp/dash.md --dry-run
#
# Options:
#   --reports-dir DIR   scan directory (default: queue/reports)
#   --state-file FILE   notified-cluster cache (default: logs/hotfix_trend_state.json)
#   --dashboard FILE    dashboard markdown (default: dashboard.md)
#   --threshold N       hits required to fire (default: 3)
#   --jaccard F         similarity threshold (default: 0.5)
#   --include-cmem      also include cmem_search.sh "hotfix" output (best-effort)
#   --no-ntfy           skip ntfy send (dashboard/state still written)
#   --dry-run           compute only, do not modify dashboard or send ntfy

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT/queue/reports"
STATE_FILE="$ROOT/logs/hotfix_trend_state.json"
DASHBOARD="$ROOT/dashboard.md"
THRESHOLD=3
JACCARD=0.5
INCLUDE_CMEM=0
DRY_RUN=0
NO_NTFY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --reports-dir) REPORTS_DIR="$2"; shift 2 ;;
    --state-file)  STATE_FILE="$2"; shift 2 ;;
    --dashboard)   DASHBOARD="$2"; shift 2 ;;
    --threshold)   THRESHOLD="$2"; shift 2 ;;
    --jaccard)     JACCARD="$2"; shift 2 ;;
    --include-cmem) INCLUDE_CMEM=1; shift ;;
    --no-ntfy)     NO_NTFY=1; shift ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -h|--help)
      sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$(dirname "$STATE_FILE")"
[ -f "$STATE_FILE" ] || echo '{"notified":[]}' > "$STATE_FILE"

# --- Collect hotfix_notes.what_was_wrong blocks from reports ---
# Output: one JSON object per line: {"src": "path", "text": "..."}
HOTFIX_JSON=$(python3 - "$REPORTS_DIR" <<'PY'
import sys, os, json, re, glob

reports_dir = sys.argv[1]
pattern = os.path.join(reports_dir, "ashigaru*_report_*.yaml")
results = []

# Very small YAML-ish extractor. We only care about hotfix_notes blocks.
# Match 'hotfix_notes:' (not 'hotfix_notes: null' and not followed by '~').
for path in sorted(glob.glob(pattern)):
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
    except Exception:
        continue
    m = re.search(r"(?m)^hotfix_notes:\s*$", src)
    if not m:
        continue
    start = m.end()
    # Read indented block until a non-indented line or EOF.
    lines = src[start:].splitlines()
    block = []
    for ln in lines:
        if ln == "" or ln.startswith(" ") or ln.startswith("\t"):
            block.append(ln)
        else:
            break
    body = "\n".join(block)
    # Capture what_was_wrong (plain string or '|' block).
    mw = re.search(r"(?m)^\s{2,}what_was_wrong:\s*(?:\|\s*\n((?:\s{2,}.*\n?)+)|\"([^\"]*)\"|'([^']*)'|(.+))", body)
    if not mw:
        # Fall back to entire block text.
        txt = body.strip()
    else:
        txt = next((g for g in mw.groups() if g), "").strip()
    if not txt or txt.lower() in ("null", "~"):
        continue
    results.append({"src": path, "text": txt})

for r in results:
    sys.stdout.write(json.dumps(r, ensure_ascii=False) + "\n")
PY
)

# --- Optional: append claude-mem hotfix hits as pseudo-records (best-effort) ---
if [ "$INCLUDE_CMEM" -eq 1 ]; then
  CMEM_TXT=$(bash "$ROOT/scripts/cmem_search.sh" "hotfix_notes" 20 2>/dev/null || true)
  if [ -n "$CMEM_TXT" ]; then
    EXTRA=$(printf '%s' "$CMEM_TXT" | python3 - <<'PY'
import sys, json, re
raw = sys.stdin.read()
# Split on blank lines; keep chunks that mention hotfix.
chunks = [c.strip() for c in re.split(r"\n\s*\n", raw) if c.strip()]
for i, c in enumerate(chunks):
    if "hotfix" in c.lower() or "ワークアラウンド" in c or "場当たり" in c:
        sys.stdout.write(json.dumps({"src": f"cmem:{i}", "text": c}, ensure_ascii=False) + "\n")
PY
)
    HOTFIX_JSON="$HOTFIX_JSON
$EXTRA"
  fi
fi

if [ -z "$(printf '%s' "$HOTFIX_JSON" | sed '/^$/d')" ]; then
  echo "[hotfix_trend] no hotfix_notes found in $REPORTS_DIR" >&2
  exit 0
fi

# --- Cluster + decide which clusters to notify. ---
# Python does the clustering + dedup against state file + emits actions.
RECS_FILE=$(mktemp)
printf '%s\n' "$HOTFIX_JSON" > "$RECS_FILE"
ACTIONS=$(python3 - "$STATE_FILE" "$THRESHOLD" "$JACCARD" "$RECS_FILE" <<'PY'
import sys, os, json, re, hashlib

state_path = sys.argv[1]
threshold = int(sys.argv[2])
jaccard_th = float(sys.argv[3])
recs_path = sys.argv[4]

records = []
with open(recs_path, encoding="utf-8") as rf:
    for line in rf:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

STOP = set("""
the a an and or of to in on at with for from by is are was were be been being this that these those it its as into not no but if then than so do does did done have has had will would should could may might must can cannot
""".split())

PATH_RE = re.compile(r"[A-Za-z0-9_./\-]+\.(?:sh|py|js|ts|yaml|yml|md|json)")
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
JP_RE = re.compile(r"[一-鿿぀-ヿ]{2,}")

def featurize(text):
    t = text.lower()
    paths = set(PATH_RE.findall(text))
    tokens = {w for w in TOKEN_RE.findall(t) if w not in STOP and len(w) >= 3}
    jp = set(JP_RE.findall(text))
    return paths, tokens | jp

def jaccard(a, b):
    if not a and not b:
        return 0.0
    u = a | b
    return len(a & b) / len(u) if u else 0.0

# Featurize.
feats = [featurize(r["text"]) for r in records]

# Union-find clustering.
n = len(records)
parent = list(range(n))
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb

for i in range(n):
    for j in range(i+1, n):
        pi, ti = feats[i]
        pj, tj = feats[j]
        shared_path = bool(pi & pj)
        sim = jaccard(ti, tj)
        if shared_path or sim >= jaccard_th:
            union(i, j)

clusters = {}
for i in range(n):
    clusters.setdefault(find(i), []).append(i)

# Build signatures (stable): sorted shared tokens + shared paths; hashed.
def signature(indices):
    shared_paths = set.intersection(*(feats[i][0] for i in indices)) if indices else set()
    shared_tokens = set.intersection(*(feats[i][1] for i in indices)) if indices else set()
    key_items = sorted(shared_paths) + sorted(shared_tokens)
    if not key_items:
        # Fall back to union of first-record features (weaker signature).
        key_items = sorted(feats[indices[0]][0] | feats[indices[0]][1])[:5]
    key = "|".join(key_items[:10])
    sig = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    return sig, shared_paths, shared_tokens, key_items[:5]

# Load state.
try:
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
except Exception:
    state = {"notified": []}
notified = set(state.get("notified", []))

actions = []
for root, members in clusters.items():
    if len(members) < threshold:
        continue
    sig, sp, st, key_items = signature(members)
    if sig in notified:
        continue
    samples = [records[i] for i in members[:3]]
    actions.append({
        "signature": sig,
        "hits": len(members),
        "shared_paths": sorted(sp),
        "shared_tokens": sorted(st)[:5],
        "key_preview": key_items,
        "samples": samples,
    })

json.dump({"actions": actions, "state_prev": sorted(notified)}, sys.stdout, ensure_ascii=False)
PY
)
rm -f "$RECS_FILE"

# Parse ACTIONS and decide on side effects.
ACTION_COUNT=$(printf '%s' "$ACTIONS" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)["actions"]))')

if [ "$ACTION_COUNT" = "0" ]; then
  echo "[hotfix_trend] no new clusters >= threshold=$THRESHOLD" >&2
  exit 0
fi

echo "[hotfix_trend] new clusters to notify: $ACTION_COUNT" >&2

# Build dashboard insertion and ntfy messages.
TMP=$(mktemp)
printf '%s' "$ACTIONS" > "$TMP"

# Write human-readable summary for logs/stderr.
python3 - "$TMP" <<'PY' >&2
import sys, json
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
for a in data["actions"]:
    srcs = ", ".join(s["src"].rsplit("/", 1)[-1] for s in a["samples"])
    print(f"  - sig={a['signature']} hits={a['hits']} paths={a['shared_paths']} preview={a['key_preview']} samples=[{srcs}]")
PY

if [ "$DRY_RUN" -eq 1 ]; then
  echo "[hotfix_trend] dry-run: no writes" >&2
  rm -f "$TMP"
  exit 0
fi

# --- Update dashboard.md under the スキル化候補 heading ---
python3 - "$TMP" "$DASHBOARD" <<'PY'
import sys, json, datetime, re, os
actions_file, dash_path = sys.argv[1], sys.argv[2]
with open(actions_file, encoding="utf-8") as f:
    data = json.load(f)
if not os.path.exists(dash_path):
    sys.exit(0)
with open(dash_path, encoding="utf-8") as f:
    src = f.read()
heading = "### 🚨 スキル化候補（殿承認要）"
idx = src.find(heading)
if idx < 0:
    # Append new section at end if missing.
    src = src.rstrip() + "\n\n" + heading + "\n"
    idx = src.find(heading)
end_of_heading_line = src.find("\n", idx) + 1
today = datetime.date.today().isoformat()
new_lines = []
for a in data["actions"]:
    preview = ", ".join(a["key_preview"]) or "(no-key)"
    paths = ", ".join(a["shared_paths"]) if a["shared_paths"] else "—"
    line = (f"- **auto-hotfix-{a['signature']}**: hotfix {a['hits']}回検出 "
            f"(共通パス: {paths} / キー: {preview}) "
            f"→ skill化検討 [{today}] "
            f"<!-- auto-hotfix-trend: {a['signature']} -->")
    if f"auto-hotfix-trend: {a['signature']}" in src:
        continue  # already present (belt-and-suspenders vs state file)
    new_lines.append(line)
if not new_lines:
    sys.exit(0)
insertion = "".join(l + "\n" for l in new_lines)
updated = src[:end_of_heading_line] + insertion + src[end_of_heading_line:]
with open(dash_path, "w", encoding="utf-8") as f:
    f.write(updated)
print(f"[hotfix_trend] dashboard.md updated (+{len(new_lines)} entries)", file=sys.stderr)
PY

# --- Send ntfy per new cluster ---
MSGS=$(python3 - "$TMP" <<'PY'
import sys, json
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
for a in data["actions"]:
    preview = ",".join(a["key_preview"][:3]) or "(no-key)"
    print(f"🔧 hotfix {a['hits']}回検出 sig={a['signature']}: {preview} → skill化候補(dashboard.md追記)")
PY
)
if [ "$NO_NTFY" -eq 0 ]; then
  while IFS= read -r msg; do
    [ -n "$msg" ] && bash "$ROOT/scripts/ntfy.sh" "$msg" || true
  done <<< "$MSGS"
else
  echo "[hotfix_trend] --no-ntfy set; skipping ntfy" >&2
fi

# --- Update state file (append new signatures) ---
python3 - "$TMP" "$STATE_FILE" <<'PY'
import sys, json, datetime
actions_file, state_path = sys.argv[1], sys.argv[2]
with open(actions_file, encoding="utf-8") as f:
    data = json.load(f)
try:
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
except Exception:
    state = {"notified": []}
existing = set(state.get("notified", []))
history = state.get("history", [])
for a in data["actions"]:
    existing.add(a["signature"])
    history.append({"signature": a["signature"], "hits": a["hits"], "at": datetime.datetime.now().isoformat(timespec="seconds")})
state["notified"] = sorted(existing)
state["history"] = history[-200:]
with open(state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
PY

rm -f "$TMP"
echo "[hotfix_trend] done" >&2
