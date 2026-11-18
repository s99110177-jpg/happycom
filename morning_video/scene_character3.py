"""캐릭터 애니메이션: 만화풍 집중선 배경에서 해피 갈매기가 착지 → 날개 주먹 3번 "화이팅!" → 큰 제목과 인사.

특별한 날(messages.SPECIAL_DAYS)에 headband 가 있으면 머리띠를 두른다 (예: 수능 '합격').
"""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from . import calendar_kr as cal
from .messages import _special, character_message
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_out_back, ease_out_cubic, finish_audio, font, lerp,
                            melody, paste, progress, render_video, rounded_rect_layer, text_layer)
from .scene_character import CH, CW, INK, PAD, WEEK_STYLE, draw_gull

CHEERS = ["화이팅!", "할 수 있다!", "아자아자!"]


def _rays(c1, c2, n=24, r=1500):
    img = Image.new("RGBA", (r * 2, r * 2), c1 + (255,))
    d = ImageDraw.Draw(img)
    for k in range(n):
        a0 = 2 * math.pi * k / n
        a1 = a0 + math.pi / n
        d.polygon([(r, r), (r + r * 1.5 * math.cos(a0), r + r * 1.5 * math.sin(a0)),
                   (r + r * 1.5 * math.cos(a1), r + r * 1.5 * math.sin(a1))], fill=c2 + (255,))
    return img


