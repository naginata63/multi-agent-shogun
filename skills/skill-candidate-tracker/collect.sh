#!/usr/bin/env bash
# skill-candidate-tracker / collect.sh
# cmd_1447: queue/reports/*.yaml を走査し skill_candidate.found=true を抽出→
# context/skill_candidates_inventory.md にマークダウン table 生成
#
# 設計原則:
#   - 新規 .py ファイル作成禁止 (cmd_1447 共通ルール)。python3 は HEREDOC のみ
#   - skill_candidate は nested object / 旧形式 bare のどちらも許容
#   - 同名 skill_name は初出日=min / 最終言及日=max / evidence は複数集約 (dedup)
#   - skills/<name>/ 実在で IMPLEMENTED 判定 (cmd_1447 殿承認根拠の「継続改善」)
#
# Usage:
#   bash collect.sh            # = --write (default)
#   bash collect.sh --write    # context/skill_candidates_inventory.md に書き出す
#   bash collect.sh --dry-run  # stdout のみ (inventory 上書きしない)
#   bash collect.sh --no-ntfy  # ntfy 通知を抑制 (手動実行時推奨)
#
# Cron: shared_context/cron_inventory.md C14 参照

set -u

MODE="write"
NO_NTFY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) MODE="dry-run" ;;
    --write)   MODE="write" ;;
    --no-ntfy) NO_NTFY=1 ;;
  esac
done

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/queue/reports"
SKILLS_DIR="$PROJECT_ROOT/skills"
INVENTORY="$PROJECT_ROOT/context/skill_candidates_inventory.md"
STATE_FILE="$PROJECT_ROOT/logs/skill_inventory_state.json"
LOG_FILE="$PROJECT_ROOT/logs/skill_inventory.log"
NTFY_SCRIPT="$PROJECT_ROOT/scripts/ntfy.sh"

mkdir -p "$(dirname "$LOG_FILE")" "$(dirname "$INVENTORY")"

TIMESTAMP=$(date '+%Y-%m-%dT%H:%M:%S')
echo "[$TIMESTAMP] collect start mode=$MODE" >> "$LOG_FILE"

export REPORTS_DIR SKILLS_DIR

# ---- YAML 走査 → JSON 出力 (HEREDOC 方式・bash quote escape 不要) ----
OUTPUT_JSON=$(python3 <<'PYEOF'
import os, sys, json, glob, re
from datetime import datetime, date, timedelta

try:
    import yaml
except ImportError:
    print(json.dumps({"error": "PyYAML not installed"}))
    sys.exit(0)

reports_dir = os.environ["REPORTS_DIR"]
skills_dir = os.environ["SKILLS_DIR"]

existing = set()
try:
    for e in os.listdir(skills_dir):
        existing.add(e)
except FileNotFoundError:
    pass

agg = {}

for path in sorted(glob.glob(os.path.join(reports_dir, "*.yaml"))):
    fname = os.path.basename(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        continue
    if not isinstance(data, dict):
        continue
    sc = data.get("skill_candidate")
    if not isinstance(sc, dict):
        continue
    if sc.get("found") is not True:
        continue

    m = re.search(r"(subtask_\w+|cmd\w+|qc_\w+)", fname)
    cmd_id = m.group(1) if m else fname.replace("_report", "").replace(".yaml", "")

    ag = "unknown"
    am = re.match(r"(ashigaru\d+|gunshi|karo|shogun)", fname)
    if am:
        ag = am.group(1)

    name = sc.get("name")
    desc = sc.get("description") or sc.get("pattern") or sc.get("benefit") or ""
    if not isinstance(desc, str):
        desc = str(desc)
    desc = desc.strip().replace("\n", " ")
    purpose = desc[:120]

    ts = data.get("timestamp") or data.get("completed_at")
    if isinstance(ts, str) and ts:
        seen = ts[:10]
    else:
        seen = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")

    if name and name in existing:
        status = "IMPLEMENTED"
    elif name:
        status = "PENDING"
    else:
        status = "NAMELESS"

    key = name if name else "(nameless):" + cmd_id
    rec = agg.get(key)
    if rec is None:
        agg[key] = {
            "skill_name": name or "(nameless)",
            "purpose": purpose,
            "status": status,
            "first_seen": seen,
            "last_seen": seen,
            "evidence": [{"cmd_id": cmd_id, "agent": ag, "file": fname, "seen": seen}],
            "mention_count": 1,
        }
    else:
        rec["first_seen"] = min(rec["first_seen"], seen)
        rec["last_seen"] = max(rec["last_seen"], seen)
        rec["evidence"].append({"cmd_id": cmd_id, "agent": ag, "file": fname, "seen": seen})
        rec["mention_count"] += 1
        prio = {"IMPLEMENTED": 3, "PENDING": 2, "NAMELESS": 1}
        if prio.get(status, 0) > prio.get(rec["status"], 0):
            rec["status"] = status
        if len(purpose) > len(rec["purpose"]):
            rec["purpose"] = purpose

def sort_key(r):
    prio = {"PENDING": 0, "NAMELESS": 1, "IMPLEMENTED": 2}
    return (prio[r["status"]], -int(r["last_seen"].replace("-", "")))
rows = sorted(agg.values(), key=sort_key)

cutoff = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
summary = {
    "total": len(rows),
    "pending": sum(1 for r in rows if r["status"] == "PENDING"),
    "implemented": sum(1 for r in rows if r["status"] == "IMPLEMENTED"),
    "nameless": sum(1 for r in rows if r["status"] == "NAMELESS"),
    "multi_mention": sum(1 for r in rows if r["mention_count"] >= 2),
    "recent_7d": sum(1 for r in rows if r["first_seen"] >= cutoff),
    "cutoff_7d": cutoff,
}

print(json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False))
PYEOF
)

