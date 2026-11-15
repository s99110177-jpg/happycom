"""영상 3 (스타일 B): 종이 공예(페이퍼컷) 일러스트 — 해피 갈매기가 인사 현수막을 끌고 부산 하늘을 난다."""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import calendar_kr as cal
from .messages import character_message, weekday_tag
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_in_out, ease_out_back, ease_out_cubic, finish_audio,
                            font, lerp, melody, paste, progress, render_video, text_layer, vertical_gradient)
from .scene_character import CH, CW, INK, WEEK_STYLE, draw_gull

S = 2


def _paper(shape_fn, size, color, shadow=(0, 0, 0, 70), off=(0, 10), blur=10):
    """shape_fn(draw, scale) 로 그린 도형을 종이처럼(그림자 + 미세한 결) 만든다."""
    w, h = size
    m = Image.new("L", (w * S, h * S), 0)
    shape_fn(ImageDraw.Draw(m), S)
    m = m.resize((w, h), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), shadow[:3] + (0,))
    sh.putalpha(m.point(lambda v: v * shadow[3] // 255))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(sh, off)
    rng = np.random.default_rng(len(color) + w)
    grain = (rng.random((h, w)) * 14 - 7).astype(np.int16)
    base = np.zeros((h, w, 4), dtype=np.int16)
    base[..., :3] = np.array(color, dtype=np.int16) + grain[..., None]
    base[..., 3] = np.array(m)
    top = Image.fromarray(base.clip(0, 255).astype(np.uint8), "RGBA")
    out.alpha_composite(top)
    return out


def _ridge(points_fn, color, y0, amp_seed):
    def fn(d, s):
        pts = [(x * s, y * s) for x, y in points_fn()] + [(W * s, H * s), (0, H * s)]
        d.polygon(pts, fill=255)
    return _paper(fn, (W, H), color, off=(0, -8), blur=12)


def _layers(rng, palette):
    sea_c, hill_c, city_c, near_c = palette
    # 먼 산
    hills = _ridge(lambda: [(x, 1290 - 90 * math.sin(x / 420 + 0.5) - 30 * math.sin(x / 130)) for x in range(-20, W + 40, 20)],
                   hill_c, 0, 1)

    # 도시 실루엣 + 부산타워 + 광안대교
    def city(d, s):
        x = -10
        while x < W + 20:
            bw, bh = rng.randint(40, 80), rng.randint(60, 200)
            d.rounded_rectangle((x * s, (1420 - bh) * s, (x + bw) * s, 1500 * s), 10 * s, fill=255)
            x += bw + rng.randint(6, 20)
        # 부산타워 (왼쪽 언덕 위)
        tx = 230
        d.polygon([((tx - 14) * s, 1300 * s), ((tx - 8) * s, 1040 * s), ((tx + 8) * s, 1040 * s), ((tx + 14) * s, 1300 * s)], fill=255)
        d.ellipse(((tx - 34) * s, 1010 * s, (tx + 34) * s, 1060 * s), fill=255)
        d.rectangle(((tx - 3) * s, 950 * s, (tx + 3) * s, 1012 * s), fill=255)
        d.ellipse(((tx - 110) * s, 1270 * s, (tx + 110) * s, 1420 * s), fill=255)
    city_l = _paper(city, (W, H), city_c, off=(0, -6), blur=10)

    def bridge(d, s):
        y = 1500
        d.rectangle((0, (y - 8) * s, W * s, (y + 6) * s), fill=255)
        for tx in (360, 760):
            d.rectangle(((tx - 12) * s, (y - 210) * s, (tx + 12) * s, (y + 60) * s), fill=255)
        pts = []
        for i in range(0, 101):
            xx = lerp(360, 760, i / 100)
            pts.append((xx * s, (y - 205 + 180 * 4 * (i / 100) * (1 - i / 100)) * s))
        d.line(pts, fill=255, width=7 * s)
        d.line([(0, (y - 20) * s), (360 * s, (y - 205) * s)], fill=255, width=7 * s)
        d.line([(760 * s, (y - 205) * s), (W * s, (y - 20) * s)], fill=255, width=7 * s)
        for xx, yy in pts[5:-5:6]:
            d.line((xx, yy, xx, (y - 6) * s), fill=255, width=2 * s)
    bridge_l = _paper(bridge, (W, H), tuple(int(c * 0.8) for c in city_c), off=(0, 6), blur=6)

    sea = _ridge(lambda: [(x, 1510) for x in range(-20, W + 40, 40)], sea_c, 0, 2)
    near = _ridge(lambda: [(x, 1720 - 50 * math.sin(x / 260 + 2.0) - 14 * math.sin(x / 70)) for x in range(-20, W + 40, 20)],
                  near_c, 0, 3)
    return hills, city_l, bridge_l, sea, near


def _cloud_paper(w, rng):
    h = int(w * 0.5)

    def fn(d, s):
        for _ in range(5):
            r = rng.uniform(0.15, 0.24) * w
            cx = rng.uniform(r, w - r)
            cy = h - r - 8
            d.ellipse(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), fill=255)
        d.rounded_rectangle((0.1 * w * s, (h - 0.2 * w - 8) * s, 0.9 * w * s, (h - 8) * s), int(0.1 * w * s), fill=255)
    return _paper(fn, (w, h + 20), (255, 255, 255), shadow=(60, 60, 100, 60), off=(6, 10), blur=8)


def _banner(text_lines, color):
    f = font("round", 50)
    lines = [text_layer(l, f, INK) for l in text_lines]
    bw = max(l.width for l in lines) + 110
    bh = sum(l.height for l in lines) + 16 * (len(lines) - 1) + 70

    def fn(d, s):
        d.polygon([(0, 0), (bw * s, 0), (bw * s, bh * s), (0, bh * s), (40 * s, bh / 2 * s)], fill=255)
    base = _paper(fn, (bw, bh + 30), (255, 252, 240), shadow=(0, 0, 0, 60), off=(0, 12), blur=8)
    d = ImageDraw.Draw(base)
    d.rectangle((bw - 18, 0, bw, bh), fill=color + (255,))
    y = 35
    for l in lines:
        base.alpha_composite(l, (int((bw - 40 - l.width) / 2) + 30, y))
        y += l.height + 16
    return base


def _wave(img: Image.Image, t, amp=16, wl=260.0, speed=5.0):
    """현수막 펄럭임: 열마다 세로로 사인 변위 (왼쪽 끝일수록 크게)."""
    a = np.array(img)
    h, w = a.shape[:2]
    pad = int(amp) + 2
    out = np.zeros((h + pad * 2, w, 4), dtype=np.uint8)
    for x in range(0, w, 2):
        k = 1 - x / w
        dy = int(pad + amp * (0.3 + 0.7 * k) * math.sin(x / wl * 2 * math.pi - t * speed))
        out[dy:dy + h, x:x + 2] = a[:, x:x + 2]
    return Image.fromarray(out, "RGBA")


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    rng = random.Random(d.toordinal() * 17 + 3)
    top, bottom, accent = WEEK_STYLE[d.weekday()]
    sky = vertical_gradient(W, H, [(0, top), (0.7, bottom), (1, bottom)]).convert("RGBA")
    palette = ((120, 190, 220), tuple(int(c * 0.86) for c in top), (178, 168, 210), (250, 214, 160))
    hills, city, bridge, sea, near = _layers(rng, palette)
    sun = _paper(lambda dr, s: dr.ellipse((10 * s, 10 * s, 250 * s, 250 * s), fill=255), (270, 280), (255, 200, 90),
                 shadow=(200, 120, 40, 90), off=(0, 10), blur=10)
    clouds = [(_cloud_paper(rng.randint(240, 340), rng), rng.uniform(0, W), y, rng.uniform(10, 24))
              for y in (640, 780, 1080)]

    msg = character_message(d)
    banner = _banner(msg.split("\n"), accent)
    gull_cache = {}

    def gull(wing, mouth):
        key = (round(wing / 4) * 4, round(mouth, 1))
        if key not in gull_cache:
            g = draw_gull(key[0], 0, key[1], accent)
            gull_cache[key] = g.resize((int(CW * 0.48), int(CH * 0.48)), Image.LANCZOS)
        return gull_cache[key]

    # 날짜 종이 태그
    t_date = text_layer(f"{d.month}월 {d.day}일", font("round", 104), INK)
    t_wd = text_layer(f"{d.year} · {cal.WEEKDAYS[d.weekday()]}", font("round", 50), INK)
    tw = max(t_date.width, t_wd.width) + 120
    th = t_date.height + t_wd.height + 90
    tag = _paper(lambda dr, s: dr.rounded_rectangle((0, 0, tw * s - 1, th * s - 1), 40 * s, fill=255),
                 (tw, th + 24), (255, 252, 244), off=(0, 12), blur=10)
    tag.alpha_composite(t_date, ((tw - t_date.width) // 2, 34))
    tag.alpha_composite(t_wd, ((tw - t_wd.width) // 2, 34 + t_date.height + 18))
    t_tag = text_layer(weekday_tag(d), font("round", 46), (255, 255, 255))
    rib = _paper(lambda dr, s: dr.rounded_rectangle((0, 0, (t_tag.width + 80) * s - 1, 84 * s - 1), 42 * s, fill=255),
                 (t_tag.width + 80, 100), accent, off=(0, 8), blur=6)
    rib.alpha_composite(t_tag, (40, (84 - t_tag.height) // 2 - 2))
    t_brand = text_layer(brand, font("round", 40), INK) if brand else None
    t_name = text_layer("해피 갈매기의 아침 인사", font("round", 36), (110, 80, 50))

    def frame(t, i):
        img = sky.copy()
        paste(img, sun, (870, 560 - 8 * t))
        for c, x0, y, v in clouds:
            paste(img, c, ((x0 + v * t) % (W + 400) - 200, y + 5 * math.sin(t + x0)))
        sway = 6 * math.sin(t * 0.8)
        img.alpha_composite(hills, (int(-sway * 0.3), 0))
        img.alpha_composite(city, (int(-sway * 0.6), 0))
        img.alpha_composite(sea)
        img.alpha_composite(bridge, (int(-sway), 0))
        # 바다 반짝임
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fx)
        for k in range(14):
            x = (k * 97 + t * 40) % W
            y = 1560 + (k * 37) % 120
            fd.line((x, y, x + 50, y), fill=(255, 255, 255, int(120 + 100 * math.sin(t * 3 + k))), width=4)
        img.alpha_composite(fx)
        img.alpha_composite(near, (int(sway), 0))

        # 날짜 태그 (위에서 내려와 흔들림)
        a = progress(t, 0.0, 0.7)
        ty = lerp(-300, 330, ease_out_back(a)) if a < 1 else 330
        tg = tag.rotate(3 * math.sin(t * 1.6) * (1 - 0.5 * clamp(t / 3)), Image.BICUBIC, expand=True)
        ImageDraw.Draw(img).line((W / 2, 0, W / 2, ty - th / 2 + 10), fill=(120, 100, 80, 255), width=4)
        paste(img, tg, (W / 2, ty))
        ar = clamp(ease_out_back(progress(t, 0.5, 0.5)))
        if ar > 0.01:
            r2 = rib.resize((max(1, int(rib.width * ar)), max(1, int(rib.height * ar))), Image.BILINEAR)
            paste(img, r2, (W / 2, ty + th / 2 + 60))

        # 갈매기가 왼쪽에서 날아오며 현수막을 끌고 온다
        pf = ease_out_cubic(progress(t, 0.3, 1.8))
        gx = lerp(-260, 880, pf)
        gy = 1000 + 26 * math.sin(t * 2.6)
        wing = 30 + 40 * math.sin(t * 11)
        mouth = 0.6 if 2.0 < t < 3.5 else 0.15
        g = gull(wing, mouth)
        bw = _wave(banner, t)
        bx = gx - g.width / 2 - 24 - bw.width
        by = gy - bw.height / 2 + 30
        img.alpha_composite(bw, (int(bx), int(by)))
        rope_from = (bx + bw.width - 14, gy + 20)
        rope_to = (gx - g.width * 0.3, gy + 10)
        ImageDraw.Draw(img).line((rope_from, ((rope_from[0] + rope_to[0]) / 2, gy + 40), rope_to),
                                 fill=(110, 90, 70, 255), width=4, joint="curve")
        paste(img, g, (gx, gy))

        a = ease_out_cubic(progress(t, 1.8, 0.6))
        paste(img, t_name, (W / 2, 1830 if not t_brand else 1800), a)
        if t_brand:
            paste(img, t_brand, (W / 2, 1866), a)
        fo = progress(t, NFRAMES / FPS - 0.3, 0.3)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), fo * 0.5)
        return img

    snd = None
    if audio:
        notes = [(0.3, 74, 0.35, 0.5), (0.5, 76, 0.35, 0.5), (0.7, 79, 0.6, 0.6), (1.3, 81, 0.35, 0.5),
                 (1.5, 79, 0.35, 0.5), (1.7, 76, 0.6, 0.55), (2.3, 74, 0.35, 0.5), (2.5, 76, 0.35, 0.5),
                 (2.7, 79, 0.35, 0.5), (2.9, 84, 1.0, 0.6), (3.7, 79, 1.4, 0.4), (3.7, 83, 1.4, 0.35)]
        snd = finish_audio(melody(notes, decay=4.0, harmonics=((1, 1.0), (2, 0.4), (3, 0.15))), vol=0.5)
    render_video(out, frame, snd)
    return {"message": msg, "tag": weekday_tag(d)}
