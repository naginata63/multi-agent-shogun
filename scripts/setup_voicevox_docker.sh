#!/usr/bin/env bash
# setup_voicevox_docker.sh — VOICEVOXエンジンをDockerで起動
# 初回のみ実行。以降は --restart unless-stopped で自動起動。

set -euo pipefail

CONTAINER_NAME="voicevox"
PORT=50021

echo "=== VOICEVOX Docker セットアップ ==="

# Dockerがインストールされていなければインストール
if ! command -v docker > /dev/null 2>&1; then
  echo "[1/4] Docker インストール中..."
  sudo apt-get update -q
  sudo apt-get install -y docker.io
  sudo systemctl enable --now docker
  sudo usermod -aG docker "$USER"
  echo "  ※ Dockerグループ追加済み。次回ログイン後から sudo なし実行可能"
  DOCKER_CMD="sudo docker"
else
  DOCKER_CMD="docker"
  echo "[1/4] Docker 検出済み: $(docker --version)"
fi

# 既存コンテナ確認
if $DOCKER_CMD ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "[2/4] 既存コンテナ '${CONTAINER_NAME}' 起動中..."
  $DOCKER_CMD start "$CONTAINER_NAME" 2>/dev/null || true
else
  echo "[2/4] VOICEVOXイメージ Pull中（GPU版を試みる）..."
  # GPU版を試みる
  if $DOCKER_CMD pull voicevox/voicevox_engine:nvidia-latest 2>/dev/null; then
    IMAGE="voicevox/voicevox_engine:nvidia-latest"
    GPU_OPT="--gpus all"
    echo "  GPU版を使用"
  else
    echo "  GPU版失敗、CPU版を使用"
    $DOCKER_CMD pull voicevox/voicevox_engine:latest
    IMAGE="voicevox/voicevox_engine:latest"
    GPU_OPT=""
  fi

  echo "[3/4] コンテナ起動..."
  # shellcheck disable=SC2086
  $DOCKER_CMD run -d \
    --name "$CONTAINER_NAME" \
    -p "${PORT}:50021" \
    --restart unless-stopped \
    $GPU_OPT \
    "$IMAGE"
fi

echo "[4/4] 起動確認中（最大30秒待機）..."
for i in $(seq 1 30); do
  if curl -sf --max-time 2 "http://localhost:${PORT}/version" > /dev/null 2>&1; then
    VERSION=$(curl -sf "http://localhost:${PORT}/version")
    echo "  VOICEVOX起動確認 ✓ version=${VERSION}"
    break
  fi
  sleep 1
  echo "  待機中 ${i}/30..."
done

echo ""
echo "=== ずんだもん speaker_id 確認 ==="
curl -sf "http://localhost:${PORT}/speakers" | python3 -c "
import json, sys
speakers = json.load(sys.stdin)
for s in speakers:
    if 'ずんだもん' in s.get('name', ''):
        print(f\"  {s['name']}: styles={[(st['name'], st['id']) for st in s['styles']]}\")
" 2>/dev/null || echo "  (確認失敗 — VOICEVOXが起動していない可能性)"

echo ""
echo "セットアップ完了。"
echo "テスト: bash scripts/ntfy_voice.sh 'cmd完了でござる'"
