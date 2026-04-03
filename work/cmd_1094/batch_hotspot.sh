#!/bin/bash
# Batch hotspot analysis for cmd_1094
set -euo pipefail

IDS=(
  -RZeHghiHTU 1-wNVCanUr0 35_iOmq8Q6A 5M5zp9TpbeA 6bTuqQqh6tM
  CyUoLI8QIio DJ_NmrIiB78 MiIMDF1YhEw SpzhnPqvn0g YVl-IcJlers
  YXxLXD6oUDE _sVuKf5Zu4A dJYydg0-ghY dV-8e6LQwXw eYEm10gIpXs
  erSyK15GFNQ g8R5UtRw6XA gmA_sg6b2H8 hRe82RR5Rmo j6AwMRYD_9A
  j_KVuabNrFg n-wtokssJJs nW8YR_7XUQQ oGm0Xk3DV1U ooc2McMaLHY
  p-oSdBIUdts pla8j_sLe7Y qr0ghdRSIIA uGSZ0TwLjOw wf49a7kUU2A
  y-qxrXenOqY
)

SUCCESS=0
SKIP=0
FAIL=0
FAILED_IDS=""

for id in "${IDS[@]}"; do
  OUTFILE="work/hotspot_${id}.json"
  if [ -f "$OUTFILE" ]; then
    echo "[SKIP] $id — already exists"
    SKIP=$((SKIP + 1))
    continue
  fi

  echo "=== Processing: $id ==="
  if python3 scripts/comment_hotspot.py --top 10 --output "$OUTFILE" -- "$id" 2>&1; then
    if [ -f "$OUTFILE" ]; then
      echo "[OK] $id → $OUTFILE"
      SUCCESS=$((SUCCESS + 1))
    else
      echo "[EMPTY] $id — no timestamp comments, creating empty marker"
      echo '{"video_id":"'"$id"'","hotspots":[],"note":"no_timestamp_comments"}' > "$OUTFILE"
      SUCCESS=$((SUCCESS + 1))
    fi
  else
    echo "[FAIL] $id — error, creating empty marker"
    echo '{"video_id":"'"$id"'","hotspots":[],"note":"processing_error"}' > "$OUTFILE"
    FAIL=$((FAIL + 1))
    FAILED_IDS="$FAILED_IDS $id"
  fi
  echo ""
done

echo "========================================="
echo "Batch complete: SUCCESS=$SUCCESS SKIP=$SKIP FAIL=$FAIL"
if [ -n "$FAILED_IDS" ]; then
  echo "Failed IDs:$FAILED_IDS"
fi
echo "========================================="
