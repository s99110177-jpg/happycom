"""영상 3 (스타일 C): 8비트 픽셀 게임 — 해피 갈매기가 걸어와 점프, 보물상자가 열리고 RPG 대화창으로 인사.

저해상도(270x480) 캔버스에 그린 뒤 4배 최근접 확대해서 픽셀 느낌을 낸다. 사운드는 칩튠(사각파).
"""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from . import calendar_kr as cal
from .messages import character_message, weekday_tag
from .render_common import (FPS, H, NFRAMES, W, clamp, finish_audio, font, melody, progress, render_video)
from .scene_character import WEEK_STYLE

K = 4
LW, LH = W // K, H // K   # 270 x 480

PAL = {"k": (34, 32, 52), "w": (250, 250, 250), "g": (160, 170, 190), "e": (20, 20, 30), "p": (255, 150, 170),
       "y": (255, 200, 40), "o": (255, 140, 40), "r": (70, 150, 255)}

BODY = [
    "....kkkkkkkk....",
    "..kkwwwwwwwwkk..",
    ".kwwwwwwwwwwwwk.",
    ".kwwwekwwkewwwk.",
    "kwwwweewweewwwwk",
    "kwpwwwyyyywwwpwk",
    "kwwwwwoyyowwwwwk",
    "kwwwwwwoowwwwwwk",
    "kwwrrrrrrrrrrwwk",
    "kwwwwwrrwwwwwwwk",
    ".kwwwwwrwwwwwwk.",
    ".kwwwwwwwwwwwwk.",
    "..kwwwwwwwwwwk..",
    "...kkkkkkkkkk...",
]
FEET = [["....oo....oo....", "...ooo....ooo..."],
        [".....oo..oo.....", "....ooo..ooo...."],
        ["...oo......oo...", "..ooo......ooo.."]]
BLINK_ROWS = {3: ".kwwwwwwwwwwwwk.", 4: "kwwwkkkwwkkkwwwk"}


def _sprite(feet=0, wings="down", blink=False, scarf=(70, 150, 255)):
    rows = [list(r) for r in BODY] + [list(r) for r in FEET[feet]]
    if blink:
        for i, r in BLINK_ROWS.items():
            rows[i] = list(r)
    img = Image.new("RGBA", (20, 18), (0, 0, 0, 0))
    px = img.load()
    pal = dict(PAL, r=scarf)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != ".":
                px[x + 2, y + 2] = pal[c] + (255,)
    gray, ink = PAL["g"] + (255,), PAL["k"] + (255,)
    if wings == "down":
        for y in range(8, 12):
            px[1, y] = ink
            px[2, y] = gray
            px[17, y] = gray
            px[18, y] = ink
    else:  # 만세
        for (x, y) in ((1, 2), (1, 3), (1, 4), (0, 1), (18, 2), (18, 3), (18, 4), (19, 1)):
            px[x, y] = gray
        for (x, y) in ((0, 2), (0, 3), (0, 4), (19, 2), (19, 3), (19, 4)):
            px[x, y] = ink
    return img


