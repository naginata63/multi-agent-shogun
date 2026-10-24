---
name: thumbnail
description: |
  毎日ドズル社切り抜きの横長の動画(HL・ランキング・集計・縦断)のサムネを作り、YouTube に付けるまでを通す。
  動画の芯の問い→本編の実在の場面3つ→背景の手本→区画ごとに字なしの絵を codex(gpt-image)で描かせる(ref は登場する全員の三面図+背景)→区切りと字を後入れで組む→168pxの試験→殿が選ぶ→設定して maxres を目で見る。
  「サムネ」「サムネイル」「thumbnail」「/thumbnail」で起動。
  Do NOT use for: ショート(サムネは付けない)。漫画のコマ(それは /manga-short)。
argument-hint: "[video_id] [動画の芯の問い]"
allowed-tools: Bash, Read
---

# /thumbnail — 横長のサムネを作る

> **先に読め:** `shared_context/procedures/thumbnail_what_works.md`。回る作りの規則・崩れた規則・出す前の点検表はそこにある。この skill は作る手順だけを書く。
> 規則を変える時は thumbnail_what_works.md の方を直す。ここに写して二重にするな。

## North Star

- 168pxの一覧で、自chのほかの回と見分けがつき、誰が主役で何の場面かが絵だけで分かる1枚。
- 大見出しは動画の芯の問い。絵は本編に実在する場面。人物は三面図そのまま。
- 決めるのは殿。拙者は意匠を振った3案を出し、選ばれた1枚を付け、YouTube 側で目で見るまでやる。

## なぜこの作りか(殿の言葉の時系列)

- 2026-04-25 殿「しっぱい」「また３かいつくれ」「１せっとづつしかたのんでない」— 「3かい」は3案1セットを1回。出したら指示を待つ。
- 2026-05-23 殿「メガネに関する記述をするな」— 眼鏡は有無も形も色も書かぬ。
- 2026-07-02 殿「使用していいのは三面図だけ。表情はプロンプトで作成せよ」
- 2026-07-22 殿「公開判断はわしの仕事」
- 2026-07-30 殿「上半期は外せ 全期間だから　なんでつくりなおしたのにそうなったの」— 作り直す前に字の事実を照合する。
- 2026-07-31 殿「後ろ向いているのはありえない　違うパターンも作成せよ　全身映るのは小さくなるしだめ」
- 2026-08-08 殿「おまえgemini使うなよ意味わからん　codex cliしかずっと使ってないよ」
- 2026-08-21 殿「おんりーポンコツとは？ファンに喧嘩売るのか？」
- 2026-08-22 / 10-09 殿「1万円くらい課金されてた。別の手段検討しましょう」「金かかるから禁止 アカウント接続設定消せ」— Gemini は撤去。
- 2026-08-27 殿「ショートにサムネいつもつけてない」
- 2026-09-20 殿「表情はつかわない。三面図だけ使う。表情はプロンプトで指示する。何度も言っている。二度と起こすな」
- 2026-10-04 殿「何で背景削ったんいれたらいいじゃん」— ref を先回りで削らぬ。
- 2026-10-10 殿「さむね作ってないじゃん」— 横長の非公開アップはサムネまでが一式。
- 2026-10-20 殿「表情指定表現なんですかsmileなんちゃらって」「その英語タグのナレッジ消せ」
- 2026-10-23 殿「何だチェックは最後してないのね」— 伺うのは総点検済みの版だけ。
- 2026-10-24 合流縦断のサムネ作り直し(この順で直した):
  - 「サムネ作りも見直して欲しい そこが第一印象だから 回る動画のサムネはどうゆう作りなのか」— 74枚を検分し、thumbnail_what_works.md にまとめた。
  - 「ABCあわせれない？」— 主役1人の3案(A ぼん・B おんりー・C おんりーとおらふくん)を合わせ、斜め3分割(M2)ほか3つの組み方を出した。殿は M2。
  - 「m2構成でいいが キャッチコピーがおかしい 案だせ」「動画のコンセプトは？」— 見出しは芯の問いから。
  - 「えは書き直せ」— 台詞に合う顔とポーズにする。
  - 「えのたっちちがうけど三面図ちゃんと三人分いちまいずついれているのか？」— 生成した絵を ref に入れていた。
  - 「ベッドやめろ」— 要らぬ小道具は背景の手本からも切る。
  - 「これさ、文字あといれ？」「わくはみでてるよな」— 字は後入れ。
  - 「三面図いちまいずつわたせといったよな」— どの区画にも全員ぶんの三面図。
  - 「三面図をわたしているのか？ かくだいなんていらんとおもうが」— 顔の拡大は外す。
  - 「三面図とはどうゆうものかわかってる？」— 見た目をプロンプトに書かぬ。
  - 「かなりよくなったんだが　おらふが逃げてるように見えない」— 動きは体の向き・足・腕で書く。
  - 「1で」「それでいい つけて」— 非公開の v17(3qXvOKi2hnM)に付けた。

