#!/usr/bin/env bash
# ntfy_voice.sh — VOICEVOXずんだもんで音声合成 → スピーカー再生
# 引数: 読み上げるテキスト
# バックグラウンド実行前提（ntfy.sh から & で呼ばれる）

set -euo pipefail

VOICEVOX_HOST="${VOICEVOX_HOST:-localhost}"
VOICEVOX_PORT="${VOICEVOX_PORT:-50021}"
VOICEVOX_BASE="http://${VOICEVOX_HOST}:${VOICEVOX_PORT}"

TEXT="${1:-}"
if [ -z "$TEXT" ]; then
  echo "usage: ntfy_voice.sh <text>" >&2
  exit 1
fi

# ずんだもん ノーマル のspeaker_id（VOICEVOX標準）
# 起動時に /speakers で確認して上書き可能
SPEAKER_ID=3

# VOICEVOXコンテナを起動（必要時のみ起動・使用後即停止でGPU占有防止）
VOICEVOX_STARTED=0
if ! curl -sf --max-time 2 "${VOICEVOX_BASE}/version" > /dev/null 2>&1; then
  echo "ntfy_voice: starting VOICEVOX container..." >&2
  if ! docker start voicevox > /dev/null 2>&1; then
    echo "ntfy_voice: docker start failed, skip" >&2
    exit 0
  fi
  VOICEVOX_STARTED=1
  # 起動待ち（最大15秒）
  for i in $(seq 1 15); do
    if curl -sf --max-time 2 "${VOICEVOX_BASE}/version" > /dev/null 2>&1; then
      break
    fi
    sleep 1
    if [ "$i" -eq 15 ]; then
      echo "ntfy_voice: VOICEVOX startup timeout, stopping container" >&2
      docker stop voicevox > /dev/null 2>&1 || true
      exit 0
    fi
  done
fi

# 終了時（正常・異常どちらでも）VOICEVOXを停止
cleanup_voicevox() {
  if [ "$VOICEVOX_STARTED" -eq 1 ]; then
    docker stop voicevox > /dev/null 2>&1 || true
    echo "ntfy_voice: VOICEVOX container stopped" >&2
  fi
}
trap cleanup_voicevox EXIT

# 読み替え辞書を適用（config/voicevox_dict.txt）
DICT_FILE="$(cd "$(dirname "$0")/.." && pwd)/config/voicevox_dict.txt"
if [ -f "$DICT_FILE" ]; then
  while IFS= read -r line; do
    # コメント行・空行をスキップ
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    word="${line%%=*}"
    reading="${line#*=}"
    TEXT="${TEXT//$word/$reading}"
  done < "$DICT_FILE"
fi

# 日本語テキストをURLエンコード
ENCODED_TEXT=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$TEXT")

# Step 1: audio_query取得
AUDIO_QUERY=$(curl -sf --max-time 10 \
  -X POST \
  "${VOICEVOX_BASE}/audio_query?text=${ENCODED_TEXT}&speaker=${SPEAKER_ID}" \
  -H "Content-Type: application/json") || {
  echo "ntfy_voice: audio_query failed" >&2
  exit 0
}

# Step 2: 音声合成
# /tmp使用: 再生後即削除（L~100: rm -f）するため中間成果物ルールの例外として許容
WAV_FILE=$(mktemp /tmp/ntfy_voice_XXXXXX.wav)
curl -sf --max-time 30 \
  -X POST \
  "${VOICEVOX_BASE}/synthesis?speaker=${SPEAKER_ID}" \
  -H "Content-Type: application/json" \
  -d "$AUDIO_QUERY" \
  -o "$WAV_FILE" || {
  echo "ntfy_voice: synthesis failed" >&2
  rm -f "$WAV_FILE"
  exit 0
}

# Step 3: 再生（aplay優先、なければpw-play）
if command -v aplay > /dev/null 2>&1; then
  aplay -q "$WAV_FILE" 2>/dev/null || true
elif command -v pw-play > /dev/null 2>&1; then
  pw-play "$WAV_FILE" 2>/dev/null || true
else
  echo "ntfy_voice: no audio player found (aplay/pw-play)" >&2
fi

rm -f "$WAV_FILE"
