#!/usr/bin/env bash
# pretool_check.sh — PreToolUse hook
# ハーネスエンジニアリング: ルールを仕組みで強制する
#
# チェック項目:
# 1. tmux capture-pane は最低100行 (-S -100以上)
# 2. 足軽のwork/cmd_*出力防止 + /tmp/書き込み禁止

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

INPUT=$(cat 2>/dev/null || true)

# ツール名とコマンドを抽出
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)

COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || true)

# 自分自身のテスト実行はスキップ
if [[ "$TOOL_NAME" == "Bash" ]] && echo "$COMMAND" | grep -q "pretool_check"; then
  exit 0
fi

# ── チェック1: tmux capture-pane は最低100行 (Bashツールのみ) ──
if [[ "$TOOL_NAME" == "Bash" ]] && echo "$COMMAND" | grep -q "tmux capture-pane"; then
  # -S オプションの値を抽出
  LINES_VAL=$(echo "$COMMAND" | grep -oP '\-S\s+\-?\K\d+' | head -1)
  if [[ -n "$LINES_VAL" && "$LINES_VAL" -lt 100 ]]; then
    echo "BLOCKED: pane確認は最低100行（-S -100）。-S -${LINES_VAL} は短すぎる。誤判断の元。MEMORY.mdルール参照。" >&2
    exit 2
  fi
  # -S オプションなし（デフォルト=短い）
  if ! echo "$COMMAND" | grep -q "\-S"; then
    echo "BLOCKED: tmux capture-paneに-Sオプションがない。-S -100 以上を指定せよ。" >&2
    exit 2
  fi
fi

# ── チェック2: 足軽のwork/cmd_*出力防止 + /tmp/禁止 (Write/Edit/Bashツール) ──
# 足軽判定（共通）
_CK2_AGENT_ID=""
if [ -n "${TMUX_PANE:-}" ]; then
  _CK2_AGENT_ID=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