## 使う物

| 物 | 場所(リポジトリ直下から) |
|----|------|
| 区画の絵を描かせる | `projects/dozle_kirinuki/scripts/gouryu_thumbnail_panels_codex.sh` |
| 区切りと字を組む | `projects/dozle_kirinuki/scripts/gouryu_thumbnail_compose.py` |
| YouTube に付ける | `projects/dozle_kirinuki/scripts/youtube_uploader.py thumbnail` |
| 三面図(ref はこれだけ) | `projects/dozle_kirinuki/assets/dozle_jp/character/3views/{dozle,bon,qnly,orafu,oo_men,nekooji}_3views.png` |
| 字の書体(これ1つ) | `projects/dozle_kirinuki/assets/fonts/RanobePopB.otf` |
| 168pxの見比べ(自chの直近12本) | `projects/dozle_kirinuki/work/thumb_study/small/sheet_own.png` |
| レビューページ | `projects/dozle_kirinuki/analytics/dashboard/<名>/index.html` → `http://100.66.15.93:8080/<名>/` |
| ntfy | `scripts/ntfy.sh` |

- 2つの gouryu スクリプトは合流縦断1本ぶんの作りである。区画の中身(L_TXT など)・`HEADLINE`・`CAPS`・`LINES`・`CAP_BOTTOM` はスクリプトに書き込んである。見出しや台詞を引数では渡せない。
- 新しい動画では、2つとも新しい名前で写し(例 `<企画>_thumbnail_panels_codex.sh` `<企画>_thumbnail_compose.py`)、中を書き換えて使う。出力の dir(`T=`)も新しい企画の work の下に変える。

## 手順

### 1. 動画の芯の問いと見出し

- まず芯(視聴者が知りたい問い)を一行で書く。例(合流縦断):「姿も座標も見えない仲間と、どうやって合流してきたのか」。
- 大見出しはその問いか、問いへの引き。例:「見えない仲間と、どう合流する?」。
- 型の言葉(誰だ/TOP/ランキング/まとめ)より、出来事か台詞(規則3・参考)。
- 題とサムネで役目を分ける。題は出来事、サムネは芯の問い。題の売り・絵・大見出しが同じひとつの出来事を指すか確かめる。
- 小見出しは台詞か状況のどちらかに揃える。混ぜない。台詞は本家のテロップから引く。
- 見出しが、並べる場面すべてに当たるか確かめる。
- 件数・期間・固有名詞は、作る前に事実と照合する。前の版で通ったことは理由にならぬ。矛盾に気づいたら直してから作るか、作る前に殿に確かめる。
- メンバーを形容する言葉は、ファンがコメントで実際に使う呼称(コメントDBで確かめる)だけ。AIが作った腐しラベル(ポンコツ等)は禁止。
- しくじり(10-24): 最初の見出し「全員そろわなかった黄昏の森」は左の場面にしか当たらず、小見出しも状況と台詞が混ざった。次の「合流できない!!」は失敗を言うだけだった。

### 2. 場面を3つ選ぶ(本編の実在の秒・動画ID)

