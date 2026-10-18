#!/usr/bin/env python3
"""office_live_hook.py — 昼の制作を「なぎなたAI工房 ライブ」に映す(Claude Code の PreToolUse フック)

殿 2026-10-18「昼も映せ」。将軍の対話セッションがコマンドを打つたびに、その中身から
誰が何をしているかを見分け、projects/dozle_kirinuki/scripts/autopilot/state.py で書き出す。
  素材の取得・文字起こし → ツルハ / 絵を描く → フデ / 組立・アップ・調べもの・台本 → カタナ
  コマや絵の検分 → ルーペ / 編集アプリ・殿への確認 → なぎなた(殿の手番)
将軍の窓以外(夜の自動の claude -p など)では何もしない。失敗しても制作を止めぬよう、常に exit 0。
v2(殿 2026-10-18 改善 1・2・3・5・6):
  - 作品名: コマンド/ファイルの work/<名> から引き、scripts/autopilot/work_labels.json で日本語名にする
  - 終わり: PostToolUse(引数 post)で、表で走る長い処理が終わったら「済み」/「失敗」を書く(裏の処理は描く側が自分で書く)
  - 成果物: ntfy で送った URL を記録に載せる(ライブの記録欄で開ける)
  - 昼の費用: 5分に1回 state.py daycost を裏で回す
"""
import json
import os
import re
import subprocess
import sys
import time

STATE = "/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/scripts/autopilot/state.py"
LAST = "/tmp/office_live_hook.last"
LABELS = "/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/scripts/autopilot/work_labels.json"
DAYCOST_STAMP = "/tmp/office_live_hook.daycost"
SKIP_DIRS = {"autopilot", "tmp", "editor", "requests", "comment_db"}

RULES = [  # (正規表現, 役, 一言, 裏で長く走るか)
    (r"yt-dlp|dl_win|dozle-dl|fetch_dozle|comment_refetch|comment_db\.py", "取り込み係", "素材を取得", True),
    (r"demucs|qwen_stt|whisper|stt_all", "取り込み係", "文字起こし", True),
    (r"(^|&&|;|\|)\s*(bash\s+)?\S*codex_manga_batch\.sh\s", "手足", "漫画のコマを描く", True),   # 起動そのものだけ(文字を含む編集コマンドで誤爆した)。終わりはスクリプトが自分で書く
    (r"codex exec|thumbnail_codex|office_art/gen", "手足", "絵を描く", True),
    (r"youtube_uploader\.py upload", "番頭", "YouTubeにアップ", True),
    (r"youtube_uploader\.py (thumbnail|update)", "番頭", "YouTubeを整える", False),
    (r"build_\w+\.py|night\.sh|ffmpeg .*(-c:v|h264_nvenc)", "番頭", "動画を組み立て", True),
    (r"clip_editor_server|telop_editor|panel_sync_editor", "なぎなた", "編集アプリで選定", True),
    (r"scripts/ntfy\.sh", "なぎなた", "殿に送った", True),
    (r"review|qc_|posqc|shot\d*\.js|screenshot", "検分役", "コマを検分", False),
]


def tmux_agent():
    pane = os.environ.get("TMUX_PANE")
    if not pane:
        return ""
    try:
        return subprocess.run(["tmux", "display-message", "-t", pane, "-p", "#{@agent_id}"],
                              capture_output=True, text=True, timeout=2).stdout.strip()
    except Exception:
        return ""


def classify(tool, inp):
    if tool == "Bash":
        cmd = inp.get("command", "")
        for pat, role, msg, long_ in RULES:
            if re.search(pat, cmd):
                return role, msg, long_ or bool(inp.get("run_in_background"))
        m = re.search(r"(?:python3?|bash)\s+(?:-\S+\s+)*\S*?([\w\-]+)\.(?:py|sh)\b", cmd)
        return "番頭", (f"{m.group(1)} を回す" if m else "作業中"), bool(inp.get("run_in_background"))
    if tool == "Read" and re.search(r"\.(png|jpe?g|webp)$", inp.get("file_path", ""), re.I):
        return "検分役", "絵を検分", False
    if tool in ("WebSearch", "WebFetch"):
        return "番頭", "調べもの", False
    if tool in ("Write", "Edit"):
        return "番頭", "台本を書く", False
    if tool == "Agent":
        return "手足", "手分けして作業", True
    return None