# 抽出エラーチェック
if [ -z "$OUTPUT_JSON" ] || echo "$OUTPUT_JSON" | grep -q '"error"'; then
  echo "[$TIMESTAMP] ERROR: python extraction failed: $OUTPUT_JSON" >> "$LOG_FILE"
  echo "FATAL: extraction failed: $OUTPUT_JSON" 1>&2
  exit 1
fi

# ---- Markdown 生成 (HEREDOC + env var JSON) ----
# heredoc は python の stdin を占有するので JSON は env var で渡す
export GENERATED_AT="$TIMESTAMP"
export OUTPUT_JSON
MD_CONTENT=$(python3 <<'PYEOF'
import os, json, sys
data = json.loads(os.environ["OUTPUT_JSON"])
rows = data["rows"]
s = data["summary"]
gen = os.environ["GENERATED_AT"]

lines = []
lines.append("# Skill Candidates Inventory (自動棚卸し)")
lines.append("")
lines.append("**最終更新**: " + gen + " / skill-candidate-tracker (cmd_1447)")
lines.append("")
lines.append("`queue/reports/*.yaml` の `skill_candidate.found=true` を横断抽出した一覧。")
lines.append("同名候補は初出/最終言及日で集約。Python/PyYAML でパース (旧形式 bare + 新形式 nested 両対応)。")
lines.append("")
lines.append("## サマリー")
lines.append("")
lines.append("- 総候補数: **" + str(s["total"]) + "**")
lines.append("- 🚨 PENDING (未スキル化): **" + str(s["pending"]) + "**")
lines.append("- ✅ IMPLEMENTED (スキル化済): **" + str(s["implemented"]) + "**")
lines.append("- 🟡 NAMELESS (旧形式・name欠落): **" + str(s["nameless"]) + "**")
lines.append("- 🔁 2回以上言及 (ashigaru.md skill化基準クリア): **" + str(s["multi_mention"]) + "**")
lines.append("- 🆕 直近7日以内初出 (cutoff=" + s["cutoff_7d"] + "): **" + str(s["recent_7d"]) + "**")
lines.append("")
lines.append("## 候補一覧 (PENDING 先頭・last_seen 降順)")
lines.append("")
lines.append("| # | skill_name | status | mentions | first_seen | last_seen | purpose | evidence |")
lines.append("|---|-----------|--------|----------|-----------|----------|---------|----------|")
badge_map = {"PENDING": "🚨", "NAMELESS": "🟡", "IMPLEMENTED": "✅"}
for i, r in enumerate(rows, 1):
    badge = badge_map.get(r["status"], "?")
    ev = r["evidence"][:3]
    ev_list = ", ".join(e["cmd_id"] + "(" + e["agent"] + ")" for e in ev)
    if len(r["evidence"]) > 3:
        ev_list = ev_list + " +" + str(len(r["evidence"]) - 3) + "件"
    purpose = r["purpose"].replace("|", "\\|").replace("\n", " ")
    skill_name = r["skill_name"].replace("|", "\\|")
    lines.append("| " + str(i) + " | `" + skill_name + "` | " + badge + " " + r["status"]
                 + " | " + str(r["mention_count"]) + " | " + r["first_seen"] + " | "
                 + r["last_seen"] + " | " + purpose + " | " + ev_list + " |")
lines.append("")
lines.append("## 🔁 2回以上言及された候補 (skill化基準クリア)")
lines.append("")
multi = [r for r in rows if r["mention_count"] >= 2]
if multi:
    for r in multi:
        lines.append("- **`" + r["skill_name"] + "`** (" + r["status"] + ", "
                     + str(r["mention_count"]) + "回) — " + r["purpose"])
else:
    lines.append("_(なし)_")
lines.append("")
lines.append("## 🆕 直近7日以内 初出候補 (軍師 quarterly review 観察対象)")
lines.append("")
recent = [r for r in rows if r["first_seen"] >= s["cutoff_7d"]]
if recent:
    for r in recent:
        lines.append("- **`" + r["skill_name"] + "`** (" + r["status"]
                     + ") — first_seen=" + r["first_seen"])
else:
    lines.append("_(なし)_")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 運用")
lines.append("")
lines.append("- **weekly cron**: `shared_context/cron_inventory.md` C14 参照 (毎週日曜深夜)")
lines.append("- **即時再生成**: `/skill-inventory` slash command または `bash skills/skill-candidate-tracker/collect.sh --write`")
lines.append("- **判定ロジック**: `skills/<name>/` 実在で IMPLEMENTED。なければ PENDING。name 欠落の旧形式 → NAMELESS (軍師レビューで name 付与 or 見送り判断)")
lines.append("")
sys.stdout.write("\n".join(lines) + "\n")
PYEOF
)