- 本編に実在する場面だけ。動画IDと秒を控える(例: 2022年回の82秒、苔むした廃墟で見回すぼんじゅうる)。
- 注目点はひとつ。主役1人か1組を手前・中央に。5人以上を同じ大きさで横に並べない(例外: 絵だけで題材が分かる舞台。逮捕王の鉄格子)。
- ネタバレ禁止。順位ものは1位を主役にしない。縦断・シリーズものは結末を主な絵にしない。
- 3案は意匠を振る。場面・主役・構図のどれかを案ごとに変える。同じプロンプトのガチャ3回にしない。
- 区画の台詞と、顔・ポーズを合わせる。「あれ?みんなどこ?」に叫ぶ顔は合わぬ(殿「えは書き直せ」)。
- ホットバー・地図・ログを絵に入れるなら、色・数・柄を本編と照合する。画面に無い記号(輪・枠線・矢印・空想の地図)を足さない。

### 3. 背景の手本を切り出す

```bash
cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
R=work/<企画>/thumb/ref; mkdir -p $R
ffmpeg -y -ss <秒> -i <本編.mp4> -frames:v 1 $R/bg_L.png
python3 - <<'PY'
from PIL import Image, ImageDraw
R = "work/<企画>/thumb/ref"
im = Image.open(f"{R}/bg_L.png").convert("RGB")
im = im.crop((x0, y0, x1, y1))   # 名前の帯・テロップ・HUD・要らぬ小道具を外す
d = ImageDraw.Draw(im)
d.rectangle((px0, py0, px1, py1), fill=(128, 128, 128))   # ゲームの肌の人物を最小限に
im.save(f"{R}/bgc_L.png")
PY
```

- 名前の帯・テロップ・HUD(ホットバー・体力など)を切り落とす。
- ゲームの肌の人物は灰色で塗りつぶす。範囲は最小に。灰色の四角をまねて描くことがある。プロンプトに「灰色の四角は人物を消した跡なので描くな」と書く。
- 場面に要らぬ小道具(ベッドなど)は背景の手本から切り落とし、プロンプトにも「描くな」と書く。例: `bgc_L.png` → `bgc_L_nobed.png`(殿「ベッドやめろ」)。
- 切った手本を Read で目で見てから使う。

### 4. 区画ごとに字なしの絵を codex で描かせる

写したスクリプトで書き換える所:

- `ALL3`: 登場する全員の三面図を一人一枚(縮めぬ原本)。**どの区画にも全員ぶん。**その区画に出ない人も画風の手本として入れ、`X_TXT` に「この区画に描くのは〜だけ(ほかは描くな)」と書く。出る人の分だけにしたら、ぼんじゅうるが老けて日焼けした顔になった(殿「三面図いちまいずつわたせといったよな」)。
- `L_REF` などの ref: `$ALL3` のあとに背景1枚だけ。
- `L_TXT` など: 添付の何枚目が誰か・描く人・場面・表情・ポーズ・構図。

プロンプトの決まり:

- 書くのは表情・ポーズ・構図・背景・場面だけ。
- 見た目(服・帽子・眼鏡・胸の花・色・雪だるまなど)は書かぬ。言い換えも要らぬ。眼鏡は有無も形も色も書かぬ。書くと、ずれた言葉の方へ絵が引っぱられる。見た目は `COMMON` の一文「人物は三面図の人物そのままに描け。三面図に無い物を足すな、ある物を省略するな」で足りる。三面図の画風(線・塗り・目の描き方)に従えも `COMMON` にある。
- 表情は日本語だけで「種類(強さ): 具体的な顔つき・手の動き」と書く。smile_r2 などの英語タグは使わぬ。
- 動きは体の向き・足・腕で書く。「振り返って驚く」だけでは、おらふくんの体がおんりーの方を向いて立ち止まった。直した書き方は `C_RUN`(体と足は右奥へ全力で走る・片足を後ろへ蹴り上げ・腕を前後に振り・上体を前へ倒す・顔だけ肩越しに振り返って両目が見える・足元に土ぼこり)。
- `COMMON` の構図はそのまま使う: 正方形1024x1024。正面〜斜め前・胸から上を大きく。顔は上から22%〜60%。上の20%に顔を入れぬ(見出し)。下の25%に顔や手の大事な所を置かぬ(台詞)。左右の端10%に顔を入れぬ(斜めに切る)。手に物を持たせぬ。字・数字・記号・吹き出し・枠線・白い区切り線・バッジ・英字・体力表示・血やグロを描かぬ。
- 顔は画面の高さの1/3以上。後ろ姿・真横・全身は禁止。縦長で描かせたら全身寄りで顔が小さくなった(L3/L4)。正方形のまま、顔と胸の目印の高さを数字で決める(`L_SQUARE`: 髪の頂点からあごまで高さの32%以上・あごは上から50%・胸元は55%〜72%。72%より下は台詞を重ねる所)。