def _halftone(color):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 28):
        for x in range(0, W, 28):
            # 가장자리로 갈수록 큰 점
            k = max(abs(x - W / 2) / (W / 2), abs(y - H / 2) / (H / 2))
            r = max(0, (k - 0.55) * 22)
            if r > 0.5:
                ox = 14 if (y // 28) % 2 else 0
                d.ellipse((x + ox - r, y - r, x + ox + r, y + r), fill=color + (90,))
    return img


def _burst(text, fill=(255, 226, 60)):
    t = text_layer(text, font("round", 74), INK)
    rw, rh = t.width + 150, t.height + 130
    img = Image.new("RGBA", (rw * 2, rh * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = []
    n = 18
    for k in range(n * 2):
        a = math.pi * k / n
        rr = 1.0 if k % 2 == 0 else 0.78
        pts.append((rw + rw * 0.98 * rr * math.cos(a), rh + rh * 0.98 * rr * math.sin(a)))
    d.polygon(pts, fill=fill + (255,), outline=INK + (255,), width=10)
    img = img.resize((rw, rh), Image.LANCZOS)
    img.alpha_composite(t, ((rw - t.width) // 2, (rh - t.height) // 2 - 4))
    return img


def _with_headband(g: Image.Image, text: str) -> Image.Image:
    s = 2
    g = g.resize((g.width * s, g.height * s), Image.LANCZOS)
    d = ImageDraw.Draw(g)
    cx = 320 + PAD
    top, bot = 232, 280
    pts_top = [((cx + x) * s, (top + 0.0006 * x * x) * s) for x in range(-172, 173, 8)]
    pts_bot = [((cx + x) * s, (bot + 0.0007 * x * x) * s) for x in range(198, -199, -8)]
    d.polygon(pts_top + pts_bot, fill=(222, 44, 56, 255), outline=INK + (255,))
    d.line(pts_top, fill=INK + (255,), width=5 * s)
    d.line(pts_bot, fill=INK + (255,), width=5 * s)
    # 매듭 끈
    kx, ky = cx + 190, 268
    for dx2, dy2 in ((70, -30), (64, 34)):
        d.polygon([(kx * s, (ky - 12) * s), ((kx + dx2) * s, (ky + dy2 - 10) * s), ((kx + dx2 + 6) * s, (ky + dy2 + 10) * s),
                   (kx * s, (ky + 12) * s)], fill=(222, 44, 56, 255), outline=INK + (255,), width=4 * s)
    t = text_layer(text, font("bold", 38 * s), (255, 255, 255))
    g.alpha_composite(t, (int(cx * s - t.width / 2), int((top + bot) / 2 * s - t.height / 2 + 2 * s)))
    return g.resize((g.width // s, g.height // s), Image.LANCZOS)


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    rng = random.Random(d.toordinal() * 31 + 7)
    top, bottom, accent = WEEK_STYLE[d.weekday()]
    rays = _rays(top, bottom)
    dots = _halftone(accent)
    headband = _special(d, "headband")

    msg = character_message(d)
    lines = msg.split("\n")
    title, bubble_txt = lines[0], " ".join(lines[1:]) if len(lines) > 1 else ""
    t_title = text_layer(title, font("round", 150), (255, 255, 255), stroke=14, stroke_fill=INK,
                         shadow=(10, 14, 0, accent + (255,)))
    t_date = text_layer(cal.korean_date(d), font("round", 50), (255, 255, 255))
    pill = rounded_rect_layer(t_date.width + 90, 96, 48, INK + (255,))
    pill.alpha_composite(t_date, ((pill.width - t_date.width) // 2, (96 - t_date.height) // 2 - 2))
    bubble = None
    if bubble_txt:
        bt = text_layer(bubble_txt, font("round", 58), INK)
        bw, bh = bt.width + 90, bt.height + 70
        bubble = Image.new("RGBA", (bw * 2, (bh + 50) * 2), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bubble)
        bd.rounded_rectangle((6, 6, bw * 2 - 6, bh * 2 - 6), 60, fill=(255, 255, 255, 255), outline=INK + (255,), width=12)
        tx = bw * 2 * 0.62
        bd.polygon([(tx - 50, bh * 2 - 14), (tx + 40, bh * 2 - 14), (tx + 70, bh * 2 + 90)], fill=(255, 255, 255, 255))
        bd.line([(tx - 50, bh * 2 - 8), (tx + 70, bh * 2 + 90), (tx + 40, bh * 2 - 8)], fill=INK + (255,), width=12)
        bubble = bubble.resize((bw, bh + 50), Image.LANCZOS)
        bubble.alpha_composite(bt, ((bw - bt.width) // 2, (bh - bt.height) // 2))
    cheers = ([headband + "!"] if headband else []) + CHEERS
    bursts = [_burst(c) for c in cheers[:3]]
    burst_pos = [(250, 900), (830, 820), (540, 700)]
    t_brand = text_layer(brand, font("round", 40), INK) if brand else None

    cache = {}

    def gull(wing, blink, mouth):
        key = (round(wing / 4) * 4, round(blink), round(mouth, 1))
        if key not in cache:
            g = draw_gull(key[0], key[1], key[2], accent)
            cache[key] = _with_headband(g, headband) if headband else g
        return cache[key]

    shadow = Image.new("RGBA", (440, 80), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse((0, 0, 439, 79), fill=(0, 0, 0, 60))
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    confetti = [[rng.uniform(0, W), rng.uniform(-300, -20), rng.uniform(250, 450), rng.uniform(-40, 40), rng.uniform(0, 6),
                 rng.uniform(3, 7), rng.choice([(255, 90, 90), (255, 210, 60), (90, 200, 255), (120, 220, 140), accent]),
                 rng.uniform(16, 26), rng.uniform(3.0, 3.8)] for _ in range(60)]
    PUMP0, PER = 0.85, 0.62
    base_y = 1650

    def frame(t, i):
        # 펌프 상태 (0~1~0)
        k = (t - PUMP0) / PER
        pump = math.sin(math.pi * (k - math.floor(k))) ** 2 if 0 <= k < 3 else 0.0
        n_pump = int(k) if 0 <= k < 3 else (3 if k >= 3 else -1)
        punch = 1 + 0.035 * pump
        # 배경: 회전 집중선 + 망점
        r = rays.rotate(t * 8, Image.BILINEAR)
        rs = int(r.width / punch)
        img = r.crop(((r.width - W / punch) / 2, (r.height - H / punch) / 2,
                      (r.width + W / punch) / 2, (r.height + H / punch) / 2)).resize((W, H), Image.BILINEAR)
        img.alpha_composite(dots)
        # 바닥
        fd = ImageDraw.Draw(img)
        fd.ellipse((-200, base_y - 40, W + 200, base_y + 520), fill=(255, 255, 255, 255), outline=INK + (255,), width=10)

        # 캐릭터: 착지 → 펌프 → 손 흔들기
        pdrop = progress(t, 0.0, 0.55)
        y_off = -1100 * (1 - ease_out_cubic(pdrop)) if pdrop < 1 else 0
        land = t - 0.55
        squash = 0.12 * math.exp(-land * 7) * math.cos(land * 24) if land > 0 else 0
        hop = -70 * pump
        if 0 <= k < 3:
            wing = lerp(-50, 85, pump)
            mouth = 0.3 + 0.7 * pump
        elif t < PUMP0:
            wing, mouth = -60, 0.0
        else:
            wing = 35 + 30 * math.sin((t - 3.0) * 7.5)
            mouth = 0.25
        blink = 1 if abs(t - 4.5) < 0.08 else 0
        g = gull(wing, blink, mouth)
        sx, sy = 1 + squash, 1 - squash
        if abs(squash) > 0.003:
            g = g.resize((int(g.width * sx), int(g.height * sy)), Image.BILINEAR)
        sh_k = clamp(1 - abs(y_off + hop) / 600, 0.3, 1)
        paste(img, shadow.resize((int(440 * sh_k), int(80 * sh_k))), (W / 2, base_y + 10))
        paste(img, g, (W / 2 - g.width / 2, base_y - g.height + y_off + hop + 20), anchor="lt")
        # 동작선
        if pump > 0.6:
            ld = ImageDraw.Draw(img)
            for j in range(3):
                x0 = W / 2 + 300 + j * 26
                ld.line((x0, base_y - 520 - j * 30, x0 + 30, base_y - 600 - j * 30), fill=INK + (255,), width=8)

        # "화이팅!" 버스트: 펌프마다 하나씩 터지고 남아 있음
        for j, (bimg, pos) in enumerate(zip(bursts, burst_pos)):
            tj = t - (PUMP0 + PER * (j + 0.5))
            if tj <= 0 or t > 3.0 + 0.4:
                continue
            sc = clamp(ease_out_back(clamp(tj / 0.25)), 0.01, 2) * (1 - clamp((t - 3.0) / 0.4))
            if sc <= 0.02:
                continue
            b2 = bimg.resize((max(1, int(bimg.width * sc)), max(1, int(bimg.height * sc))), Image.BILINEAR)
            b2 = b2.rotate((-8 if j % 2 else 8) + 3 * math.sin(t * 10), Image.BICUBIC, expand=True)
            paste(img, b2, pos)

        # 날짜 (처음부터)
        a = ease_out_back(progress(t, 0.1, 0.5))
        paste(img, pill, (W / 2, 170 - 120 * (1 - clamp(a))), clamp(a * 2))
        # 큰 제목 + 말풍선 (펌프 후)
        pt = progress(t, 2.95, 0.5)
        if pt > 0:
            sc = clamp(ease_out_back(pt), 0.01, 2)
            t2 = t_title.resize((max(1, int(t_title.width * sc)), max(1, int(t_title.height * sc))), Image.BILINEAR)
            paste(img, t2.rotate(-4, Image.BICUBIC, expand=True), (W / 2, 390), clamp(pt * 2))
        if bubble:
            pb = progress(t, 3.3, 0.45)
            if pb > 0:
                sc = clamp(ease_out_back(pb), 0.01, 2)
                b2 = bubble.resize((max(1, int(bubble.width * sc)), max(1, int(bubble.height * sc))), Image.BILINEAR)
                paste(img, b2, (W / 2 - 40, 720), clamp(pb * 2))
        # 축하 종이 조각
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(fx)
        for x0, y0, vy, vx, ph, spin, col, size, delay in confetti:
            tt = t - delay
            if tt <= 0:
                continue
            x, y = x0 + vx * tt + 25 * math.sin(tt * 3 + ph), y0 + vy * tt + 300 * tt * tt
            ang = ph + spin * tt
            w2, h2 = size * abs(math.cos(ang)), size * 0.5
            ca, sa = math.cos(ang * 0.6), math.sin(ang * 0.6)
            cd.polygon([(x + dx * ca - dy * sa, y + dx * sa + dy * ca) for dx, dy in
                        ((-w2 / 2, -h2 / 2), (w2 / 2, -h2 / 2), (w2 / 2, h2 / 2), (-w2 / 2, h2 / 2))], fill=col + (255,))
        img.alpha_composite(fx)
        if t_brand:
            paste(img, t_brand, (W / 2, 1860), ease_out_cubic(progress(t, 3.0, 0.5)))
        fo = progress(t, NFRAMES / FPS - 0.25, 0.25)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), fo * 0.5)
        return img

    snd = None
    if audio:
        import numpy as np
        from .render_common import SR, DURATION
        notes = [(0.55, 60, 0.3, 0.8)]  # 착지 '쿵'
        for j in range(3):  # 펌프마다 상승음
            st = PUMP0 + PER * (j + 0.5) - 0.05
            notes += [(st, 72 + j * 2, 0.25, 0.6), (st + 0.07, 76 + j * 2, 0.25, 0.6), (st + 0.14, 79 + j * 2, 0.35, 0.6)]
        notes += [(2.95, 84, 0.9, 0.7), (2.95, 88, 0.9, 0.5), (2.95, 91, 0.9, 0.4),
                  (3.6, 79, 0.3, 0.5), (3.8, 81, 0.3, 0.5), (4.0, 84, 1.3, 0.6), (4.0, 88, 1.3, 0.45)]
        sig = melody(notes, decay=4.5, harmonics=((1, 1.0), (2, 0.5), (3, 0.2)))
        n = int(DURATION * SR)
        thud = np.zeros(n)
        L = int(0.25 * SR)
        tt = np.arange(L) / SR
        i0 = int(0.55 * SR)
        thud[i0:i0 + L] = np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 18) * 1.5
        snd = finish_audio(sig + thud, vol=0.55)
    render_video(out, frame, snd)
    return {"message": msg, "headband": headband}