def project_of(inp):
    """コマンド/ファイルの work/<名> から作品名。名札の表に無ければフォルダ名のまま"""
    text = " ".join(str(v) for v in inp.values() if isinstance(v, str))
    names = [m for m in re.findall(r"work/([A-Za-z0-9_\-]+)", text) if m not in SKIP_DIRS]
    if not names:
        return ""
    try:
        lab = json.load(open(LABELS))
    except Exception:
        lab = {}
    return lab.get(names[0], names[0])


def ntfy_text(cmd):
    m = re.search(r"ntfy\.sh\s+([\"'])(.*?)\1", cmd, re.S)
    body = m.group(2) if m else ""
    url = (re.findall(r"https?://\S+", body) or [""])[0].rstrip("'\")")
    text = re.sub(r"https?://\S+", "", body).strip()
    return text[:28], url


def write(role, status, msg, long_, proj="", url=""):
    env = dict(os.environ, OFFICE_BG="1" if long_ else "0", OFFICE_PROJ=proj, OFFICE_URL=url)
    subprocess.Popen(["python3", STATE, "set", time.strftime("%Y-%m-%d"), role, status, msg],
                     env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def daycost():
    """昼の対話の費用(API 換算)を5分に1回だけ数え直す"""
    try:
        if time.time() - os.path.getmtime(DAYCOST_STAMP) < 300:
            return
    except Exception:
        pass
    open(DAYCOST_STAMP, "w").write("")
    subprocess.Popen(["python3", STATE, "daycost", time.strftime("%Y-%m-%d")],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def post(d):
    """表で走った長い処理(裏に回さぬ文字起こし・組立など)が終わったら、済み/失敗を書く"""
    if d.get("tool_name") != "Bash":
        return
    inp = d.get("tool_input") or {}
    if inp.get("run_in_background"):
        return   # 裏の処理はまだ走っている。終わりは描く側(codex_manga_batch.sh 等)が自分で書く
    hit = classify("Bash", inp)
    if not hit or not hit[2] or hit[0] == "なぎなた" or hit[1] == "漫画のコマを描く":
        return
    role, msg, _ = hit
    r = d.get("tool_response") or {}
    out = (r.get("stderr") or "") + (r.get("stdout") or "") if isinstance(r, dict) else str(r)
    bad = (isinstance(r, dict) and r.get("interrupted")) or "Traceback (most recent call last)" in out
    write(role, "fail" if bad else "done", msg + (" 失敗" if bad else " 済み"), False, project_of(inp))


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return
    if tmux_agent() != "shogun":
        return
    daycost()
    if sys.argv[1:] == ["post"]:
        post(d)
        return
    inp = d.get("tool_input") or {}
    hit = classify(d.get("tool_name", ""), inp)
    if not hit:
        return
    role, msg, long_ = hit
    proj, url = project_of(inp), ""
    if role == "なぎなた" and msg == "殿に送った":
        text, url = ntfy_text(inp.get("command", ""))
        msg = text or msg
    key = f"{role}|{msg}|{proj}"
    try:   # 同じ役・同じ一言が20秒以内に続くなら書かぬ(記録が膨らむのを防ぐ)
        last_key, last_t = open(LAST).read().split("\t")
        if last_key == key and time.time() - float(last_t) < 20:
            return
    except Exception:
        pass
    open(LAST, "w").write(f"{key}\t{time.time()}")
    write(role, "running", msg, long_, proj, url)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
