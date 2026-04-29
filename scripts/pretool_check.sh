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
      _CK2_TARGET_PATH=$(python3 -c "
import sys, re
try:
    content = open('$_CK2_TASK_YAML').read()
    blocks = re.split(r'(?=^- task_id:)', content, flags=re.MULTILINE)
    for block in reversed(blocks):
        if re.search(r'status:\s*(assigned|in_progress)', block):
            m = re.search(r'target_path:\s*([^\n]+)', block)
            if m:
                print(m.group(1).strip().strip('\"').strip(\"'\"))
                break
except Exception:
    pass
" 2>/dev/null || true)
      if [ -n "$_CK2_TARGET_PATH" ] && echo "$_CK2_FILE_PATH" | grep -qF "$_CK2_TARGET_PATH"; then
        :  # target_pathと一致 → 許可（次のチェックへ）
      else
        # work/cmd_* パターン検出
        if echo "$_CK2_FILE_PATH" | grep -qE '/work/cmd_[0-9]+/' && \
           ! echo "$_CK2_FILE_PATH" | grep -qE '/projects/[^/]+/work/'; then
          echo "BLOCKED: リポジトリルート直下の work/cmd_*/ には書き込み禁止。" >&2
          echo "正しい格納場所: projects/{project}/work/{動画タイトル or cmd_xxx}/ 配下、" >&2
          echo "もしくはタスクYAML target_path で指定された場所。" >&2
          echo "現在のパス: $_CK2_FILE_PATH" >&2
          echo "例: /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/20260417_TITLE/output.json" >&2
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
      if echo "$_CK2_FILE_PATH" | grep -qE '/work/cmd_[0-9]+/' && \
         ! echo "$_CK2_FILE_PATH" | grep -qE '/projects/[^/]+/work/'; then
        echo "BLOCKED: リポジトリルート直下の work/cmd_*/ には書き込み禁止。" >&2
        echo "正しい格納場所: projects/{project}/work/{動画タイトル or cmd_xxx}/ 配下、" >&2
        echo "もしくはタスクYAML target_path で指定された場所。" >&2
        echo "現在のパス: $_CK2_FILE_PATH" >&2
        echo "例: /home/murakami/multi-agent-shogun/projects/dozle_kirinuki/work/20260417_TITLE/output.json" >&2
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

# ── チェック3 拡張: 新規 task_id の procedure: 必須 (cmd_1470) ──
# steps 1行化済の新規 task に procedure: がなければ BLOCK。
# CHK7 と同じ new_id 判定 (post_ids - pre_ids)。Write/Edit のみ対象。
if [[ "$_CK3_MATCH" == "true" ]] && { [[ "$TOOL_NAME" == "Write" ]] || [[ "$TOOL_NAME" == "Edit" ]]; }; then
  _CK3_PROC_RESULT=$(PRETOOL_INPUT_JSON="$INPUT" python3 <<'PYEOF_PROC' 2>/dev/null
import os, json, re, sys
try:
    data = json.loads(os.environ.get('PRETOOL_INPUT_JSON', ''))
except Exception:
    sys.exit(0)
ti = data.get('tool_input', {})
tool = data.get('tool_name', '')
file_path = ti.get('file_path', '')
try:
    with open(file_path) as f:
        pre = f.read()
except Exception:
    pre = ''
if tool == 'Edit':
    old_s = ti.get('old_string', '')
    new_s = ti.get('new_string', '')
    if ti.get('replace_all'):
        post = pre.replace(old_s, new_s)
    else:
        post = pre.replace(old_s, new_s, 1)
elif tool == 'Write':
    post = ti.get('content', '')
else:
    sys.exit(0)
def ids_in(content):
    out = set()
    for m in re.finditer(r'^- task_id:\s*(\S+)', content, re.MULTILINE):
        v = m.group(1).strip().strip('"').strip("'")
        out.add(v)
    return out
pre_ids = ids_in(pre)
post_ids = ids_in(post)
new_ids = post_ids - pre_ids
if not new_ids:
    sys.exit(0)
blocks = re.split(r'(?=^- task_id:)', post, flags=re.MULTILINE)
missing = []
for block in blocks:
    if not block.strip().startswith('- task_id:'):
        continue
    m = re.search(r'^- task_id:\s*(\S+)', block, re.MULTILINE)
    if not m:
        continue
    tid = m.group(1).strip().strip('"').strip("'")
    if tid not in new_ids:
        continue
    if not re.search(r'^\s+procedure:', block, re.MULTILINE):
        missing.append(tid)
if missing:
    print('BLOCKED: 新規 task_id に procedure: フィールドがありません (CHK3拡張)')
    for tid in missing:
        print(f'  - {tid}')
    print('具体的手順は shared_context/procedures/ に外出しし、procedure: で参照せよ。')
    print('例: procedure: shared_context/procedures/xxx.md')
    print('既存 task の編集は対象外 (新規 task_id のみ)。')
    sys.exit(2)
sys.exit(0)
PYEOF_PROC
)
  _CK3_PROC_EXIT=$?
  if [ $_CK3_PROC_EXIT -eq 2 ]; then
    echo "$_CK3_PROC_RESULT" >&2
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

  echo "$(date +%H:%M:%S) CHK4: content_len=${#_CMD_CONTENT}, tool=$TOOL_NAME, cmd_len=${#COMMAND}, cmd_first50=${COMMAND:0:50}" >> "$SCRIPT_DIR/../logs/pretool_cmd_check.log"
  if [ -n "$_CMD_CONTENT" ]; then
    echo "$(date +%H:%M:%S) CHK4: has content, checking cmd_id" >> "$SCRIPT_DIR/../logs/pretool_cmd_check.log"
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

# ── チェック5: done gate (cmd_1442 H1 + H10改統合) ──
# queue/tasks/{ashigaru*,gunshi}.yaml の status:done 遷移を検査:
#   (1) verify: 欄宣言済 task は verify_result:pass 必須 (未達なら BLOCK)
#   (2) verify: 欄宣言済 task は advisor 呼出 2 回以上必須 (未達なら BLOCK)
# opt-in: verify: 欄無しの task は素通り (既存全 subtask の後方互換)。
# 実ロジックは scripts/done_gate.sh に委譲。
if [[ "$TOOL_NAME" == "Write" ]] || [[ "$TOOL_NAME" == "Edit" ]]; then
  _CK5_FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)
  if echo "$_CK5_FILE_PATH" | grep -qE 'queue/tasks/(ashigaru[0-9]+|gunshi)\.yaml$'; then
    # edit 後の content を simulate し、status:done の task_id を列挙する
    # NOTE: stdin は heredoc が奪うため INPUT を env 経由で渡す
    _CK5_DONE_IDS=$(PRETOOL_INPUT_JSON="$INPUT" PRETOOL_FILE_PATH="$_CK5_FILE_PATH" python3 <<'PYEOF' 2>/dev/null
import sys, json, re, os, tempfile
try:
    data = json.loads(os.environ.get('PRETOOL_INPUT_JSON', ''))
except Exception:
    sys.exit(0)
ti = data.get('tool_input', {})
tool = data.get('tool_name', '')
file_path = os.environ.get('PRETOOL_FILE_PATH', '')

if tool == 'Edit':
    old_s = ti.get('old_string', '')
    new_s = ti.get('new_string', '')
    if not re.search(r'(^|\n)\s*status:\s*done\b', new_s):
        sys.exit(0)
    try:
        with open(file_path) as f:
            content = f.read()
    except Exception:
        sys.exit(0)
    if ti.get('replace_all'):
        content = content.replace(old_s, new_s)
    else:
        content = content.replace(old_s, new_s, 1)
elif tool == 'Write':
    content = ti.get('content', '')
else:
    sys.exit(0)

# post-edit content を temp file に出力し、done かつ verify 宣言済 task_id を列挙
tmp = tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False, prefix='pretool_sim_')
tmp.write(content)
tmp.close()

blocks = re.split(r'(?=^- task_id:)', content, flags=re.MULTILINE)
ids = []
for block in blocks:
    if not block.strip().startswith('- task_id:'):
        continue
    tid_m = re.search(r'^- task_id:\s*(\S+)', block, re.MULTILINE)
    if not tid_m:
        continue
    task_id = tid_m.group(1).strip().strip('"').strip("'")
    if not re.search(r'^\s+verify:\s*(\{|$|\n)', block, re.MULTILINE):
        continue
    st_m = re.search(r'^\s+status:\s*([^\s\n#]+)', block, re.MULTILINE)
    if not st_m:
        continue
    status_val = st_m.group(1).strip().strip('"').strip("'")
    if status_val != 'done':
        continue
    ids.append(task_id)

if ids:
    print(tmp.name)
    for tid in ids:
        print(tid)
else:
    os.unlink(tmp.name)
PYEOF
)
    if [ -n "$_CK5_DONE_IDS" ]; then
      _CK5_SIM=$(echo "$_CK5_DONE_IDS" | head -n1)
      _CK5_AGENT=""
      if [ -n "${TMUX_PANE:-}" ]; then
        _CK5_AGENT=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
      fi
      [ -z "$_CK5_AGENT" ] && _CK5_AGENT="unknown"

      _CK5_FAIL=0
      _CK5_MSG=""
      while IFS= read -r _CK5_TID; do
        [ -z "$_CK5_TID" ] && continue
        if bash "${SCRIPT_DIR}/done_gate.sh" "$_CK5_AGENT" "$_CK5_TID" "$_CK5_SIM" 2>/tmp/done_gate_err.$$ ; then
          :
        else
          _CK5_FAIL=1
          _CK5_MSG="${_CK5_MSG}$(cat /tmp/done_gate_err.$$ 2>/dev/null)\n"
        fi
        rm -f /tmp/done_gate_err.$$
      done < <(echo "$_CK5_DONE_IDS" | tail -n +2)

      rm -f "$_CK5_SIM" 2>/dev/null

      if [ "$_CK5_FAIL" -eq 1 ]; then
        printf "%b" "$_CK5_MSG" >&2
        exit 2
      fi
    fi
  fi
fi

# ── チェック6: advisor 呼出ログ (cmd_1442 H10改) ──
# tool_name == "advisor" 検出時、logs/advisor_calls.log に追記。
# 形式: ISO8601\tagent_id\ttask_id\tloop=pre|post
# done_gate.sh はこのログを参照して呼出回数を検証する。
if [[ "$TOOL_NAME" == "advisor" ]]; then
  _CK6_AGENT=""
  _CK6_TASK=""
  if [ -n "${TMUX_PANE:-}" ]; then
    _CK6_AGENT=$(tmux display-message -t "$TMUX_PANE" -p '#{@agent_id}' 2>/dev/null || true)
    _CK6_TASK=$(tmux display-message -t "$TMUX_PANE" -p '#{@current_task}' 2>/dev/null || true)
  fi
  [ -z "$_CK6_AGENT" ] && _CK6_AGENT="unknown"
  [ -z "$_CK6_TASK" ] && _CK6_TASK="unknown"
  mkdir -p "${REPO_DIR}/logs" 2>/dev/null || true
  printf "%s\t%s\t%s\tsource=pretool_hook\n" \
    "$(date -Iseconds 2>/dev/null || date +%Y-%m-%dT%H:%M:%S)" \
    "$_CK6_AGENT" \
    "$_CK6_TASK" \
    >> "${REPO_DIR}/logs/advisor_calls.log" 2>/dev/null || true
  # Never BLOCK advisor calls — logging is side-effect only
fi

# ── チェック7: task YAML lint (cmd_1443 p06 H5) ──
# queue/tasks/{ashigaru*,gunshi}.yaml に新規 task ブロックを追加する編集で、
# 必須フィールド (task_id/parent_cmd/bloom_level/status/target_path/timestamp/
# description/steps/acceptance_criteria) 欠落時 BLOCK。
#
# 規制は NEW task_id のみ対象 (既存 task の status 変更等は素通り・regression 回避)。
# NEW 判定: 編集前ファイルに該当 task_id がなく、編集後に出現する task_id。
if [[ "$TOOL_NAME" == "Write" ]] || [[ "$TOOL_NAME" == "Edit" ]]; then
  _CK7_FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)
  if echo "$_CK7_FILE_PATH" | grep -qE 'queue/tasks/(ashigaru[0-9]+|gunshi)\.yaml$'; then
    _CK7_RESULT=$(PRETOOL_INPUT_JSON="$INPUT" PRETOOL_FILE_PATH="$_CK7_FILE_PATH" python3 <<'PYEOF' 2>/dev/null
import os, json, re, sys
REQUIRED = ['task_id','parent_cmd','bloom_level','status','target_path','timestamp','description','steps','acceptance_criteria']
try:
    data = json.loads(os.environ.get('PRETOOL_INPUT_JSON',''))
except Exception:
    sys.exit(0)
ti = data.get('tool_input', {})
tool = data.get('tool_name', '')
file_path = os.environ.get('PRETOOL_FILE_PATH', '')

# pre-edit content
try:
    with open(file_path) as f:
        pre = f.read()
except Exception:
    pre = ''

if tool == 'Edit':
    old_s = ti.get('old_string','')
    new_s = ti.get('new_string','')
    if ti.get('replace_all'):
        post = pre.replace(old_s, new_s)
    else:
        post = pre.replace(old_s, new_s, 1)
elif tool == 'Write':
    post = ti.get('content','')
else:
    sys.exit(0)

def ids_in(content):
    out = set()
    for m in re.finditer(r'^- task_id:\s*(\S+)', content, re.MULTILINE):
        v = m.group(1).strip().strip('"').strip("'")
        out.add(v)
    return out

pre_ids = ids_in(pre)
post_ids = ids_in(post)
new_ids = post_ids - pre_ids
if not new_ids:
    sys.exit(0)

blocks = re.split(r'(?=^- task_id:)', post, flags=re.MULTILINE)
violations = []
for block in blocks:
    if not block.strip().startswith('- task_id:'):
        continue
    m = re.search(r'^- task_id:\s*(\S+)', block, re.MULTILINE)
    if not m:
        continue
    tid = m.group(1).strip().strip('"').strip("'")
    if tid not in new_ids:
        continue
    missing = []
    for fld in REQUIRED:
        if fld == 'task_id':
            continue  # already confirmed
        # Acceptance criteria = list, so look for the key start only
        if not re.search(rf'^\s+{re.escape(fld)}:', block, re.MULTILINE):
            missing.append(fld)
    if missing:
        violations.append(f'{tid}: missing {",".join(missing)}')

if violations:
    print('BLOCKED: task YAML lint (cmd_1443 p06 H5): 新規 task_id に必須フィールド欠落')
    for v in violations:
        print(f'  - {v}')
    print('必須フィールド: ' + ' / '.join(REQUIRED))
    print('既存 task の編集は対象外 (NEW task_id のみ lint)。task YAML 追記時は template 参照せよ。')
    sys.exit(2)
sys.exit(0)
PYEOF
)
    _CK7_EXIT=$?
    if [ $_CK7_EXIT -eq 2 ]; then
      echo "$_CK7_RESULT" >&2
      exit 2
    fi
  fi
