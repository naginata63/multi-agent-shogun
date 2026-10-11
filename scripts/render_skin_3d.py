#!/usr/bin/env python3
"""マインクラフトのスキン(64x64)を斜め上からの立体で描き、2層目の段差まで目で確かめる。

平面の前/後ろ姿だけでは、2層目(本体より一回り大きく描かれる)の切れ目による
段差が見えぬ。正射影で箱を組み、2層目は実機どおり膨らませて重ねる。

使い方: python3 scripts/render_skin_3d.py <skin.png> <out.png>
"""
import math
import sys

from PIL import Image

S = 14                       # 1ブロック画素あたりの出力画素
INF_HEAD, INF_BODY = 0.5, 0.25   # 2層目の膨らみ (実機の値)

# 部位: (x0,x1, y0,y1, z0,z1), 1層目UV原点, 2層目UV原点, (幅,高さ,奥行き)
# UV原点は「右面」の左上から数えた展開図の基準点 (u, v)
PARTS = [
    # name,        box,                        base uv,  overlay uv, inflate
    ("right_leg",  (-4, 0, 0, 12, -2, 2),      (0, 16),  (0, 32),   INF_BODY),
    ("left_leg",   (0, 4, 0, 12, -2, 2),       (16, 48), (0, 48),   INF_BODY),
    ("body",       (-4, 4, 12, 24, -2, 2),     (16, 16), (16, 32),  INF_BODY),
    ("right_arm",  (-8, -4, 12, 24, -2, 2),    (40, 16), (40, 32),  INF_BODY),
    ("left_arm",   (4, 8, 12, 24, -2, 2),      (32, 48), (48, 48),  INF_BODY),
    ("head",       (-4, 4, 24, 32, -4, 4),     (0, 0),   (32, 0),   INF_HEAD),
]


def face_rects(u, v, w, h, d):
    """展開図上の各面の矩形 (left, top, width, height)。w=幅(x) h=高さ(y) d=奥行き(z)"""
    return {
        "top":   (u + d, v, w, d),
        "right": (u, v + d, d, h),
        "front": (u + d, v + d, w, h),
        "left":  (u + d + w, v + d, d, h),
        "back":  (u + d + w + d, v + d, w, h),
    }


def corners(face, x0, x1, y0, y1, z0, z1):
    """テクスチャの 左上/右上/左下 に当たる3D点 (人物は +z を向く)"""
    return {
        "front": ((x0, y1, z1), (x1, y1, z1), (x0, y0, z1)),
        "right": ((x0, y1, z0), (x0, y1, z1), (x0, y0, z0)),
        "left":  ((x1, y1, z1), (x1, y1, z0), (x1, y0, z1)),
        "back":  ((x1, y1, z0), (x0, y1, z0), (x1, y0, z0)),
        "top":   ((x0, y1, z0), (x1, y1, z0), (x0, y1, z1)),
    }[face]


def make_cam(yaw, pitch):
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def cam(p):
        x, y, z = p
        x, z = x * cy + z * sy, -x * sy + z * cy          # 鉛直軸まわり
        y, z = y * cp - z * sp, y * sp + z * cp            # 見下ろし
        return x, y, z
    return cam


def render(skin, yaw, pitch, size):
    cam = make_cam(yaw, pitch)
    cx, cy = size[0] / 2, size[1] * 0.93
    to2d = lambda p: (cx + p[0] * S, cy - p[1] * S)
    faces = []
    for _name, (x0, x1, y0, y1, z0, z1), buv, ouv, inf in PARTS:
        w, h, d = x1 - x0, y1 - y0, z1 - z0
        for layer, uv, k in ((0, buv, 0.0), (1, ouv, inf)):
            bx = (x0 - k, x1 + k, y0 - k, y1 + k, z0 - k, z1 + k)
            for f, (l, t, fw, fh) in face_rects(*uv, w, h, d).items():
                tl, tr, bl = [cam(p) for p in corners(f, *bx)]
                # 法線がカメラ(+z)を向く面だけ描く
                ax = [tr[i] - tl[i] for i in range(3)]
                ay = [bl[i] - tl[i] for i in range(3)]
                nz = ax[0] * ay[1] - ax[1] * ay[0]
                if nz >= 0:
                    continue
                depth = (tl[2] + tr[2] + bl[2]) / 3 + layer * 0.01
                faces.append((depth, skin.crop((l, t, l + fw, t + fh)), tl, tr, bl))
    faces.sort(key=lambda f: f[0])                     # 奥から順に
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    for _d, tex, tl, tr, bl in faces:
        P0, P1, P2 = to2d(tl), to2d(tr), to2d(bl)
        tw, th = tex.size
        # 出力(X,Y) → テクスチャ(u,v) の逆アフィン
        a11, a12 = (P1[0] - P0[0]) / tw, (P2[0] - P0[0]) / th
        a21, a22 = (P1[1] - P0[1]) / tw, (P2[1] - P0[1]) / th
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-9:
            continue
        i11, i12, i21, i22 = a22 / det, -a12 / det, -a21 / det, a11 / det
        c1 = -(i11 * P0[0] + i12 * P0[1])
        c2 = -(i21 * P0[0] + i22 * P0[1])
        layer_img = tex.transform(size, Image.AFFINE, (i11, i12, c1, i21, i22, c2),
                                  resample=Image.NEAREST, fillcolor=(0, 0, 0, 0))
        out.alpha_composite(layer_img)
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    skin = Image.open(src).convert("RGBA")
    size = (int(26 * S), int(40 * S))
    views = [render(skin, yaw, 25, size) for yaw in (-35, 35, 145, 215)]
    sheet = Image.new("RGBA", (size[0] * 4 + 40, size[1] + 20), (28, 30, 36, 255))
    for i, v in enumerate(views):
        sheet.alpha_composite(v, (10 + i * (size[0] + 6), 10))
    sheet.convert("RGB").save(dst)
    print(f"[DONE] {dst} {sheet.size}")


if __name__ == "__main__":
    main()
