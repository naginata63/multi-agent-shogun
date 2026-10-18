#!/usr/bin/env python3
"""office_live_hook.py — 昼の制作を「なぎなたAI工房 ライブ」に映す(Claude Code の PreToolUse フック)

殿 2026-10-18「昼も映せ」。将軍の対話セッションがコマンドを打つたびに、その中身から
誰が何をしているかを見分け、projects/dozle_kirinuki/scripts/autopilot/state.py で書き出す。
  素材の取得・文字起こし → ツルハ / 絵を描く → フデ / 組立・アップ・調べもの・台本 → カタナ
  コマや絵の検分 → ルーペ / 編集アプリ・殿への確認 → なぎなた(殿の手番)
将軍の窓以外(夜の自動の claude -p など)では何もしない。失敗しても制作を止めぬよう、常に exit 0。
"""
import json
import os
import re
import subprocess
import sys
import time

STATE = "/home/murakami/multi-agent-shogun/projects/dozle_kirinuki/scripts/autopilot/state.py"
LAST = "/tmp/office_live_hook.last"

RULES = [  # (正規表現, 役, 一言, 裏で長く走るか)
    (r"yt-dlp|dl_win|dozle-dl|fetch_dozle|comment_refetch|comment_db\.py", "取り込み係", "素材を取得", True),
    (r"demucs|qwen_stt|whisper|stt_all", "取り込み係", "文字起こし", True),
    (r"codex exec|thumbnail_codex|office_art/gen", "手足", "絵を描く", True),
    (r"youtube_uploader\.py upload", "番頭", "YouTubeにアップ", True),
    (r"youtube_uploader\.py (thumbnail|update)", "番頭", "YouTubeを整える", False),
    (r"build_\w+\.py|night\.sh|ffmpeg .*(-c:v|h264_nvenc)", "番頭", "動画を組み立て", True),
    (r"clip_editor_server|telop_editor|panel_sync_editor", "なぎなた", "編集アプリで選定", True),
    (r"scripts/ntfy\.sh", "なぎなた", "確認待ち", True),
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
        return "番頭", "作業中", bool(inp.get("run_in_background"))
    if tool == "Read" and re.search(r"\.(png|jpe?g|webp)$", inp.get("file_path", ""), re.I):
        return "検分役", "絵を検分", False
    if tool in ("WebSearch", "WebFetch"):
        return "番頭", "調べもの", False
    if tool in ("Write", "Edit"):
        return "番頭", "台本を書く", False
    if tool == "Agent":
        return "手足", "手分けして作業", True
    return None


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return
    if tmux_agent() != "shogun":
        return
    hit = classify(d.get("tool_name", ""), d.get("tool_input") or {})
    if not hit:
        return
    role, msg, long_ = hit
    key = f"{role}|{msg}"
    try:   # 同じ役・同じ一言が20秒以内に続くなら書かぬ(記録が膨らむのを防ぐ)
        last_key, last_t = open(LAST).read().split("\t")
        if last_key == key and time.time() - float(last_t) < 20:
            return
    except Exception:
        pass
    open(LAST, "w").write(f"{key}\t{time.time()}")
    env = dict(os.environ, OFFICE_BG="1" if long_ else "0")
    subprocess.Popen(["python3", STATE, "set", time.strftime("%Y-%m-%d"), role, "running", msg],
                     env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