if [ -z "$MD_CONTENT" ]; then
  echo "[$TIMESTAMP] ERROR: markdown generation empty" >> "$LOG_FILE"
  echo "FATAL: markdown generation failed" 1>&2
  exit 1
fi

if [ "$MODE" = "dry-run" ]; then
  printf "%s" "$MD_CONTENT"
  echo "[$TIMESTAMP] dry-run complete" >> "$LOG_FILE"
  exit 0
fi

# write モード
printf "%s" "$MD_CONTENT" > "$INVENTORY"
LINES_WRITTEN=$(wc -l < "$INVENTORY")
echo "[$TIMESTAMP] wrote $INVENTORY ($LINES_WRITTEN lines)" >> "$LOG_FILE"

# ---- 差分検知 & ntfy ----
CURRENT_PENDING=$(printf '%s' "$OUTPUT_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['summary']['pending'])")
PREV_PENDING=0
if [ -f "$STATE_FILE" ]; then
  PREV_PENDING=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d.get('pending',0))" 2>/dev/null || echo 0)
fi

NEW_PENDING=0
if [ "$CURRENT_PENDING" -gt "$PREV_PENDING" ]; then
  NEW_PENDING=$((CURRENT_PENDING - PREV_PENDING))
fi

# state 更新
printf '%s' "$OUTPUT_JSON" | python3 -c "
import json, sys, os
d = json.load(sys.stdin)
out = {'pending': d['summary']['pending'], 'total': d['summary']['total'], 'generated_at': os.environ.get('GENERATED_AT','')}
open('$STATE_FILE','w').write(json.dumps(out, ensure_ascii=False))
" 2>/dev/null || true

if [ "$NO_NTFY" -eq 0 ] && [ "$NEW_PENDING" -gt 0 ] && [ -x "$NTFY_SCRIPT" ]; then
  MSG="🧰 skill化候補 新規${NEW_PENDING}件検出 (PENDING計${CURRENT_PENDING}件)。context/skill_candidates_inventory.md 参照。"
  bash "$NTFY_SCRIPT" "$MSG" >/dev/null 2>&1 || echo "[$TIMESTAMP] ntfy failed" >> "$LOG_FILE"
fi

echo "[$TIMESTAMP] done pending=$CURRENT_PENDING new=$NEW_PENDING" >> "$LOG_FILE"
echo "✅ generated: $INVENTORY (PENDING=$CURRENT_PENDING / new=$NEW_PENDING)"