fi
if [[ "$_CK2_AGENT_ID" == ashigaru* ]]; then
  _CK2_FILE_PATH=""
  _CK2_SKIP=false
  if [[ "$TOOL_NAME" == "Write" ]] || [[ "$TOOL_NAME" == "Edit" ]]; then
    _CK2_FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)
  elif [[ "$TOOL_NAME" == "Bash" ]]; then
    # Bash: リダイレクト先パスをcommandから抽出（>>, >, tee等）
    _CK2_FILE_PATH=$(echo "$COMMAND" | python3 -c "
import sys, re
cmd = sys.stdin.read()
# リダイレクト先を抽出: > /path, >> /path
matches = re.findall(r'(?:>>|>)\s*([^\s;|&]+)', cmd)
# tee /path パターン
matches += re.findall(r'tee\s+([^\s;|&]+)', cmd)
# 最初にマッチしたパスを使用
for m in matches:
    if m and not m.startswith('/dev/'):
        print(m)
        break
" 2>/dev/null || true)
    # Bashでshogun_to_karo.yaml書き込みの場合はチェック2の対象外（チェック4で処理）
    if [[ "$COMMAND" == *"shogun_to_karo.yaml"* ]]; then
      _CK2_SKIP=true
    fi
  fi

  if [[ "$_CK2_SKIP" == "false" && -n "$_CK2_FILE_PATH" ]]; then
    # Phase 2: タスクYAMLからtarget_pathを読み取り、一致するパスは許可
    _CK2_AGENT_NUM="${_CK2_AGENT_ID#ashigaru}"
    _CK2_TASK_YAML="${REPO_DIR}/queue/tasks/ashigaru${_CK2_AGENT_NUM}.yaml"
    if [ -f "$_CK2_TASK_YAML" ]; then
      _CK2_TARGET_PATH=$(grep -A5 'status: assigned' "$_CK2_TASK_YAML" | grep -E 'target_path:|output_file:' | head -1 | sed 's/.*:[[:space:]]*//' | tr -d '"' | tr -d "'" || true)
      if [ -n "$_CK2_TARGET_PATH" ] && echo "$_CK2_FILE_PATH" | grep -qF "$_CK2_TARGET_PATH"; then
        :  # target_pathと一致 → 許可（次のチェックへ）
      else
        # work/cmd_* パターン検出
        if echo "$_CK2_FILE_PATH" | grep -qE '/work/cmd_[0-9]+/'; then
          echo "BLOCKED: 足軽はwork/cmd_*に直接書き込み禁止。タスクYAMLのtarget_pathに出力せよ。パス: $_CK2_FILE_PATH" >&2
          exit 2
        fi

        # /tmp/ パターン検出
        if [[ "$_CK2_FILE_PATH" == /tmp/* ]]; then
          echo "BLOCKED: /tmp/への出力禁止（再起動で消える）。work/配下またはtarget_pathに出力せよ。パス: $_CK2_FILE_PATH" >&2
          exit 2
        fi
      fi
    else
      # タスクYAMLなし（通常ありえないが念のため）
      if echo "$_CK2_FILE_PATH" | grep -qE '/work/cmd_[0-9]+/'; then
        echo "BLOCKED: 足軽はwork/cmd_*に直接書き込み禁止。パス: $_CK2_FILE_PATH" >&2
        exit 2
      fi
      if [[ "$_CK2_FILE_PATH" == /tmp/* ]]; then
        echo "BLOCKED: /tmp/への出力禁止（再起動で消える）。パス: $_CK2_FILE_PATH" >&2
        exit 2
      fi
    fi
  fi
fi

# ── チェック3: タスクYAMLのsteps行数チェック (Write/Edit/Bashツール) ──
_CK3_MATCH=false
_CK3_CONTENT=""
if [[ "$TOOL_NAME" == "Write" ]] || [[ "$TOOL_NAME" == "Edit" ]]; then
  CHECK_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)
  if echo "$CHECK_PATH" | grep -qE 'queue/tasks/(ashigaru[0-9]+|gunshi)\.yaml'; then
    _CK3_MATCH=true
    _CK3_CONTENT=$(echo "$INPUT" | python3 -c "
import sys,json
d=json.load(sys.stdin).get('tool_input',{})
print(d.get('content','') + d.get('new_string',''))
" 2>/dev/null || true)
  fi
elif [[ "$TOOL_NAME" == "Bash" ]]; then
  # Bash: command内にqueue/tasks/*.yamlへの書き込みがあるか
  if echo "$COMMAND" | grep -qE 'queue/tasks/(ashigaru[0-9]+|gunshi)\.yaml'; then
    _CK3_MATCH=true
    # Bashコマンド全文をcontentとして扱う（HereDoc等を含む）
    _CK3_CONTENT="$COMMAND"
  fi
fi

if [[ "$_CK3_MATCH" == "true" && -n "$_CK3_CONTENT" ]]; then
  # stepsフィールドの行数だけカウント（steps: | の後の内容）
  STEPS_LINES=$(echo "$_CK3_CONTENT" | python3 -c "
import sys, re
text = sys.stdin.read()
# steps: | 以降の内容を抽出
m = re.search(r'steps:\s*\|?\n((?:[ \t]+.*\n?)*)', text)
if m:
    lines = [l for l in m.group(1).split('\n') if l.strip()]
    print(len(lines))
else:
    print(0)
" 2>/dev/null || echo 0)
  if [ "$STEPS_LINES" -gt 1 ]; then
    echo "BLOCKED: タスクYAMLのstepsが${STEPS_LINES}行（上限1行）。手順はshared_context/procedures/に外出しし、procedure:フィールドで参照せよ。stepsには補足1行のみ。" >&2
    exit 2
  fi
fi

# ── チェック: スクリプトblacklist + 未登録警告（足軽のみ）──
if [[ "$TOOL_NAME" == "Bash" ]]; then
  _AGENT_ID_BK=""
  if [ -n "${TMUX_PANE:-}" ]; then
    _AGENT_ID_BK=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
  fi
  if [[ "$_AGENT_ID_BK" == ashigaru* ]]; then
    if echo "$COMMAND" | grep -qE 'python3[[:space:]]+[^-][^[:space:]]*\.py' && \
       ! echo "$COMMAND" | grep -qE 'python3[[:space:]]+-[cm]|venv/|pip'; then
      PY_FILES=$(echo "$COMMAND" | grep -oE '[^/[:space:]]+\.py' | grep -v '__pycache__')
      if [[ -n "$PY_FILES" ]]; then
        BLACKLIST="${REPO_DIR}/config/script_blacklist.txt"
        SCRIPT_INDEX="${REPO_DIR}/projects/dozle_kirinuki/context/script_index.md"
        # 1段目: blacklist → BLOCKED（全.pyファイルをループチェック）
        for PY_FILE in $PY_FILES; do
          if [[ -f "$BLACKLIST" ]] && grep -qxF "$PY_FILE" "$BLACKLIST"; then
            echo "BLOCKED: ${PY_FILE} はblacklistに登録された使用禁止スクリプトです。" >&2
            echo "config/script_blacklist.txt を参照。代替スクリプトを使用してください。" >&2
            exit 2
          fi
        done
        # 2段目: script_index.md未登録 → WARNING + 候補表示（メインスクリプトのみ）
        PY_FILE=$(echo "$PY_FILES" | head -1)
        if [[ -f "$SCRIPT_INDEX" ]] && ! grep -qF "$PY_FILE" "$SCRIPT_INDEX"; then
          echo "WARNING: 未登録スクリプト: ${PY_FILE}" >&2
          # キーワード分割で類似候補を検索
          BASE="${PY_FILE%.py}"
          IFS='_' read -ra KWS <<< "$BASE"
          BEST_CANDIDATES=""
          while IFS= read -r si_line; do
            if [[ "$si_line" =~ ^\#[[:space:]]([a-zA-Z_]+\.py) ]] || \
               [[ "$si_line" =~ ^\#{2,3}[[:space:]]([a-zA-Z_]+\.py) ]]; then
              CAND="${BASH_REMATCH[1]}"
              CNT=0
              for KW in "${KWS[@]}"; do
                [[ "$CAND" == *"$KW"* ]] && ((CNT++)) || true
              done
              [[ $CNT -ge 2 ]] && BEST_CANDIDATES="${BEST_CANDIDATES}${CAND}|2 "
              [[ $CNT -eq 1 ]] && BEST_CANDIDATES="${BEST_CANDIDATES}${CAND}|1 "
            fi
          done < "$SCRIPT_INDEX"
          # 2一致優先、なければ1一致
          SHOW=$(echo "$BEST_CANDIDATES" | tr ' ' '\n' | grep '|2' | head -3)
          [[ -z "$SHOW" ]] && SHOW=$(echo "$BEST_CANDIDATES" | tr ' ' '\n' | grep '|1' | head -3)
          if [[ -n "$SHOW" ]]; then
            echo "類似の登録済みスクリプト:" >&2
            while IFS='|' read -r CNAME _; do
              [[ -z "$CNAME" ]] && continue
              PURPOSE=$(grep -A5 "^### ${CNAME}" "$SCRIPT_INDEX" | grep '\*\*用途\*\*' | head -1 | sed 's/.*用途[^:：]*[:：][[:space:]]*//')
              echo "  → ${CNAME}（${PURPOSE:-詳細はscript_index.md参照}）" >&2
            done <<< "$SHOW"
          fi
          echo "正規スクリプトを使用してください。判断できない場合は家老に確認せよ。" >&2
        fi
      fi
    fi
  fi
fi

# ── チェック4: 将軍cmdのlord_original必須チェック (Write/Edit/Bashツール) ──
# 将軍のみ対象
_AGENT_ID_CMD="${_AGENT_ID_CMD:-}"
if [ -z "$_AGENT_ID_CMD" ] && [ -n "${TMUX_PANE:-}" ]; then
  _AGENT_ID_CMD=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
fi
if [[ "$_AGENT_ID_CMD" == "shogun" ]]; then
  _CMD_CONTENT=""
  if [[ "$TOOL_NAME" == "Write" ]] || [[ "$TOOL_NAME" == "Edit" ]]; then
    _CMD_CHECK_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)
    if [[ "$_CMD_CHECK_PATH" == *"shogun_to_karo.yaml" ]]; then
      _CMD_CONTENT=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin).get('tool_input', {})
print(d.get('content', '') + d.get('new_string', ''))
" 2>/dev/null || true)
    fi
  elif [[ "$TOOL_NAME" == "Bash" ]]; then
    # Bashツール: command内にshogun_to_karo.yamlが含まれる場合のみ
    if [[ "$COMMAND" == *"shogun_to_karo.yaml"* ]]; then
      # Bashコマンド全文を_CMD_CONTENTとして扱う（HereDoc等の内容を含む）
      _CMD_CONTENT="$COMMAND"
    fi
  fi

  echo "$(date +%H:%M:%S) CHK4: content_len=${#_CMD_CONTENT}, tool=$TOOL_NAME, cmd_len=${#COMMAND}, cmd_first50=${COMMAND:0:50}" >> /tmp/pretool_cmd_check.log
  if [ -n "$_CMD_CONTENT" ]; then
    echo "$(date +%H:%M:%S) CHK4: has content, checking cmd_id" >> /tmp/pretool_cmd_check.log
    # 新規cmdブロック（- id: cmd_）が含まれるか確認
    if echo "$_CMD_CONTENT" | grep -qF -- '- id: cmd_'; then
      # lord_original: フィールドが存在するか確認
      HAS_LORD_ORIGINAL=$(echo "$_CMD_CONTENT" | python3 -c "
import sys, re
text = sys.stdin.read()
blocks = re.split(r'(?=^- id: cmd_)', text, flags=re.MULTILINE)
missing = []
for block in blocks:
    if not block.strip().startswith('- id: cmd_'):
        continue
    cmd_match = re.search(r'^- id: (cmd_\d+)', block, re.MULTILINE)
    if not cmd_match:
        continue
    cmd_id = cmd_match.group(1)
    lo_match = re.search(r'^  lord_original:\s*(.+)', block, re.MULTILINE)
    if not lo_match:
        missing.append(cmd_id)
    else:
        val = lo_match.group(1).strip()
        for ch in ['\"', chr(39)]:
            val = val.strip(ch)
        if not val:
            missing.append(cmd_id)
if missing:
    print('MISSING:' + ','.join(missing))
else:
    print('OK')
" 2>/dev/null || echo "OK")

      if [[ "$HAS_LORD_ORIGINAL" == MISSING:* ]]; then
        MISSING_CMDS="${HAS_LORD_ORIGINAL#MISSING:}"
        echo "BLOCKED: ${MISSING_CMDS} に lord_original フィールドがありません。" >&2
        echo "殿の発言原文を lord_original: に記載せよ（加工・要約禁止）。" >&2
        echo "例: lord_original: \"難問を今の足軽にやらせろ\"" >&2
        exit 2
      fi
    fi
  fi
fi

exit 0