ref の決まり:

- 渡すのは三面図と背景だけ。生成した絵(過去のサムネ・試作)・顔の拡大・縮めた複数人の三面図シート・表情差分(`selected/bust`・`expressions/gemini_v3`・`remotion-overlay/public/*_bust_rgba.png`)は入れぬ。構図の手本が要る時は言葉で書く。
- 「枚数が増えると薄まる」を理由に先回りで削らぬ。全部入れて描き、崩れた時だけ減らす。

走らせる:

```bash
cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
bash scripts/gouryu_thumbnail_panels_codex.sh panels_3v2        # L/B/C を2枚ずつ・3並列を2回 → L1,B1,C1,L2,B2,C2
bash scripts/gouryu_thumbnail_panels_codex.sh panels_Ls Ls      # 左だけ2枚(L5,L6)を描き直す。L_SQUARE は既定の L1/L2 にも入っている
bash scripts/gouryu_thumbnail_panels_codex.sh panels_3v2 C      # 右だけ・逃げる絵 → C3,C4,C5
```

- 第1引数は出力の dir 名(省くと panels)。第2引数は無し / `Ls` / `C` の3つだけ。それ以外の値(B・L・打ち間違い)は黙って既定の6枚を走らせる。区画を選ぶ引数は Ls と C しかない。
- 合流縦断で実際に描いた L5/L6 は `thumb_v2/panels/` に在る(`panels_3v2/` には無い)。
- 出力は `work/gouryu_yokonaga/thumb_v2/<出力dir名>/<名>.png`。在る物は `[SKIP]`。1枚ごとに `[OK]` か `[NG]`、最後に `PANELS_DONE`。
- 中身: `unset OPENAI_API_KEY`(ChatGPT のサブスク枠を使う)→ プロンプトを stdin で `timeout 900 codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox --image ...` に渡し、image_gen ツール(gpt-image)で保存させる。
- 1枚に最大15分かかる。Bash の run_in_background で走らせ、終わりの知らせを待つ。
- 既定は2枚ずつ・動きが肝の区画は3枚(`C` モード)。2枚の区画は良い方を取る。動きが肝の区画は3枚描かせ、一番その動きに見えて、主役が大きく、一覧の大きさでも誰か分かる1枚を取る(合流縦断の右は C3〜C5 から C4)。描き直しは新しい出力 dir 名で。前のセットは消さぬ。
- codex に実際に何枚の ref が渡ったかは、`~/.codex/sessions/<年>/<月>/<日>/rollout-*.jsonl` の user message の画像で確かめる。殿に問われたら、この記録で答える。

### 5. 1人ずつ三面図と並べて見る

```bash
cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
python3 - <<'PY'
from PIL import Image
a = Image.open("work/gouryu_yokonaga/thumb_v2/panels_3v2/L1.png").convert("RGB")
b = Image.open("assets/dozle_jp/character/3views/bon_3views.png").convert("RGB")
h = 1024
a = a.resize((round(a.width * h / a.height), h)); b = b.resize((round(b.width * h / b.height), h))
c = Image.new("RGB", (a.width + b.width, h), "white"); c.paste(a, (0, 0)); c.paste(b, (a.width, 0))
c.save("work/gouryu_yokonaga/thumb_v2/cmp_L1_bon.png")
PY
```

- できた並べ画像を Read で開き、顔・髪・服・色・小物を三面図と照合する。三面図に無い装飾を足したり、三面図にある物(胸の花・頭の雪だるまなど)を落としたりする癖がある。崩れた字(シャツの『ぼ』など)は描き直す。
- 顔の大きさと向き(正面〜斜め前・胸から上・高さの1/3以上)も見る。
- 一覧の大きさに縮めても誰か分かるか見る。

### 6. 区切りと字を後入れで組む

写した compose.py で書き換える所(合流縦断の値):

