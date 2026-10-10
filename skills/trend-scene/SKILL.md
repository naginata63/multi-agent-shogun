---
name: trend-scene
description: |
  いま追い風が吹いておる本家の場面を、他の切り抜きchの実測(再生/日)から見つけて殿に出す。
  切り抜き・ショートの題材を決める最初の工程。後発でもシーンに追い風があれば回る(2026-08-14 殿方針)。
  「はやり」「流行り」「今なにが伸びてる」「追い風」「流行りのシーン」「他chは何やってる」
  「ネタ探し」「題材」「trend」「/trend-scene」で起動。
  古い回から探し始める前に必ずこれを先に回せ。
  Do NOT use for: 自chの再生数分析(それは /youtube-stats)。場面が決まった後の制作(それは /manga-short-workflow)。
argument-hint: "[--days 10]"
allowed-tools: Bash, Read
---

# /trend-scene — 流行りシーン検知

## North Star

**題材は勘で選ぶな。他chの実測(再生/日)で、いま追い風が吹いておる本家の場面を先に特定せよ。**

## なぜ要るか

2026-08-14 殿方針: ぼん死因ショートは他chが2日先行した同シーンを、9日遅れの漫画動画で出して23万再生。
**シーンに追い風が吹いておる時は後発でも回る**。ゆえに「流行りのシーンを真似る」を仕組みにする。

2026-10-10 の失敗: 殿「ショート企画けんとうせよ」に対し、7〜9月の古い回のコメントから候補を作って献上。
殿「はやりは？」。流行り検知は毎日動いておったのに見もせなんだ。**入口はここでござる。**

## 手順

1. 最新の走査結果を読む（毎日 09:50 に cron で走っておる）
   ```bash
   cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
   python3 - <<'E'
   import json
   d=json.load(open('work/trend/latest.json'))
   rows=[s for s in d if s.get('src') and not s.get('covered')]
   rows.sort(key=lambda s:-s['vpd'])
   for s in rows[:8]:
       print(f"{s['vpd']:>9,.0f}/日 {s['n_ch']}ch {s['src']['date']} {s['key']} {s['src']['title'][:44]}")
       for sh in s['shorts'][:3]: print(f"    {sh.get('views',0):>8,} [{sh.get('ch','')[:16]}] {sh['title'][:56]}")
   E
   ```
   古ければ `python3 scripts/trend_scan.py --days 10` で取り直す。

2. 読み方
   - `vpd` = 再生/日。追い風の強さ
   - `n_ch` = 追っておるch数。**少ないほど空いておる**（1chなら狙い目、4chなら二番手以降）
   - `covered` = 自chが既に出した場面（true は除外済み）
   - `key` = 本家の video_id。素材はここから自前で切る

3. 殿に出す（上位5〜8件・表で）。**選ぶのは殿**。AIが勝手に決めるな

4. 殿が選んだら本家をDL
   ```bash
   venv/bin/yt-dlp --cookies /home/murakami/ダウンロード/www.youtube.com_cookies.txt \
     --js-runtimes node:/home/murakami/.nvm/versions/node/v20.20.0/bin/node \
     --write-auto-sub --sub-lang ja --no-progress \
     -f "299+bestaudio[ext=m4a]/137+bestaudio/best[height<=1080]/best" --merge-output-format mp4 \
     -o "work/<project>/%(id)s.%(ext)s" "https://youtu.be/<video_id>"
   ```

5. その回の中の場面を絞る（二段構え）
   - **視聴者の時刻つきコメント**を取る: `python3 scripts/comment_db.py fetch --since <日付> --max-pages 3`
     → `work/comment_db/raw/<vid>.json` の本文から `(\d+):(\d\d)` を拾い、♥順に並べる
   - **他chが伸ばした場面**（手順1の shorts タイトル）と突き合わせる
   - ♥はコメントの人気であって場面の面白さではない。**感心・萌え系が混じる**ので、掛け合いとオチがあるものを選べ
   - 候補は30秒ずつ切り出し、音つきで再生できるページにして殿に出す

6. 場面が決まったら `/manga-short-workflow` の Phase2 へ渡す

## 掟

- 他chのショートは**題材の信号としてのみ**使う。映像の再切り抜きは規約違反。採用時は**本家の横長本編から自前で切る**
- 自chが既に出した場面（`covered`）は出すな
- 「シーンが新しく・追っておるchが少ない」ほど価値が高い

## アンチパターン

| NG | 理由 | 正しくは |
|----|------|---------|
| 古い回から探し始める | 追い風が無い | まず latest.json を見る |
| ♥の数だけで決める | 感心・萌え系が混じる | 掛け合いとオチで絞る |
| AIが場面を決める | 殿の掟に反する | 候補を出して殿が選ぶ |
| 他chの映像を切る | 規約違反 | 本家本編から自前で切る |
