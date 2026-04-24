#!/usr/bin/env bash
#
# slim_yaml_all.sh - Run slim_yaml.sh for all agents, tolerating per-agent failures.
#
# Replaces the 9x `&&` chain in crontab. The chain stops on first failure,
# leaving the rest of the agents un-slimmed (drift risk). This wrapper runs
# every agent and logs failures but continues, so one agent's lock timeout
# or parse error does not suppress slimming for the other 8.
#
# Usage: bash slim_yaml_all.sh [--dry-run] [agent ...]
#
# Exit: 0 if every agent succeeded, 1 if any failed (but all were attempted).
#

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SLIM="${SLIM_YAML_BIN:-${SCRIPT_DIR}/slim_yaml.sh}"

# Default agents: karo + ashigaru1..7 + gunshi
DEFAULT_AGENTS=(karo ashigaru1 ashigaru2 ashigaru3 ashigaru4 ashigaru5 ashigaru6 ashigaru7 gunshi)

DRY_RUN=""
AGENTS=()

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN="--dry-run" ;;
    *) AGENTS+=("$arg") ;;
  esac
done

if [ ${#AGENTS[@]} -eq 0 ]; then
  AGENTS=("${DEFAULT_AGENTS[@]}")
fi

ts() { date '+%Y-%m-%dT%H:%M:%S'; }

fail_count=0
fail_list=()

for agent in "${AGENTS[@]}"; do
  if bash "$SLIM" "$agent" $DRY_RUN; then
    echo "[$(ts)] slim_yaml_all: $agent OK"
  else
    rc=$?
    fail_count=$((fail_count + 1))
    fail_list+=("$agent (exit=$rc)")
    echo "[$(ts)] slim_yaml_all: $agent FAIL (exit=$rc) — continuing" >&2
  fi
done

if [ "$fail_count" -gt 0 ]; then
  echo "[$(ts)] slim_yaml_all: ${fail_count} agent(s) failed: ${fail_list[*]}" >&2
  exit 1
fi

echo "[$(ts)] slim_yaml_all: all ${#AGENTS[@]} agents OK"
exit 0
