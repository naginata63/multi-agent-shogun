#!/usr/bin/env bash
# GLM足軽用Claude Code起動スクリプト（OAuth衝突対策済み）
# 用途: ashigaru1をZ.AI GLM-5.1で起動する。別HOMEでOAuth衝突を回避。
# 参考: work/cmd_1053/batch4_findings.md（記事074/088）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GLM_HOME="/home/murakami/.claude_glm"
API_KEY_FILE="$PROJECT_ROOT/config/glm_api_key.env"
SETTINGS_FILE="$GLM_HOME/.claude/settings.json"

if [[ ! -f "$API_KEY_FILE" ]]; then
    echo "[ERROR] $API_KEY_FILE が存在しない。Z.AIアカウント作成後にAPIキーを設定せよ。" >&2
    echo "[INFO]  形式: ZAI_API_KEY=your_key_here" >&2
    exit 1
fi

# shellcheck source=/dev/null
source "$API_KEY_FILE"

if [[ -z "$ZAI_API_KEY" ]]; then
    echo "[ERROR] ZAI_API_KEY が空。$API_KEY_FILE を確認せよ。" >&2
    exit 1
fi

# GLM HOME用.claudeディレクトリ作成
mkdir -p "$GLM_HOME/.claude"

# ADC認証ファイルを通常HOMEからコピー（Vertex AI用）
MAIN_ADC="/home/murakami/.config/gcloud/application_default_credentials.json"
GLM_ADC="$GLM_HOME/.config/gcloud/application_default_credentials.json"
if [[ -f "$MAIN_ADC" ]]; then
    mkdir -p "$GLM_HOME/.config/gcloud"
    cp "$MAIN_ADC" "$GLM_ADC"
fi

# settings.jsonにAPIキーを書き込む（毎回更新して最新キーを反映）
cat > "$SETTINGS_FILE" << EOF
{
  "autoUpdates": false,
  "autoUpdaterStatus": "disabled",
  "bypassPermissions": true,
  "skipDangerousModePermissionPrompt": true,
  "enabledPlugins": {
    "claude-mem@thedotmack": true
  },
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "$ZAI_API_KEY",
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
    "API_TIMEOUT_MS": "3000000",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.5-air",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-5.1",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-5.1"
  }
}
EOF

# 別HOMEでClaude Code起動（OAuth衝突回避）
export HOME="$GLM_HOME"
# skipDangerousModePermissionPrompt in settings.json suppresses the interactive confirm dialog
exec claude --model sonnet --dangerously-skip-permissions
