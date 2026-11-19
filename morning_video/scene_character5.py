"""영상 3 (스타일 D): 다이어리 스크랩북 — 모눈 노트에 폴라로이드 속 해피 갈매기, 마스킹테이프와 스티커, 손글씨 한마디."""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import calendar_kr as cal
from .handmade import paper, sticker, wipe
from .messages import character_message, weekday_tag
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_out_back, ease_out_cubic, emoji_image, finish_audio, font,
                            melody, paste, progress, render_video, text_layer, vertical_gradient)
from .scene_character import CH, CW, WEEK_STYLE, draw_gull

PEN = (40, 46, 70)
TAPES = [(255, 190, 200), (170, 220, 210), (255, 220, 140), (190, 200, 255)]


def _notebook(seed):
    img = paper((252, 250, 243), seed, strength=6)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 36):
        d.line((x, 0, x, H), fill=(190, 210, 235, 255), width=1)
    for y in range(0, H, 36):
        d.line((0, y, W, y), fill=(190, 210, 235, 255), width=1)
    d.line((110, 0, 110, H), fill=(240, 150, 150, 255), width=3)     # 여백 선
    for y in range(80, H, 110):                                        # 스프링 구멍
        d.ellipse((30, y, 66, y + 36), fill=(70, 70, 80, 255))
        d.arc((10, y - 12, 80, y + 40), 200, 340, fill=(160, 160, 170, 255), width=7)
    return img


