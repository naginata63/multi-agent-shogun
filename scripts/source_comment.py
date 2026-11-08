#!/usr/bin/env python3
"""
source_comment.py — 公開済み動画に「📌 元動画：題+URL」のコメントをもう1つ投稿する(殿 2026-11-08「もう1個コメント投稿したくて 動画に合わせてコメントいれたい」)

形(殿の例どおり):
  📌 元動画：
  【ロケランあり】銃でしか戦えない世界でエンドラ討伐！【マイクラ】
  https://www.youtube.com/watch?v=zwmA378Jktc

元動画の決め方:
  概要欄に出てくる YouTube 動画のうち、自チャンネル以外の動画がちょうど1本なら、それを元動画とする。
  題は本家の今の題を API で引く。2本以上(総集編・ランキング等)と0本は飛ばす(殿 11-08 案どおり)。
既に「📌 元動画」で始まる自コメントがある動画は飛ばす。
投稿は1本 50 枠を食い、一日の枠はアップ・分析と共用ゆえ、1回の投稿は --max 本まで(新しい動画から)。

Usage:
  python3 source_comment.py --dry-run     # 投稿せず、付ける一覧を表示+確認ページを書く
  python3 source_comment.py --max 30      # 投稿(既定30本まで)
"""
import argparse
import html
import json
import os
import re
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cta_comment as cta  # 認証・公開動画一覧・自チャンネルIDは CTA と共用