| 定数 | 値 | 意味 |
|------|----|------|
| `HEADLINE` | `見えない仲間と、どう合流する?` | 黄 (255,228,0)・黒縁 size//8。全幅1行。150px から縮めて幅 W-120 に収める。上端 y≈60。「、」「。」の送りは0.55に詰める |
| `CAPS` | L=`あれ?` / `みんなどこ?`(白)・B=`嫌だ!!!!!`(赤 (235,20,20)・白の中の縁)・C=`おい止まれ!`(白) | 区画: 台詞の行・字の色・中の縁 |
| `LINES` | `[(690,570),(1220,1100)]` | 斜めの区切りの上端xと下端x。左約33%・中約28%・右約40%(右は2人ゆえ広く) |
| `CAP_BOTTOM` | L=1045・B=1000・C=975 | 台詞の下端。右下の再生時間の札(y≥990)に被るのは右の区画だけ |
| `LINE_W` / `MARGIN` | 16 / 36 | 白い区切り16px(下に幅22pxの黒線を敷き、両側3pxの黒縁)/ 区切りから字までの空き |

```bash
cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
P=work/gouryu_yokonaga/thumb_v2/panels_3v2; O=work/gouryu_yokonaga/thumb_v2/composed_3v2; mkdir -p $O
python3 scripts/gouryu_thumbnail_compose.py $P/L1.png $P/B2.png $P/C4.png $O/final_c4.jpg --off L=0,-60,1.12 --off C=-95,0,1.0
ls -l $O/final_c4.jpg    # 2MB 未満か
```

- 出力は `final_c4.jpg`(1280x720・quality 92)と `final_c4_1920.png`(1920x1080)。表示は `[headline] Npx`・`[cap] K Npx`・KB。
- `--off K=dx,dy,scale`(K は L/B/C・何度でも・既定 0,0,1.0)。dx,dy は区画の中心からのずらし(px・1920x1080 基準)。scale は絵の拡大率(1.0 で高さ1080)。
- 合わせ方:
  - 顔や胸の目印が台詞に隠れる → dy を負にして絵を上げるか、scale を上げる(L=0,-60,1.12)。
  - 顔が斜めの区切りに切れる → dx で区画の内側へ寄せる(C=-95,0,1.0)。
  - 絵を縮めて区画に隙間ができた所は、同じ絵のぼかし(GaussianBlur 28)で埋まる。
  - 値を2〜3通り組み(`t_L1_1.jpg` など)、並べて目で選ぶ。
- 台詞は、その高さで区画の内側に取れる幅に収まる大きさまで。`fit_caption` が140pxから2pxずつ縮め、行の上端と下端の両方で収まる大きさを取る。どこまで縮めても収まらねば「台詞が区画に収まらぬ」で止まる。長い台詞は2行に割る(あれ? / みんなどこ?)。
- 右下の再生時間の札(1920基準で y≥990)に字を被せない。
- compose は2MBを確かめぬ。`ls -l` で自分で見る。超えたら JPEG の quality を下げる。
- 区画に分けず1枚で描かせた 3:2(1536x1024)の絵を16:9にする時だけ、次を使う。中央クロップ(`crop=iw:iw*9/16`)は端の字や札が切れるので禁止。

```bash
ffmpeg -y -i in.png -filter_complex "[0:v]crop=1536:928:0:48[c];[c]split[a][b];[a]scale=1650:928,boxblur=24:3[bg];[bg][b]overlay=57:0,scale=1280:720" -q:v 2 out.jpg
```

### 7. 168pxの試験(自chの直近と並べる)

```bash
cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
python3 - <<'PY'
from PIL import Image
s = Image.open("work/thumb_study/small/sheet_own.png").convert("RGB")   # 自chの直近12本
t = Image.open("work/gouryu_yokonaga/thumb_v2/composed_3v2/final_c4.jpg").convert("RGB")
t = t.resize((168, round(168 * t.height / t.width)), Image.LANCZOS)
c = Image.new("RGB", (s.width, s.height + t.height + 20), "white")
c.paste(s, (0, 0)); c.paste(t, (0, s.height + 20))
c.save("work/gouryu_yokonaga/thumb_v2/composed_3v2/test168_c4.png")
PY
```