def _tape(w, h, color, seed):
    rng = np.random.default_rng(seed)
    img = Image.new("RGBA", (w, h), color + (190,))
    d = ImageDraw.Draw(img)
    for x in range(0, w, 18):                                           # 줄무늬
        d.line((x, 0, x + 10, h), fill=(255, 255, 255, 70), width=6)
    a = np.full((h, w), 190, dtype=np.uint8)                            # 찢은 끝
    for y in range(h):
        a[y, : int(rng.integers(0, 6))] = 0
        a[y, w - int(rng.integers(0, 6)):] = 0
    img.putalpha(Image.fromarray(a))
    return img


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    seed = d.toordinal()
    rng = random.Random(seed)
    top, bottom, accent = WEEK_STYLE[d.weekday()]
    book = _notebook(seed)

    # 날짜 라벨 (테이프로 붙인 종이)
    t_date = text_layer(f"{d.year}. {d.month}. {d.day}. ({cal.WEEKDAYS_SHORT[d.weekday()]})", font("pen", 96), PEN)
    label = Image.new("RGBA", (t_date.width + 80, t_date.height + 50), (255, 255, 255, 255))
    label.alpha_composite(t_date, (40, 22))
    label = label.rotate(2, Image.BICUBIC, expand=True)
    tape1 = _tape(200, 54, TAPES[0], seed).rotate(-8, Image.BICUBIC, expand=True)
    t_tag = text_layer(weekday_tag(d), font("pen", 74), PEN)
    hl = Image.new("RGBA", (t_tag.width + 30, 40), (0, 0, 0, 0))
    ImageDraw.Draw(hl).rounded_rectangle((0, 0, t_tag.width + 29, 39), 16, fill=(255, 236, 110, 170))

    # 폴라로이드
    PW, PH, PI = 640, 760, 580
    photo_bg = vertical_gradient(PI, PI, [(0, top), (0.68, bottom), (0.7, (120, 196, 230)), (1, (90, 170, 220))]).convert("RGBA")
    sd = ImageDraw.Draw(photo_bg)
    sd.ellipse((420, 70, 520, 170), fill=(255, 216, 100, 255))
    cap = text_layer("해피 갈매기, 오늘도 출근!", font("pen", 54), PEN)
    tapes_p = [_tape(170, 50, TAPES[1], seed + 1).rotate(30, Image.BICUBIC, expand=True),
               _tape(170, 50, TAPES[2], seed + 2).rotate(-28, Image.BICUBIC, expand=True)]
    gull_cache = {}

    def gull(wing, blink):
        key = (round(wing / 4) * 4, blink)
        if key not in gull_cache:
            g = draw_gull(key[0], key[1], 0.2, accent)
            gull_cache[key] = g.resize((int(CW * 0.6), int(CH * 0.6)), Image.LANCZOS)
        return gull_cache[key]

    def polaroid(t):
        p = Image.new("RGBA", (PW, PH), (255, 255, 255, 255))
        ph = photo_bg.copy()
        g = gull(35 + 30 * math.sin(t * 7), 1 if abs(t - 3.9) < 0.08 else 0)
        ph.alpha_composite(g, (int(PI / 2 - g.width / 2), int(PI - g.height + 20 + 6 * math.sin(t * 3))))
        p.paste(ph, (30, 30))
        p.alpha_composite(cap, ((PW - cap.width) // 2, PI + 60))
        shadow = Image.new("RGBA", (PW + 60, PH + 60), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rectangle((30, 40, PW + 30, PH + 40), fill=(0, 0, 0, 70))
        shadow = shadow.filter(ImageFilter.GaussianBlur(12))
        shadow.alpha_composite(p, (30, 30))
        return shadow.rotate(-4, Image.BICUBIC, expand=True)

    # 스티커
    icons = ["☀️", "🌊", "💛", "✨", "🍀", "☕"]
    rng.shuffle(icons)
    spots = [(170, 760), (930, 700), (900, 1310), (190, 1290), (960, 1010), (520, 470)]
    stickers = [(sticker(emoji_image(e, 110), 9), x, y, rng.uniform(-15, 15)) for e, (x, y) in zip(icons, spots)]

    msg = character_message(d)
    t_head = text_layer("오늘의 한마디", font("pen", 60), (220, 90, 110))
    t_msg = text_layer(msg, font("pen", 92), PEN, line_gap=0.15)
    hl2 = Image.new("RGBA", (t_msg.width + 40, t_msg.height + 10), (0, 0, 0, 0))
    ImageDraw.Draw(hl2).rounded_rectangle((0, t_msg.height * 0.8, t_msg.width + 39, t_msg.height * 0.98), 14,
                                          fill=accent + (90,))
    t_brand = text_layer(brand, font("pen", 58), PEN) if brand else None
    pol_y = 1020

    def frame(t, i):
        img = book.copy()
        # 날짜 라벨 + 테이프
        a = ease_out_cubic(progress(t, 0.0, 0.5))
        paste(img, label, (W / 2 + 30, 200 - 40 * (1 - a)), a)
        paste(img, tape1, (W / 2 + 30 - label.width / 2 + 30, 160 - 40 * (1 - a)), a)
        hp = progress(t, 0.5, 0.4)
        if hp > 0:
            img.alpha_composite(hl.crop((0, 0, max(1, int(hl.width * hp)), hl.height)),
                                (int(W / 2 + 30 - t_tag.width / 2 - 15), 330))
        paste(img, t_tag, (W / 2 + 30, 345), ease_out_cubic(progress(t, 0.5, 0.4)))
        # 폴라로이드 툭 놓이기
        pp = progress(t, 0.5, 0.6)
        if pp > 0:
            pol = polaroid(t)
            sc = 1.25 - 0.25 * ease_out_cubic(pp)
            pol2 = pol.resize((int(pol.width * sc), int(pol.height * sc)), Image.BILINEAR)
            paste(img, pol2, (W / 2 + 30, pol_y), clamp(pp * 2))
            if pp >= 1:
                paste(img, tapes_p[0], (W / 2 + 30 - 300, pol_y - 360), 1)
                paste(img, tapes_p[1], (W / 2 + 30 + 300, pol_y - 380), 1)
        # 스티커 하나씩 '뽁'
        for k, (s, x, y, ang) in enumerate(stickers):
            sp = progress(t, 1.2 + k * 0.22, 0.35)
            if sp > 0:
                sc = clamp(ease_out_back(sp), 0.01, 2)
                s2 = s.resize((max(1, int(s.width * sc)), max(1, int(s.height * sc))), Image.BILINEAR).rotate(ang, Image.BICUBIC, expand=True)
                paste(img, s2, (x, y))
        # 오늘의 한마디 (손글씨로 써짐 + 형광펜)
        paste(img, t_head, (W / 2 + 30, 1510), ease_out_cubic(progress(t, 2.4, 0.4)))
        mp = progress(t, 2.6, 1.3)
        if mp > 0:
            mx, my = int(W / 2 + 30 - t_msg.width / 2), 1580
            if mp >= 1:
                hp2 = progress(t, 3.9, 0.4)
                img.alpha_composite(hl2.crop((0, 0, max(1, int(hl2.width * hp2)), hl2.height)), (mx - 20, my))
            img.alpha_composite(wipe(t_msg, mp), (mx, my))
        if t_brand:
            paste(img, t_brand, (W - 200, H - 60), ease_out_cubic(progress(t, 3.0, 0.5)))
        fo = progress(t, NFRAMES / FPS - 0.3, 0.3)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (252, 250, 243, 255)), fo * 0.5)
        return img

    snd = None
    if audio:
        pops = [(1.2 + k * 0.22, 84 + (k % 3) * 3, 0.15, 0.5) for k in range(6)]
        notes = [(0.5, 60, 0.3, 0.6), (0.6, 67, 0.3, 0.4)] + pops + \
                [(2.6, 72, 0.4, 0.4), (2.9, 76, 0.4, 0.4), (3.2, 79, 0.4, 0.4), (3.5, 77, 0.4, 0.4),
                 (3.9, 76, 1.2, 0.45), (3.9, 72, 1.2, 0.35)]
        snd = finish_audio(melody(notes, decay=4.0, harmonics=((1, 1.0), (2, 0.3), (4, 0.1))), vol=0.5)
    render_video(out, frame, snd)
    return {"message": msg, "tag": weekday_tag(d)}