fi

# ── チェック8: git add . / -A BLOCK (cmd_1443 p06 scope_extension) ──
# 軍師 qc_1443_p02 HIGH finding (commit 1440234 巻込事故) 対応:
# 足軽が `git add .` で他足軽の作業中ファイルを巻込 commit する事故の恒久防止。
# BLOCK: `git add .` (literal dot), `git add -A`, `git add --all`, `git add *` (unquoted glob)
# 許可: `git add -p` / `--patch`, `git add <具体パス>`, `git add -u` (tracked-only・note で記録)
# 重要: ヒアドキュメント / 引用文字列内に現れる "git add ." 等の文字列は誤検知しない
#       (commit message に `git add .` と書いた場合等の false positive 回避)
if [[ "$TOOL_NAME" == "Bash" ]]; then
  # ヒアドキュメント (<<'EOF' ... EOF / <<EOF ... EOF / <<-EOF / <<'PYEOF' 等) を除去
  # また "..." / '...' / $(cat <<...) 等の引用内容も除外
  _CK8_CMD=$(PRETOOL_CMD_RAW="$COMMAND" python3 <<'PYEOF_CK8' 2>/dev/null || true
import os, re, sys
cmd = os.environ.get('PRETOOL_CMD_RAW', '')
# Strip heredoc bodies: match <<'TAG' or <<"TAG" or <<TAG or <<-TAG up to a line "TAG"
def strip_heredocs(s):
    def repl(m):
        return '\n'  # keep line count roughly
    # -? optional indent, ' or " optional quotes around tag
    pat = re.compile(r"<<-?(['\"]?)(\w+)\1.*?^\s*\2\s*$", re.DOTALL | re.MULTILINE)
    prev = None
    while prev != s:
        prev = s
        s = pat.sub(repl, s)
    return s
cmd = strip_heredocs(cmd)
# Strip single-quoted strings '...' (no escaping inside)
cmd = re.sub(r"'[^']*'", "''", cmd)
# Strip double-quoted strings "..." (simple — ignore escaped quotes)
cmd = re.sub(r'"[^"]*"', '""', cmd)
# Strip backtick `...`
cmd = re.sub(r'`[^`]*`', '``', cmd)
print(cmd)
PYEOF_CK8
)
  if [ -z "$_CK8_CMD" ]; then
    _CK8_CMD="$COMMAND"  # fallback
  fi
  # `git add .` / `git add -f .`
  if echo "$_CK8_CMD" | grep -qE '(^|[[:space:];&|])git add ([-][AfF]+ )?(\.)($|[[:space:];&|])'; then
    echo "BLOCKED: 'git add .' 禁止 (cmd_1443 p06 scope / 軍師 qc_1443_p02 HIGH finding)" >&2
    echo "理由: 他足軽の作業中ファイルを意図せず staged する巻込事故の恒久対策" >&2
    echo "許可: 'git add <具体パス>' / 'git add -p' (対話的) / 'git add --patch'" >&2
    exit 2
  fi
  if echo "$_CK8_CMD" | grep -qE '(^|[[:space:];&|])git add ([-][AfF]+ )?\*($|[[:space:];&|])'; then
    echo "BLOCKED: 'git add *' (unquoted glob) 禁止 (cmd_1443 p06 scope)" >&2
    echo "許可: 'git add <具体パス>' / 'git add -p'" >&2
    exit 2
  fi
  if echo "$_CK8_CMD" | grep -qE '(^|[[:space:];&|])git add (-A|--all)\b'; then
    echo "BLOCKED: 'git add -A' / 'git add --all' 禁止 (cmd_1443 p06 scope)" >&2
    echo "理由: 他足軽の作業中ファイルを意図せず staged する巻込事故の恒久対策" >&2
    echo "許可: 'git add <具体パス>' / 'git add -p'" >&2
    exit 2
  fi