- Read で開き、4点を見る: ほかの回と見分けがつくか・主役が誰か・大見出しが読めるか・何の場面か。
- 1つでも落ちたら直す。直したら最初から点検表(thumbnail_what_works.md)を通す。

### 8. レビューページと ntfy で殿に出し、殿が選ぶ

- 意匠を振った3案を `projects/dozle_kirinuki/analytics/dashboard/<名>/index.html` に並べる。各案に番号・使った場面(動画ID・秒)・168px版を添える。
- ntfy は URL だけ送る。画像は添付せぬ。

```bash
cd /home/murakami/multi-agent-shogun
bash scripts/ntfy.sh "合流縦断サムネ 3案 http://100.66.15.93:8080/gouryu_v1/"
```

- 殿が番号を選ぶ。拙者は推しを一言添えてよいが、独断で決めぬ。点数は参考にしかならぬ。組み方を変えた時も数字だけで報告せず、比べ画で見せる。
- 殿の「3かい作れ」は3案1セットを1回。出したら指示を待つ。続けて作らぬ。
- 伺うのは、thumbnail_what_works.md の点検表を全部通した版だけ。
- 「送った」を「届いた」と言わぬ。届いていないと言われたら、すぐ URL を本文に入れて送り直す。

### 9. youtube_uploader.py thumbnail で付け、maxres を取り直して目で見る

```bash
cd /home/murakami/multi-agent-shogun/projects/dozle_kirinuki
python3 scripts/youtube_uploader.py thumbnail 3qXvOKi2hnM work/gouryu_yokonaga/thumb_v2/composed_3v2/final_c4.jpg
python3 - <<'PY'
import sys, urllib.request
sys.path.insert(0, "scripts")
from youtube_uploader import get_authenticated_service
yt = get_authenticated_service()
it = yt.videos().list(part="snippet,status", id="3qXvOKi2hnM").execute()["items"][0]
print(it["status"]["privacyStatus"], it["snippet"]["title"])
th = it["snippet"]["thumbnails"]
k = next(k for k in ("maxres", "standard", "high") if k in th)   # 処理中は maxres がまだ無い
u = th[k]["url"]
print(k, u)
urllib.request.urlretrieve(u, "work/gouryu_yokonaga/thumb_v2/composed_3v2/yt_readback.jpg")
PY
```

- `yt_readback.jpg` を Read で開いて目で見る。API の成功応答だけで確認済みとせぬ。
- 表示された大きさの名(maxres・standard・high)が maxres でなければ、まだ処理中。CDN がしばらく古い絵を配ることもある。古い絵なら数分待ち、URL に `?t=<時刻>` を付けて取り直す。新しい絵が見えるまで済みとせぬ。
- uploader は OAuth(`token.json`・切れていれば更新)で入り、`channels().list(mine=True)` で接続先 ch を表示してから `thumbnails().set` を呼ぶ。mimetype は JPEG でも image/png 固定で送る(それで通る)。
- 2MB を超えると `MediaUploadSizeError`。PNG で失敗する前に、1280x720 の JPEG にしてから上げる。
- `invalid_grant` が出たら、`python3 scripts/reauth_phone.py url`(projects/dozle_kirinuki で)の URL だけを ntfy で殿へ送る。先送りせぬ。
- HL を `youtube_uploader.py auto` で上げる時、work_dir に thumbnail.png が在ると黙って付く。殿が選んだ版以外を置くな(置くなら上げた後に thumbnail で付け直し maxres を見る)。
- 横長の非公開アップは、ここまでで一式。本編URLだけで報告を終えぬ。
- 公開は殿の明示の指示まで出さぬ。サムネを付けても公開判断は殿の専権。
- 公開後、1日後と7日後の再生を、同じ月の自chの回と並べて記録する(点検表11)。

## やってはならぬこと