HEAD = cta.SOURCE_COMMENT_HEAD
YT_ID = re.compile(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([\w-]{11})')
PAGE_DIR = os.path.join(cta.PROJECT_DIR, "analytics", "dashboard", "source_comment")


def snippets(youtube, ids):
    out = {}
    for i in range(0, len(ids), 50):
        r = youtube.videos().list(part="snippet", id=",".join(ids[i:i + 50])).execute()
        for it in r.get("items", []):
            out[it["id"]] = it["snippet"]
    return out


def has_source_comment(youtube, video_id, my_channel_id):
    """(found, error)。コメント無効などで読めなければ error=True"""
    page_token = None
    while True:
        try:
            kw = dict(part="snippet", videoId=video_id, maxResults=100)
            if page_token:
                kw["pageToken"] = page_token
            res = youtube.commentThreads().list(**kw).execute()
        except Exception as e:
            return False, str(e).split("returned")[-1][:80]
        for th in res.get("items", []):
            s = th["snippet"]["topLevelComment"]["snippet"]
            if s.get("authorChannelId", {}).get("value") == my_channel_id and s["textOriginal"].lstrip().startswith(HEAD):
                return True, None
        page_token = res.get("nextPageToken")
        if not page_token:
            return False, None


def comment_text(title, vid):
    return f"{HEAD}：\n{title}\nhttps://www.youtube.com/watch?v={vid}"


def write_page(rows, stamp):
    os.makedirs(PAGE_DIR, exist_ok=True)
    order = {"投稿する": 0, "済み": 1, "元動画が複数": 2, "元動画なし": 3, "コメント不可": 4}
    rows = sorted(rows, key=lambda r: order.get(r["action"], 9))
    cnt = {}
    for r in rows:
        cnt[r["action"]] = cnt.get(r["action"], 0) + 1
    trs = "".join(
        f'<tr class="a{order.get(r["action"], 9)}"><td>{html.escape(r["action"])}</td>'
        f'<td><a href="https://youtu.be/{r["id"]}">{html.escape(r["title"])}</a></td>'
        f'<td>{"<pre>" + html.escape(r["text"]) + "</pre>" if r["text"] else html.escape(r.get("note", ""))}</td></tr>'
        for r in rows)
    summ = " / ".join(f"{k} {v}" for k, v in sorted(cnt.items(), key=lambda kv: order.get(kv[0], 9)))
    path = os.path.join(PAGE_DIR, f"dryrun_{stamp}.html")
    open(path, "w").write(f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>元動画コメント 試し運転</title><style>
:root{{--bg:#f6f5f2;--fg:#1d1d1f;--card:#fff;--line:#e3e1dc;--sub:#666}}@media (prefers-color-scheme:dark){{:root{{--bg:#151515;--fg:#eee;--card:#202020;--line:#333;--sub:#aaa}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,sans-serif}}main{{max-width:980px;margin:0 auto;padding:16px}}h1{{font-size:20px}}
table{{width:100%;border-collapse:collapse;background:var(--card)}}td{{border-bottom:1px solid var(--line);padding:6px;vertical-align:top}}td:first-child{{white-space:nowrap;font-weight:600}}
pre{{margin:0;white-space:pre-wrap;font:13px/1.45 system-ui,sans-serif}}.a0 td:first-child{{color:#1a7f37}}.a2 td,.a3 td,.a4 td{{color:var(--sub)}}a{{color:inherit}}</style></head><body><main>
<h1>元動画コメント 試し運転(投稿していない)</h1><p>{html.escape(summ)}。「投稿する」は新しい動画から1回 {MAX} 本まで、残りは翌日以降に回す。</p>
<table>{trs}</table></main></body></html>''')
    return path


MAX = 30


def main():
    global MAX
    ap = argparse.ArgumentParser(description="元動画コメント投稿")
    ap.add_argument("--dry-run", action="store_true", help="投稿せず一覧と確認ページだけ")
    ap.add_argument("--max", type=int, default=30, help="1回に投稿する上限(既定30)")
    args = ap.parse_args()
    MAX = args.max

    youtube = cta.get_service()
    me = youtube.channels().list(part="snippet", mine=True).execute()["items"][0]
    my_id = me["id"]
    print(f"[src] チャンネル: {me['snippet']['title']} ({my_id})" + ("  *** DRY-RUN ***" if args.dry_run else ""))

    videos = cta.get_public_videos(youtube)  # 新しい順
    sn = snippets(youtube, videos)
    # 概要欄の YouTube 動画のうち自チャンネル以外を元動画候補とする
    cand = {}
    for v in videos:
        ids = []
        for x in YT_ID.findall(sn.get(v, {}).get("description", "")):
            if x != v and x not in ids:
                ids.append(x)
        cand[v] = ids
    src_sn = snippets(youtube, sorted({x for ids in cand.values() for x in ids}))

    rows, posted = [], 0
    for v in videos:
        title = sn.get(v, {}).get("title", "")
        ext = [x for x in cand[v] if x in src_sn and src_sn[x]["channelId"] != my_id]
        if len(ext) == 0:
            rows.append(dict(id=v, title=title, action="元動画なし", text="", note=""))
            continue
        if len(ext) > 1:
            rows.append(dict(id=v, title=title, action="元動画が複数", text="", note=f"{len(ext)}本"))
            continue
        found, err = has_source_comment(youtube, v, my_id)
        if err:
            rows.append(dict(id=v, title=title, action="コメント不可", text="", note=err))
            continue
        text = comment_text(src_sn[ext[0]]["title"], ext[0])
        if found:
            rows.append(dict(id=v, title=title, action="済み", text=text))
            continue
        rows.append(dict(id=v, title=title, action="投稿する", text=text))
        if args.dry_run:
            continue
        if posted >= MAX:
            rows[-1]["action"] = "翌日以降"
            continue
        try:
            res = youtube.commentThreads().insert(part="snippet", body={"snippet": {
                "videoId": v, "topLevelComment": {"snippet": {"textOriginal": text}}}}).execute()
            print(f"  {v}: 元動画コメント投稿完了 ({res['id']})")
            posted += 1
            time.sleep(1)
        except Exception as e:
            print(f"  {v}: 投稿エラー: {e}")
            rows[-1]["action"] = "エラー"

    cnt = {}
    for r in rows:
        cnt[r["action"]] = cnt.get(r["action"], 0) + 1
    print("[src] " + " / ".join(f"{k} {n}" for k, n in cnt.items()))
    if args.dry_run:
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        print("[src] 確認ページ:", write_page(rows, stamp))
        json.dump(rows, open(os.path.join(PAGE_DIR, f"dryrun_{stamp}.json"), "w"), ensure_ascii=False, indent=1)
    else:
        print(f"[src] 新規投稿: {posted} 件")


if __name__ == "__main__":
    main()