fi

# ── チェック10: curl JSON 直書き BLOCK (cmd_1546) ──
# cmd_create / inbox_write 等のAPI投入で JSON を直接 -d '{...}' するのを禁止。
# ペイロードは queue/cmd_payloads/ にファイル保存し、curl --data @path で投入せよ。
# 例外: inbox_write の短文メッセージ (文字数 ≤200) は許可。
if [[ "$TOOL_NAME" == "Bash" ]]; then
  if echo "$COMMAND" | grep -qE 'curl.*(-d|--data|--data-raw|--data-binary)\s+['\''"]?\{'; then
    # 例外判定: @ファイル参照 は許可
    if ! echo "$COMMAND" | grep -qE 'curl.*(-d|--data|--data-raw|--data-binary)\s+@'; then
      # 例外判定: inbox_write の短文 (message値が200文字以下) は許可
      _CK10_IS_SHORT=$(echo "$COMMAND" | python3 -c "
import sys, re, json
cmd = sys.stdin.read()
is_inbox = '/api/inbox_write' in cmd
m = re.search(r\"(-d|--data|--data-raw|--data-binary)\\s+['\\\"]?(\\{.+})['\\\"]?\\s*($|;|&|\\|)\", cmd, re.DOTALL)
if m and is_inbox:
    try:
        d = json.loads(m.group(2))
        msg = d.get('message', '')
        if len(msg) <= 200:
            print('short')
        else:
            print('long')
    except Exception:
        print('long')
else:
    print('long')
" 2>/dev/null || echo "long")
      if [[ "$_CK10_IS_SHORT" != "short" ]]; then
        echo "BLOCKED: curl API投入でJSON直書きは禁止 (cmd_1546 CHK10)" >&2
        echo "queue/cmd_payloads/ にペイロードファイルを置き、curl --data @<path> で送れ。" >&2
        echo "詳細: context/cmd_template.md / queue/cmd_payloads/README.md" >&2
        exit 2
      fi
    fi
  fi
fi

# ── チェック9: full_yaml_blob 参照 BLOCK (cmd_1511 再発防止) ──
# full_yaml_blob は 3テーブルから削除済。再追加・参照を防止する。
if [ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ]; then
  _CHK9_FILE_PATH=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null)
  if echo "$_CHK9_FILE_PATH" | grep -qE '\.py$'; then
    _CHK9_CONTENT=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('new_string','') + d.get('content',''))" 2>/dev/null)
    if echo "$_CHK9_CONTENT" | grep -q 'full_yaml_blob'; then
      echo "BLOCKED: full_yaml_blob 参照検出 (cmd_1511 再発防止ルール)" >&2
      echo "理由: 3テーブル(commands/tasks/reports)から同カラム削除済。再追加禁止。" >&2
      exit 2
    fi
  fi
fi

exit 0