- ショート(漫画ショート・表情ショートなど)にサムネを作る・付ける。完了報告の残課題にも書かぬ。サムネが要るのは横長だけ。
- 絵を描く AI に字を描かせる。
- 生成した絵(過去のサムネ・試作)を ref に入れる。
- ref に顔の拡大・縮めた複数人シート・表情差分バスト・既製の表情 PNG を使う。
- 区画に出る人の三面図だけを渡す(全員ぶん渡す)。
- プロンプトに見た目(服・帽子・眼鏡・花・色)を書く。英語の表情タグを書く。
- 「薄まる」を理由に三面図や背景を先回りで削る。
- 本編に無い場面・作り物のホットバー・画面に無い記号を描く。
- 個人の回数バッジ・天使の輪・英字バッジ・血やグロを入れる。
- 順位ものの1位、縦断の結末を主役にする。5人以上の同じ大きさの横並び。
- 同じプロンプトのガチャ3回を「3案」として出す。
- 16:9 にする時の中央クロップ。2MB を確かめずに上げる。
- AI が独断でサムネを選ぶ。総点検していない版で殿に伺う。
- 殿の指示なしに公開する。
- Gemini / Vertex と `generate_manga_short.py` を使う。
- 関連: クリップに重ねる札も人物の顔に被せぬ(殿「コメントが顔に被らないようにせよ おらふの三つ目被ってた」2026-10-17)。

## 旧式(使わぬ)

- `make_thumbnail_auto.py`(旧 /thumbnail): Gemini Vision の背景選び・Gemini Text の文案・Embedding 2 の表情マッチング・viability_score が前提。Gemini は接続設定ごと撤去したので動かぬ(2026-08-22 / 10-09)。文案は芯の問いから起こす。
- `projects/dozle_kirinuki/scripts/archive/generate_thumbnail.py`(DoZ の Gemini 手順・`shared_context/procedures/dozle_thumbnail_generation.md` の `--hero` `--ref-limit 0` `--count 3` など): 同じく Gemini 前提。主役を手前・中央に置くこと(規則1)は今も生きるが、codex のプロンプトで書く。
- `projects/dozle_kirinuki/scripts/manga_poc/generate_manga_short.py`(Gemini / Vertex の漫画コマ生成): サムネにも使わぬ。描くのは codex。
- Gemini / Vertex での画像生成と検分: 月1万円の課金で撤去。描くのは codex、検分はローカルの Qwen2.5-VL(ollama)と自分の目。
- 表情立ち絵(`selected/bust` などの表情差分)の合成・ref: 殿「表情はつかわない。三面図だけ使う」(2026-09-20)。表情はプロンプトで指示する。
- 顔の拡大(`face_*.png`・三面図の左上36%×30%を600px幅に)を三面図のあとに添える: 拙者が 09-15 の「6人シートを縮めたら顔が崩れた」件から作った決まりで、殿の決まりではない。殿「かくだいなんていらんとおもうが」(2026-10-24)。
- 複数人の三面図シート(members6_sheet・members6_faces): 縮めると顔が崩れる。一人一枚の原本を渡す。
- ref は最大4枚: 拙者の経験則。殿「何で背景削ったんいれたらいいじゃん」(2026-10-04)。
- 絵と一緒に字も描かせる(`gouryu_thumbnail_v2_codex.sh`・1536x1024・字の置き場をプロンプトに書く): 字が毎回変わり崩れ、台詞が斜めの区切りを越えた。殿「わくはみでてるよな」(2026-10-24)。「字も codex に描かせ後乗せしない」(2026-06-04 殿「codexは日本語強い」)は、サムネについてはこれで改めた。
- 過去のサムネを ref に渡す(総集編のフルイラスト調・`--ref-dir` の DoZ サムネ): 画風と型がそちらへずれる。stdin でプロンプトを渡す作りだけは今も使う。
- 順位ものを全員同じ大きさの横一列・正面の顔アップで並べる(2026-10-10): 横並びは回らない(規則1)。
- 「文字は2つまで」(2026-10-10): 字数に差は出なかった(規則2)ので決まりとしない。禁止物(バッジ・輪・英字・グロ)は今も禁止。
- `--text-mode suggest` で文案5つ: 文案は芯の問いから拙者が起こし、殿に見せる。
- `output/{cmd_id}/thumbnail/thumbnail_{A,B,C}.png` と `thumbnail_meta.json` の置き方・家老への起票: 将軍システムは廃止(2026-08-21)。企画の work の下に dir を切り、直接作る。
- DoZ(コラボ回)のメンバー構成・ゴーグル版の立ち絵のメモ(2026-04-25): Gemini 手順のためのもの。DoZ のサムネを作る時は、その回の本編で確かめ直す。
