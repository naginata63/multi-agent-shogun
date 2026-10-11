#!/usr/bin/env python3
"""なぎなた(note記事の案内役)のマインクラフトスキンを 64x64 PNG で起こす。

元デザイン: projects/note_mcp_server/assets/naginata_tachie.png
  白髪ショート / 緑の瞳 / 赤いマフラー / 青いロングコート / 左肩に革の肩当て /
  オリーブのチュニック / 赤いベルト+金のバックル / 赤いショルダーバッグ /
  生成りのパンツ / 編み上げの茶色ブーツ(赤い紐)

出力:
  projects/note_mcp_server/assets/naginata_skin.png        … スキン本体 (64x64 RGBA)
  projects/note_mcp_server/assets/naginata_skin_preview.png … 確認用の前/後ろ姿 + 展開図
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "projects/note_mcp_server/assets/naginata_skin.png")
PRV = os.path.join(ROOT, "projects/note_mcp_server/assets/naginata_skin_preview.png")

# ─── 配色 ────────────────────────────────────────────────────────────────
C = {
    "hair":   (232, 236, 240, 255), "hair_s": (214, 220, 228, 255), "hair_d": (166, 177, 190, 255),
    "skin":   (242, 201, 160, 255), "skin_s": (220, 174, 134, 255), "skin_d": (190, 143, 104, 255),
    "eye_w":  (255, 255, 255, 255), "eye":    ( 62, 176, 140, 255), "eye_d":  ( 36, 122,  96, 255),
    "mouth":  (176, 110,  90, 255),
    "scarf":  (192,  57,  43, 255), "scarf_d":(150,  39,  28, 255), "scarf_l":(217,  81,  63, 255),
    "coat":   ( 46,  95, 138, 255), "coat_d": ( 32,  70, 104, 255), "coat_l": ( 62, 122, 173, 255),
    "tunic":  ( 74,  79,  66, 255), "tunic_d":( 56,  60,  50, 255),
    "pad":    (168, 124,  74, 255), "pad_d":  (133,  96,  58, 255),
    "belt":   (179,  58,  43, 255), "buckle": (201, 162,  39, 255),
    "bag":    (181,  54,  44, 255), "bag_d":  (142,  40,  33, 255),
    "pants":  (230, 220, 195, 255), "pants_s":(205, 194, 166, 255),
    "boot":   (139,  90,  43, 255), "boot_d": (105,  66,  32, 255), "lace": (200, 70, 55, 255),
    "none":   (0, 0, 0, 0),
}

img = Image.new("RGBA", (64, 64), C["none"])
d = ImageDraw.Draw(img)


def box(x, y, w, h, c):
    """スキン座標 (左上原点) に w×h の矩形を塗る。"""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=C[c] if isinstance(c, str) else c)


def px(x, y, c):
    img.putpixel((x, y), C[c] if isinstance(c, str) else c)


# ─── 頭 (base layer) ────────────────────────────────────────────────────
# top / bottom
box(8, 0, 8, 8, "hair")                    # 頭頂はすべて白髪
# 頭頂の陰は一列の帯にせず、毛束のまだらで付ける(帯は立体で段差に見える)
for x, y in ((9, 1), (12, 0), (14, 2), (10, 5), (13, 6)):
    px(x, y, "hair_s")
box(16, 0, 8, 8, "skin_s")                 # 顎の裏

for bx, side in ((0, "right"), (16, "left"), (24, "back"), (8, "front")):
    box(bx, 8, 8, 8, "skin")

# 側面・後頭部の髪
# 右側面(0,8): x=7 が顔側 / 左側面(16,8): x=16 が顔側
box(0, 8, 8, 4, "hair"); box(0, 12, 4, 4, "hair")    # 後ろ半分は襟足まで髪
for x, y in ((1, 9), (3, 11), (5, 10), (2, 13), (6, 12)):   # 毛束のまだら+もみあげ
    px(x, y, "hair_s")
box(16, 8, 8, 4, "hair"); box(20, 12, 4, 4, "hair")
for x, y in ((22, 9), (20, 11), (18, 10), (21, 13), (17, 12)):
    px(x, y, "hair_s")
box(24, 8, 8, 7, "hair")                    # 後頭部はほぼ髪
for x, y in ((25, 10), (28, 12), (30, 9), (26, 14), (29, 14)):
    px(x, y, "hair_s")
box(24, 15, 8, 1, "skin_s")                 # うなじ

# 正面
box(8, 8, 8, 3, "hair")                     # 前髪
px(8, 11, "hair"); px(9, 11, "hair")        # こめかみの毛先
px(14, 11, "hair"); px(15, 11, "hair")
px(11, 11, "hair_s"); px(12, 11, "hair_s")  # 中央の毛束
# 目 (緑)
px(9, 12, "eye_w"); px(10, 12, "eye")
px(13, 12, "eye"); px(14, 12, "eye_w")
px(10, 13, "eye_d"); px(13, 13, "eye_d")
# 口
px(11, 14, "mouth"); px(12, 14, "mouth")
px(8, 15, "skin_s"); px(15, 15, "skin_s")   # 顎の陰

# ─── 頭 2層目 (hat) は空のまま ─────────────────────────────────────────
# 2層目は本体より一回り大きく描かれるゆえ、髪を途中の段までしか置かぬと
# その切れ目が頭の段差になって見える(2026-10-11 殿「スキン頭に段差ができている」)。
# 髪とマフラーはすべて本体レイヤーに描き、頭の2層目は透明で残す。

# ─── 胴 (base) ──────────────────────────────────────────────────────────
box(20, 16, 8, 4, "scarf")                   # 肩の上 = マフラー
box(28, 16, 8, 4, "tunic_d")                 # 腰の裏

# 正面 (20,20) 8x12
box(20, 20, 8, 12, "tunic")                  # まずチュニック
box(20, 20, 2, 12, "coat"); box(26, 20, 2, 12, "coat")   # 左右にコートの前身頃
box(20, 20, 8, 2, "scarf")                   # 首元のマフラー
px(23, 22, "scarf"); px(24, 22, "scarf")     # マフラーの垂れ
px(23, 23, "scarf_d"); px(24, 23, "scarf_l")
px(23, 24, "scarf_d")
box(20, 26, 8, 1, "belt")                    # ベルト
px(23, 26, "buckle"); px(24, 26, "buckle")
box(20, 29, 8, 3, "coat_d")                  # 裾の陰
for i, (bx, by) in enumerate([(22, 22), (23, 23), (24, 24), (24, 25), (25, 26)]):
    px(bx, by, "bag_d")                      # 斜め掛けの革帯

# 背面 (32,20) 8x12
box(32, 20, 8, 12, "coat")
box(32, 20, 8, 2, "scarf")
box(32, 29, 8, 3, "coat_d")
for bx, by in [(33, 22), (34, 23), (35, 24), (36, 25), (37, 26)]:
    px(bx, by, "bag_d")

# 右側面 (16,20) 4x12 / 左側面 (28,20) 4x12
box(16, 20, 4, 12, "coat"); box(16, 20, 4, 2, "scarf"); box(16, 29, 4, 3, "coat_d")
box(28, 20, 4, 12, "coat"); box(28, 20, 4, 2, "scarf"); box(28, 29, 4, 3, "coat_d")
box(28, 25, 3, 4, "bag")                     # 左腰の赤い鞄
box(28, 25, 3, 1, "bag_d"); px(29, 27, "buckle")

# ─── 胴 2層目: マフラーの厚みと鞄 ──────────────────────────────────────
B = 16                                        # body overlay は y+16
box(20, 16 + B, 8, 4, "scarf")
box(20, 20 + B, 8, 2, "scarf")                # 正面の襟巻き
px(23, 23 + B, "scarf_d"); px(24, 23 + B, "scarf_l")
px(23, 24 + B, "scarf_d")
box(32, 20 + B, 8, 2, "scarf")                # 背面
box(16, 20 + B, 4, 2, "scarf")
box(28, 20 + B, 4, 2, "scarf")
box(28, 25 + B, 3, 4, "bag")                  # 鞄の張り出し
box(28, 25 + B, 3, 1, "bag_d")

# ─── 右腕 (キャラの右・青い袖+茶の手甲) base (40,16) ────────────────────
box(44, 16, 4, 4, "coat")                     # 肩の上
box(48, 16, 4, 4, "skin_s")                   # 手のひら側
for bx in (40, 44, 48, 52):
    box(bx, 20, 4, 12, "coat")
    box(bx, 20, 4, 1, "coat_l")
    box(bx, 27, 4, 2, "pad")                  # 手甲
    box(bx, 28, 4, 1, "pad_d")
    box(bx, 29, 4, 3, "skin")
    box(bx, 31, 4, 1, "skin_s")

# ─── 左腕 (キャラの左・肩当てあり) base (32,48) ─────────────────────────
box(36, 48, 4, 4, "pad")                      # 肩当ての上面
box(40, 48, 4, 4, "skin_s")
for bx in (32, 36, 40, 44):
    box(bx, 52, 4, 12, "coat")
    box(bx, 52, 4, 3, "pad")                  # 革の肩当て
    box(bx, 54, 4, 1, "pad_d")
    px(bx + 1, 53, "buckle")
    box(bx, 61, 4, 3, "skin")
    box(bx, 63, 4, 1, "skin_s")

# ─── 脚 (生成りのパンツ + 編み上げブーツ) ────────────────────────────────
def leg(bx, by):
    box(bx + 4, by, 4, 4, "pants")            # top
    box(bx + 8, by, 4, 4, "boot_d")           # bottom = 靴底
    for fx in (bx, bx + 4, bx + 8, bx + 12):
        box(fx, by + 4, 4, 12, "pants")
        box(fx, by + 9, 4, 7, "boot")         # 膝下はブーツ
        box(fx, by + 9, 4, 1, "boot_d")       # ブーツの履き口
        px(fx + 1, by + 11, "lace"); px(fx + 2, by + 13, "lace")
        box(fx, by + 15, 4, 1, "boot_d")

leg(0, 16)    # 右脚
leg(16, 48)   # 左脚

# ─── 脚 2層目: 膝まで届く青いコートの裾 ─────────────────────────────────
def coat_tail(bx, by):
    for fx in (bx, bx + 4, bx + 8, bx + 12):
        box(fx, by + 4, 4, 3, "coat")
        box(fx, by + 6, 4, 1, "coat_d")

coat_tail(0, 32)    # 右脚 overlay
coat_tail(0, 48)    # 左脚 overlay

img.save(OUT)

# ─── 確認用プレビュー (前/後ろ姿 + 展開図) ──────────────────────────────
def face(x, y, w, h):
    return img.crop((x, y, x + w, y + h))


def over(base, top):
    out = base.copy()
    out.alpha_composite(top)
    return out


S = 14  # 1px あたりの拡大率
def paste_scaled(canvas, tile, cx, cy):
    canvas.alpha_composite(tile.resize((tile.width * S, tile.height * S), Image.NEAREST), (cx * S, cy * S))


# 前姿: 頭(8x8) 胴(8x12) 腕(4x12)x2 脚(4x12)x2 → 16x32 の枠
def doll(front=True):
    cv = Image.new("RGBA", (16 * S, 32 * S), (0, 0, 0, 0))
    hx = 8 if front else 24
    paste_scaled(cv, over(face(hx, 8, 8, 8), face(hx + 32, 8, 8, 8)), 4, 0)
    bx = 20 if front else 32
    paste_scaled(cv, over(face(bx, 20, 8, 12), face(bx, 36, 8, 12)), 4, 8)
    # 腕 (前から見て 左に右腕 / 右に左腕・背面は左右逆)
    ra = face(44, 20, 4, 12)
    la = over(face(36, 52, 4, 12), face(52, 52, 4, 12))
    if not front:
        ra = face(52, 20, 4, 12)
        la = over(face(44, 52, 4, 12), face(60, 52, 4, 12))
    paste_scaled(cv, ra if front else la, 0, 8)
    paste_scaled(cv, la if front else ra, 12, 8)
    rl = over(face(4, 20, 4, 12), face(4, 36, 4, 12))
    ll = over(face(20, 52, 4, 12), face(4, 52, 4, 12))
    if not front:
        rl = over(face(12, 20, 4, 12), face(12, 36, 4, 12))
        ll = over(face(28, 52, 4, 12), face(12, 52, 4, 12))
    paste_scaled(cv, rl if front else ll, 4, 20)
    paste_scaled(cv, ll if front else rl, 8, 20)
    return cv


def side():
    """右から見た姿 (側面の面だけで組む)"""
    cv = Image.new("RGBA", (16 * S, 32 * S), (0, 0, 0, 0))
    paste_scaled(cv, over(face(0, 8, 8, 8), face(32, 8, 8, 8)), 4, 0)
    paste_scaled(cv, over(face(16, 20, 4, 12), face(16, 36, 4, 12)), 6, 8)
    paste_scaled(cv, face(40, 20, 4, 12), 6, 8)
    paste_scaled(cv, over(face(0, 20, 4, 12), face(0, 36, 4, 12)), 6, 20)
    return cv


f, b = doll(True), doll(False)
sd = side()
sheet = img.resize((64 * 6, 64 * 6), Image.NEAREST)
W = f.width + sd.width + b.width + sheet.width + 5 * 36
prev = Image.new("RGBA", (W, max(f.height, sheet.height) + 40), (28, 30, 36, 255))
for i, t in enumerate((f, sd, b)):
    prev.alpha_composite(t, (36 * (i + 1) + f.width * i, 20))
prev.alpha_composite(sheet, (36 * 4 + f.width * 3, 20))
prev.convert("RGB").save(PRV)

print(f"[DONE] {OUT}  {img.size} {img.mode}")
print(f"[DONE] {PRV}  {prev.size}")
