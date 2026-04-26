#!/bin/bash
# claude_mem_hook_guard.sh (cmd_1495)
# claude-mem plugin が upgrade されると hooks.json が上書きされ shogun フィルタが消える。
# このスクリプトが SessionStart の context-inject hook に shogun-only フィルタを再適用する。
# 冪等: 既にフィルタ済なら NOOP。
# 実行: cron daily (or 必要時手動)。

set -u
LOG=/home/murakami/multi-agent-shogun/logs/claude_mem_hook_guard.log
PYTHON=/usr/bin/python3
NOW=$(date '+%Y-%m-%dT%H:%M:%S%z')

"$PYTHON" - <<'PYEOF' >> "$LOG" 2>&1
import json, os, sys, glob, shutil, datetime

NOW = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
PLUGIN_ROOT = os.path.expanduser("~/.claude/plugins/cache/thedotmack/claude-mem")
hooks_paths = sorted(glob.glob(os.path.join(PLUGIN_ROOT, "*", "hooks", "hooks.json")))

if not hooks_paths:
    print(f"[{NOW}] no claude-mem hooks.json found under {PLUGIN_ROOT}")
    sys.exit(0)

FILTER_PREFIX = (
    'AID=$(tmux display-message -t "$TMUX_PANE" -p \'#{@agent_id}\' 2>/dev/null); '
    '[ "$AID" = "shogun" ] || exit 0; '
)

patched_any = False
for hpath in hooks_paths:
    try:
        with open(hpath, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[{NOW}] FAIL parse {hpath}: {e}")
        continue

    target = None
    ss_list = data.get("hooks", {}).get("SessionStart", [])
    for entry in ss_list:
        for h in entry.get("hooks", []):
            cmd = h.get("command", "")
            # context-inject hook = "worker-service.cjs hook claude-code context" を含むもの
            if "hook claude-code context" in cmd and 'AID=' not in cmd:
                target = h
                break
        if target is not None:
            break

    if target is None:
        # 既にパッチ済 or 該当 hook 不在 → skip
        continue

    bak = f"{hpath}.bak_{NOW}"
    shutil.copy2(hpath, bak)
    target["command"] = FILTER_PREFIX + target["command"]
    with open(hpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[{NOW}] PATCHED {hpath} (backup: {os.path.basename(bak)})")
    patched_any = True

if patched_any:
    # ntfy 通知 (殿に upgrade 検知を知らせる)
    ntfy_path = "/home/murakami/multi-agent-shogun/scripts/ntfy.sh"
    if os.path.exists(ntfy_path) and os.access(ntfy_path, os.X_OK):
        os.system(f'"{ntfy_path}" "🛡️ claude-mem hook guard: shogun フィルタ再適用済 (plugin upgrade 検知)"')
else:
    print(f"[{NOW}] all hooks.json already filtered — NOOP")
PYEOF