def _chest(open_=False):
    img = Image.new("RGBA", (18, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    brown, dark, gold = (170, 100, 50, 255), (90, 50, 30, 255), (255, 200, 40, 255)
    d.rectangle((1, 7, 16, 15), fill=brown, outline=dark)
    d.line((1, 11, 16, 11), fill=dark)
    if open_:
        d.rectangle((1, 1, 16, 4), fill=brown, outline=dark)
        d.rectangle((3, 5, 14, 7), fill=(255, 240, 150, 255))
    else:
        d.rectangle((1, 3, 16, 7), fill=brown, outline=dark)
        d.rectangle((8, 6, 9, 9), fill=gold)
    return img


def _heart(col=(255, 70, 90)):
    pat = [".kk.kk.", "krrkrrk", "krrrrrk", ".krrrk.", "..krk..", "...k..."]
    img = Image.new("RGBA", (7, 6), (0, 0, 0, 0))
    px = img.load()
    for y, r in enumerate(pat):
        for x, c in enumerate(r):
            if c == "k":
                px[x, y] = PAL["k"] + (255,)
            elif c == "r":
                px[x, y] = col + (255,)
    return img


def _star(col=(255, 230, 60)):
    pat = ["..k..", ".kyk.", "kyyyk", ".kyk.", "..k.."]
    img = Image.new("RGBA", (5, 5), (0, 0, 0, 0))
    px = img.load()
    for y, r in enumerate(pat):
        for x, c in enumerate(r):
            if c != ".":
                px[x, y] = (PAL["k"] if c == "k" else col) + (255,)
    return img


def _text(d: ImageDraw.ImageDraw, xy, s, size, fill, anchor="la", shadow=True):
    d.fontmode = "1"   # 안티앨리어싱 끄기 -> 픽셀 글자
    f = font("bold", size)
    if shadow:
        d.text((xy[0] + 1, xy[1] + 1), s, font=f, fill=PAL["k"] + (255,), anchor=anchor)
    d.text(xy, s, font=f, fill=fill + (255,), anchor=anchor)


def _background(d_: dt.date):
    top, bottom, _ = WEEK_STYLE[d_.weekday()]
    img = Image.new("RGBA", (LW, LH), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    # 디더링 하늘 (밴드)
    sky = [(92, 148, 252), (120, 170, 255), (160, 196, 255), (200, 220, 255), (255, 214, 200)]
    band_h = 300 // len(sky)
    for i, c in enumerate(sky):
        y0 = i * band_h
        d.rectangle((0, y0, LW, y0 + band_h), fill=c + (255,))
        if i + 1 < len(sky):  # 체커 디더
            for y in range(y0 + band_h - 4, y0 + band_h):
                for x in range((y % 2), LW, 2):
                    d.point((x, y), fill=sky[i + 1] + (255,))
    # 해
    d.ellipse((190, 150, 230, 190), fill=(255, 220, 90, 255))
    # 광안대교 픽셀
    d.rectangle((0, 300, LW, 360), fill=(60, 120, 200, 255))
    for x in range(0, LW, 6):
        d.point((x + (x // 6 % 2) * 3, 310 + (x * 7) % 40), fill=(170, 210, 255, 255))
    deck = 292
    d.rectangle((0, deck, LW, deck + 2), fill=(70, 60, 110, 255))
    for tx in (70, 200):
        d.rectangle((tx - 2, deck - 46, tx + 2, deck + 12), fill=(70, 60, 110, 255))
    for i in range(0, 131):
        x = 70 + i
        y = deck - 44 + int(40 * 4 * (i / 130) * (1 - i / 130))
        d.point((x, y), fill=(70, 60, 110, 255))
        if i % 6 == 0:
            d.line((x, y, x, deck), fill=(120, 110, 160, 255))
    for x in range(0, 70):
        d.point((x, deck - 2 - int(42 * (x / 70) ** 1.6)), fill=(70, 60, 110, 255))
    for x in range(200, LW):
        d.point((x, deck - 44 + int(42 * ((x - 200) / 70) ** 1.6)), fill=(70, 60, 110, 255))
    # 모래 + 블록 바닥
    d.rectangle((0, 360, LW, LH), fill=(240, 200, 130, 255))
    for x in range(0, LW, 12):
        d.rectangle((x, 360, x + 11, 371), fill=(220, 140, 70, 255), outline=(150, 80, 40, 255))
        d.line((x + 1, 361, x + 10, 361), fill=(255, 190, 120, 255))
    return img


def _cloud():
    pat = ["...kkkk.....", "..kwwwwk.kk.", ".kwwwwwwkwwk", "kwwwwwwwwwwk", ".kkkkkkkkkk."]
    img = Image.new("RGBA", (12, 5), (0, 0, 0, 0))
    px = img.load()
    for y, r in enumerate(pat):
        for x, c in enumerate(r):
            if c != ".":
                px[x, y] = (PAL[c] if c == "k" else (255, 255, 255)) + (255,)
    return img.resize((36, 15), Image.NEAREST)


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    _, _, accent = WEEK_STYLE[d.weekday()]
    bg = _background(d)
    cloud = _cloud()
    sprites = {}

    def spr(feet, wings, blink):
        key = (feet, wings, blink)
        if key not in sprites:
            sprites[key] = _sprite(feet, wings, blink, accent).resize((60, 54), Image.NEAREST)
        return sprites[key]

    chest_c = _chest(False).resize((36, 32), Image.NEAREST)
    chest_o = _chest(True).resize((36, 32), Image.NEAREST)
    heart = _heart().resize((14, 12), Image.NEAREST)
    star = _star().resize((10, 10), Image.NEAREST)
    msg = character_message(d).split("\n")
    quest = weekday_tag(d)
    rng = random.Random(d.toordinal())
    GROUND = 360
    CHEST_X = 192

    def frame(t, i):
        img = bg.copy()
        dr = ImageDraw.Draw(img)
        for k, (x0, y, v) in enumerate(((20, 150, 6), (150, 200, 4), (240, 245, 8))):
            x = int((x0 + v * t) % (LW + 40)) - 40
            img.alpha_composite(cloud, (x, y))
        # HUD
        _text(dr, (8, 8), "1P HAPPY", 12, (255, 255, 255))
        for k in range(3):
            img.alpha_composite(heart, (LW - 52 + k * 15, 8))
        _text(dr, (LW // 2, 30), f"STAGE {d.month}-{d.day}", 14, (255, 230, 90), anchor="ma")
        # 큰 날짜
        _text(dr, (LW // 2, 56), f"{d.year}", 12, (255, 255, 255), anchor="ma")
        _text(dr, (LW // 2, 72), f"{d.month}월 {d.day}일 {cal.WEEKDAYS[d.weekday()]}", 22, (255, 255, 255), anchor="ma")
        # 퀘스트 배너
        if t > 0.5:
            qy = 108
            qb = int(min(1, (t - 0.5) / 0.3) * 200)
            dr.rectangle((LW // 2 - qb // 2, qy, LW // 2 + qb // 2, qy + 22), fill=PAL["k"] + (255,))
            dr.rectangle((LW // 2 - qb // 2 + 2, qy + 2, LW // 2 + qb // 2 - 2, qy + 20), outline=accent + (255,))
            if t > 0.8:
                _text(dr, (LW // 2, qy + 4), f"QUEST: {quest}", 12, (255, 255, 255), anchor="ma", shadow=False)

        # 갈매기: 걷기 -> 점프 -> 상자 열기 -> 기뻐 깡총
        if t < 1.6:
            x = -40 + (100 + 40) * (t / 1.6)
            y = GROUND - 54
            feet = 1 + int(t / 0.12) % 2
            wings = "down"
        elif t < 2.1:
            u = (t - 1.6) / 0.5
            x = 100 + 16 * u
            y = GROUND - 54 - int(60 * math.sin(math.pi * u))
            feet, wings = 0, "up"
        else:
            u = ((t - 2.1) % 0.5) / 0.5
            hop = int(14 * math.sin(math.pi * u)) if t > 2.6 else 0
            x, y = 116, GROUND - 54 - hop
            feet, wings = 0, ("up" if hop > 6 else "down")
        blink = abs(t - 4.6) < 0.1
        img.alpha_composite(spr(feet, wings, blink), (int(x), int(y)))
        # 보물상자
        opened = t >= 1.85
        img.alpha_composite(chest_o if opened else chest_c, (CHEST_X, GROUND - 32))
        if opened:
            tt = t - 1.85
            for k in range(6):  # 별 튀어오르기
                ang = -math.pi / 2 + (k - 2.5) * 0.35
                r = 70 * min(1, tt / 0.6)
                sx = CHEST_X + 13 + int(r * math.cos(ang))
                sy = GROUND - 40 + int(r * math.sin(ang) + 60 * max(0, tt - 0.6) ** 2)
                if tt < 1.6 and (int(tt * 20) + k) % 3:
                    img.alpha_composite(star, (sx, sy))
            if tt < 1.4:
                _text(dr, (CHEST_X + 18, GROUND - 60 - int(30 * tt)), "+1 행복", 14, (255, 230, 90), anchor="ma")
        # RPG 대화창
        if t > 2.2:
            u = min(1, (t - 2.2) / 0.25)
            bh = 100
            by = LH - 4 - int(bh * u)
            dr.rectangle((8, by, LW - 8, by + bh), fill=(16, 16, 40, 255))
            dr.rectangle((10, by + 2, LW - 10, by + bh - 2), outline=(255, 255, 255, 255), width=2)
            dr.rectangle((14, by + 6, LW - 14, by + bh - 6), outline=(120, 120, 170, 255))
            if u >= 1:
                _text(dr, (22, by + 12), "해피 갈매기", 13, accent, shadow=False)
                total = sum(len(m) for m in msg)
                shown = int((t - 2.5) / 1.3 * total)
                yy = by + 32
                for line in msg:
                    part = line[: max(0, shown)]
                    if part:
                        _text(dr, (22, yy), part, 18, (255, 255, 255), shadow=False)
                    shown -= len(line)
                    yy += 26
                if shown > 4 and int(t * 3) % 2:  # 다음 ▼
                    dr.polygon([(LW - 34, by + bh - 22), (LW - 22, by + bh - 22), (LW - 28, by + bh - 15)],
                               fill=(255, 255, 255, 255))
        if brand:
            _text(dr, (LW // 2, 132), brand, 12, (255, 255, 255), anchor="ma")
        big = img.resize((W, H), Image.NEAREST)
        # 스캔라인 (살짝)
        arr = np.asarray(big, dtype=np.uint8).copy()
        arr[3::K, :, :3] = (arr[3::K, :, :3] * 0.88).astype(np.uint8)
        big = Image.fromarray(arr, "RGBA")
        fo = progress(t, NFRAMES / FPS - 0.3, 0.3)
        if fo > 0:
            big = Image.blend(big, Image.new("RGBA", (W, H), (0, 0, 0, 255)), fo * 0.7)
        return big

    snd = None
    if audio:
        sq = ((1, 1.0), (3, 0.33), (5, 0.2), (7, 0.14))  # 사각파 근사
        notes = []
        for k in range(13):  # 걷기 베이스
            notes.append((k * 0.12, 48 + (k % 2) * 7, 0.1, 0.35))
        notes += [(1.6, 72, 0.1, 0.5), (1.65, 76, 0.1, 0.5), (1.7, 79, 0.1, 0.5), (1.75, 84, 0.12, 0.5)]  # 점프
        notes += [(1.85, 83, 0.08, 0.6), (1.93, 88, 0.4, 0.6)]  # 코인
        melody_line = [72, 76, 79, 76, 77, 81, 84, 81, 79, 77, 76, 74, 72]
        for k, n in enumerate(melody_line):
            notes.append((2.3 + k * 0.2, n, 0.18, 0.4))
        notes += [(2.3 + k * 0.4, 48 + (0, 5, 7, 5, 0, 7, 0)[k], 0.35, 0.3) for k in range(7)]
        snd = finish_audio(melody(notes, decay=6.0, harmonics=sq), vol=0.45)
    render_video(out, frame, snd)
    return {"message": "\n".join(msg), "quest": quest}
