"""영상 3: 일러스트/캐릭터 스타일 — 오리지널 캐릭터 '해피 갈매기'의 아침 인사."""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from . import calendar_kr as cal
from .messages import character_message, weekday_tag
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_out_back, ease_out_cubic, emoji_image, finish_audio,
                            font, lerp, melody, paste, progress, radial_glow, render_video, rounded_rect_layer,
                            text_layer, vertical_gradient)

S = 2
BW = 640                   # 몸통 캔버스 폭 (1x)
PAD = 120                  # 날개가 잘리지 않도록 좌우 여백
CW, CH = BW + PAD * 2, 720  # 캐릭터 캔버스 (1x)
INK = (48, 54, 90)

# 요일별 파스텔 배경 (top, bottom) 과 스카프 색
WEEK_STYLE = [
    ((255, 214, 224), (255, 240, 214), (90, 150, 255)),   # 월
    ((214, 236, 255), (236, 248, 255), (255, 120, 120)),  # 화
    ((220, 245, 222), (250, 255, 230), (255, 160, 60)),   # 수
    ((232, 222, 255), (255, 236, 246), (60, 190, 170)),   # 목
    ((255, 236, 200), (255, 250, 230), (240, 90, 140)),   # 금
    ((205, 240, 245), (240, 255, 250), (130, 110, 230)),  # 토
    ((255, 225, 205), (255, 245, 235), (70, 160, 230)),   # 일
]


def _e(d, cx, cy, rx, ry, **kw):
    d.ellipse(((cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S), **kw)


def _wing(length=190, width=78, tip=(120, 128, 150)):
    img = Image.new("RGBA", ((length + 20) * S, (width + 20) * S), (0, 0, 0, 0))
    sq = (length + 20) * 2 * S
    d = ImageDraw.Draw(img)
    box = (10 * S, 10 * S, (10 + length) * S, (10 + width) * S)
    d.ellipse(box, fill=(196, 204, 222, 255), outline=INK + (255,), width=6 * S)
    # 날개 끝 (검회색)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse((16 * S, 16 * S, (4 + length) * S, (4 + width) * S), fill=255)
    tipm = Image.new("L", img.size, 0)
    ImageDraw.Draw(tipm).rectangle(((10 + length * 0.68) * S, 0, img.width, img.height), fill=255)
    tip_layer = Image.new("RGBA", img.size, tip + (255,))
    img.paste(tip_layer, (0, 0), ImageChops.multiply(m, tipm))
    d.ellipse(box, outline=INK + (255,), width=6 * S)
    canvas = Image.new("RGBA", (sq, sq), (0, 0, 0, 0))
    canvas.alpha_composite(img, (sq // 2 - 16 * S, sq // 2 - img.height // 2))
    return canvas  # 피벗 = 캔버스 중앙(날개 뿌리)


WING = None


def draw_gull(wing_angle: float, blink: float, mouth: float, scarf) -> Image.Image:
    """캐릭터 1장을 그린다. wing_angle: 오른쪽 날개 각도(도), blink 0~1, mouth 0~1"""
    global WING
    if WING is None:
        WING = _wing()
    img = Image.new("RGBA", (BW * S, CH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 발
    for fx in (255, 385):
        _e(d, fx, 668, 46, 20, fill=(255, 150, 60, 255), outline=INK + (255,), width=5 * S)
    # 왼쪽 날개(몸 뒤)
    lw = WING.rotate(235, Image.BICUBIC)
    img.alpha_composite(lw, (int(128 * S - lw.width / 2), int(420 * S - lw.height / 2)))
    # 몸
    body = Image.new("L", img.size, 0)
    ImageDraw.Draw(body).ellipse((92 * S, 150 * S, 548 * S, 668 * S), fill=255)
    img.paste((255, 255, 255, 255), (0, 0), body)
    shade = ImageChops.subtract(body, body.transform(body.size, Image.AFFINE, (1, 0, 26 * S, 0, 1, 22 * S)))
    img.paste((222, 230, 244, 255), (0, 0), shade)
    d.ellipse((92 * S, 150 * S, 548 * S, 668 * S), outline=INK + (255,), width=7 * S)
    # 머리 깃털
    d.line([(312 * S, 156 * S), (300 * S, 112 * S), (330 * S, 96 * S)], fill=INK + (255,), width=7 * S, joint="curve")
    d.line([(328 * S, 154 * S), (348 * S, 116 * S)], fill=INK + (255,), width=7 * S)
    # 스카프
    sc = tuple(scarf) + (255,)
    d.chord((150 * S, 380 * S, 490 * S, 560 * S), 20, 160, fill=sc, outline=INK + (255,), width=6 * S)
    d.polygon([(360 * S, 520 * S), (430 * S, 545 * S), (395 * S, 610 * S)], fill=sc, outline=INK + (255,), width=5 * S)
    for k in range(4):
        _e(d, 210 + k * 70, 528 + (k % 2) * 6, 8, 8, fill=(255, 255, 255, 230))
    # 볼터치
    for cx in (196, 444):
        _e(d, cx, 410, 36, 21, fill=(255, 150, 170, 170))
    # 눈
    for ex in (248, 392):
        if blink > 0.5:
            d.arc(((ex - 28) * S, (318) * S, (ex + 28) * S, (362) * S), 200, 340, fill=INK + (255,), width=8 * S)
        else:
            ry = 36 * (1 - blink * 0.8)
            _e(d, ex, 336, 27, ry, fill=INK + (255,))
            _e(d, ex - 9, 336 - ry * 0.4, 9, 9, fill=(255, 255, 255, 255))
            _e(d, ex + 8, 336 + ry * 0.35, 4, 4, fill=(255, 255, 255, 220))
    # 부리 + 입
    if mouth > 0.02:
        _e(d, 320, 430 + 10 * mouth, 38, 10 + 26 * mouth, fill=(220, 70, 80, 255), outline=INK + (255,), width=5 * S)
        _e(d, 320, 444 + 18 * mouth, 20, 7 * mouth + 2, fill=(255, 140, 150, 255))
    _e(d, 320, 452 + 22 * mouth, 44, 15, fill=(255, 160, 50, 255), outline=INK + (255,), width=5 * S)
    _e(d, 320, 414, 58, 26, fill=(255, 196, 60, 255), outline=INK + (255,), width=5 * S)
    _e(d, 304, 406, 14, 6, fill=(255, 236, 170, 255))
    # 오른쪽 날개(인사) — 정사각 캔버스 중앙이 어깨 피벗
    full = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0))
    full.alpha_composite(img, (PAD * S, 0))
    img = full
    rw = WING.rotate(wing_angle, Image.BICUBIC)
    img.alpha_composite(rw, (int((512 + PAD) * S - rw.width / 2), int(410 * S - rw.height / 2)))
    return img.resize((CW, CH), Image.LANCZOS)


def _cloud(w, rng):
    h = int(w * 0.55)
    m = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(m)
    for _ in range(6):
        r = rng.uniform(0.14, 0.24) * w
        cx = rng.uniform(r, w - r)
        cy = h - r - rng.uniform(0, 0.1) * w
        d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=255)
    d.rounded_rectangle((0.12 * w * S, (h - 0.2 * w) * S, 0.88 * w * S, h * S - 1), int(0.1 * w * S), fill=255)
    out = Image.new("RGBA", m.size, INK + (0,))
    edge = m.filter(ImageFilter.MaxFilter(9))
    out.putalpha(edge)
    white = Image.new("RGBA", m.size, (255, 255, 255, 255))
    out.paste(white, (0, 0), m)
    return out.resize((w, h), Image.LANCZOS)


def _sun_rays(r=520, n=14, color=(255, 236, 160, 110)):
    img = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k in range(n):
        a0 = 2 * math.pi * k / n
        a1 = a0 + math.pi / n * 0.8
        d.polygon([(r, r), (r + r * math.cos(a0), r + r * math.sin(a0)), (r + r * math.cos(a1), r + r * math.sin(a1))],
                  fill=color)
    return img.filter(ImageFilter.GaussianBlur(3))


def build(d: dt.date, out: Path, brand: str = "", audio=True):
    rng = random.Random(d.toordinal() * 13 + 5)
    top, bottom, scarf = WEEK_STYLE[d.weekday()]
    bg = vertical_gradient(W, H, [(0, top), (0.75, bottom), (1, bottom)]).convert("RGBA")
    # 바다 + 모래
    bd = ImageDraw.Draw(bg)
    sun_rays = _sun_rays()
    sun = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    sd.ellipse((10, 10, 290, 290), fill=(255, 214, 90, 255), outline=INK + (255,), width=8)
    clouds = [(_cloud(rng.randint(220, 340), rng), rng.uniform(0, W), rng.uniform(600, 760), rng.uniform(14, 28))
              for _ in range(3)]
    sparkle_emojis = ["✨", "💛", "🎵", "☀️"]
    floaters = [(emoji_image(rng.choice(sparkle_emojis), rng.randint(48, 70)), rng.uniform(90, W - 90),
                 rng.uniform(0.8, 4.5), rng.uniform(80, 160), rng.uniform(0, 6.28)) for _ in range(9)]

    msg = character_message(d)
    msg_lines = msg.split("\n")
    mf = font("round", 66)
    line_imgs = [text_layer(l, mf, INK) for l in msg_lines]
    bw = max(li.width for li in line_imgs) + 120
    bh = sum(li.height for li in line_imgs) + 22 * (len(line_imgs) - 1) + 90
    bubble = Image.new("RGBA", (bw * S, (bh + 50) * S), (0, 0, 0, 0))
    bdr = ImageDraw.Draw(bubble)
    bdr.rounded_rectangle((4 * S, 4 * S, (bw - 4) * S, (bh - 4) * S), 48 * S, fill=(255, 255, 255, 255),
                          outline=INK + (255,), width=7 * S)
    tx = bw * 0.42
    bdr.polygon([((tx - 34) * S, (bh - 8) * S), ((tx + 30) * S, (bh - 8) * S), ((tx + 26) * S, (bh + 44) * S)],
                fill=(255, 255, 255, 255))
    bdr.line([((tx - 34) * S, (bh - 4) * S), ((tx + 26) * S, (bh + 44) * S), ((tx + 30) * S, (bh - 4) * S)],
             fill=INK + (255,), width=7 * S, joint="curve")
    bubble = bubble.resize((bw, bh + 50), Image.LANCZOS)

    t_month = text_layer(f"{d.month}월 {d.day}일", font("round", 116), (255, 255, 255), stroke=10, stroke_fill=INK)
    t_wd = text_layer(cal.WEEKDAYS[d.weekday()], font("round", 76), INK)
    t_year = text_layer(f"{d.year}", font("round", 46), INK)
    tag = weekday_tag(d)
    t_tag = text_layer(tag, font("round", 50), (255, 255, 255))
    ribbon = rounded_rect_layer(t_tag.width + 90, 92, 46, tuple(scarf) + (255,), INK + (255,), 5)
    t_name = text_layer("해피 갈매기", font("round", 38), INK)
    t_brand = text_layer(brand, font("round", 40), INK) if brand else None

    char_cache: dict = {}

    def gull(wing, blink, mouth):
        key = (round(wing / 3) * 3, round(blink, 1), round(mouth, 1))
        if key not in char_cache:
            char_cache[key] = draw_gull(key[0], key[1], key[2], scarf)
        return char_cache[key]

    char_shadow = Image.new("RGBA", (420, 70), (0, 0, 0, 0))
    ImageDraw.Draw(char_shadow).ellipse((0, 0, 419, 69), fill=(0, 0, 0, 50))
    char_shadow = char_shadow.filter(ImageFilter.GaussianBlur(6))

    bubble_y = 880
    char_base_y = 1640  # 발 위치

    def frame(t, i):
        img = bg.copy()
        # 해 + 햇살
        rays = sun_rays.rotate(t * 12, Image.BILINEAR)
        paste(img, rays, (980, 110))
        paste(img, sun, (980, 110))
        for c, x0, y, v in clouds:
            paste(img, c, ((x0 + v * t) % (W + 400) - 200, y + 6 * math.sin(t + x0)))
        # 바다/모래 (물결 애니메이션)
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fx)
        sea_y = 1500
        pts = [(x, sea_y + 10 * math.sin(x / 70 + t * 2.2)) for x in range(0, W + 20, 20)]
        fd.polygon(pts + [(W, H), (0, H)], fill=(110, 196, 236, 255))
        pts2 = [(x, sea_y + 70 + 12 * math.sin(x / 90 - t * 2.8)) for x in range(0, W + 20, 20)]
        fd.line(pts2, fill=(255, 255, 255, 200), width=8, joint="curve")
        sand_y = 1630
        pts3 = [(x, sand_y + 14 * math.sin(x / 120 + 1.5) + 8 * math.sin(x / 50 + t * 1.6)) for x in range(0, W + 20, 20)]
        fd.polygon(pts3 + [(W, H), (0, H)], fill=(255, 226, 170, 255))
        fd.line(pts3, fill=(255, 255, 255, 255), width=10, joint="curve")
        img.alpha_composite(fx)

        # 캐릭터 등장(떨어지며 통통)
        pdrop = progress(t, 0.0, 0.7)
        y_off = -900 * (1 - ease_out_cubic(pdrop) if pdrop < 1 else 0)
        land = t - 0.7
        if land > 0:
            squash = 0.1 * math.exp(-land * 6) * math.cos(land * 22)
        else:
            squash = 0
        bob = 8 * math.sin(t * 3.2) if t > 1.0 else 0
        sx, sy = 1 + squash, 1 - squash
        wave = 35 + 30 * math.sin(t * 7.5) if t > 0.9 else -60
        blink = 1.0 if (abs(t - 2.2) < 0.08 or abs(t - 4.3) < 0.08) else 0.0
        talking = 1.2 < t < 3.2
        mouth = (0.5 + 0.5 * math.sin(t * 18)) if talking else (0.25 if t > 3.2 else 0.0)
        g = gull(wave, blink, mouth)
        g2 = g.resize((int(CW * sx), int(CH * sy)), Image.BILINEAR) if squash else g
        sh_scale = 1 - min(1, abs(y_off) / 900) * 0.6
        paste(img, char_shadow.resize((max(1, int(420 * sh_scale)), max(1, int(70 * sh_scale)))),
              (W / 2, char_base_y - 30), 1)
        paste(img, g2, (W / 2 - g2.width / 2, char_base_y - g2.height + y_off + bob), anchor="lt")

        # 상단 날짜
        a = ease_out_back(progress(t, 0.1, 0.6))
        paste(img, t_year, (W / 2, 150), clamp(a))
        m2 = t_month.resize((max(1, int(t_month.width * clamp(a, 0.01, 2))), max(1, int(t_month.height * clamp(a, 0.01, 2)))),
                            Image.BILINEAR)
        paste(img, m2, (W / 2, 262), clamp(a * 1.5))
        a2 = ease_out_cubic(progress(t, 0.35, 0.5))
        paste(img, t_wd, (W / 2, 385 + 20 * (1 - a2)), a2)
        a3 = ease_out_back(progress(t, 0.55, 0.6))
        if a3 > 0:
            rib = ribbon.copy()
            rib.alpha_composite(t_tag, ((rib.width - t_tag.width) // 2, (rib.height - t_tag.height) // 2 - 2))
            rib = rib.rotate(-3 * clamp(a3), Image.BICUBIC, expand=True)
            rib = rib.resize((max(1, int(rib.width * clamp(a3, 0.01, 2))), max(1, int(rib.height * clamp(a3, 0.01, 2)))),
                             Image.BILINEAR)
            paste(img, rib, (W / 2, 515), clamp(a3 * 2))

        # 말풍선 + 한 줄씩 써지는 메시지
        pb = progress(t, 1.0, 0.5)
        if pb > 0:
            k = clamp(ease_out_back(pb), 0.01, 2)
            b2 = bubble.resize((max(1, int(bubble.width * k)), max(1, int(bubble.height * k))), Image.BILINEAR)
            paste(img, b2, (W / 2 + 30, bubble_y), clamp(pb * 2))
            if pb >= 1:
                total = sum(len(l) for l in msg_lines)
                shown = (t - 1.4) / 1.6 * total
                y = bubble_y - bubble.height / 2 + 45
                for li, line_txt in zip(line_imgs, msg_lines):
                    n = len(line_txt)
                    frac = clamp(shown / max(1, n))
                    if frac > 0:
                        k = int(round(frac * n))
                        if k <= 0:
                            shown -= n
                            y += li.height + 22
                            continue
                        wcut = li.width if k >= n else int(mf.getlength(line_txt[:k])) + 2
                        part = li.crop((0, 0, max(1, wcut), li.height))
                        img.alpha_composite(part, (int(W / 2 + 30 - li.width / 2), int(y)))
                    shown -= n
                    y += li.height + 22

        # 떠오르는 반짝이
        for e, x, st, v, ph in floaters:
            tt = t - st
            if tt <= 0:
                continue
            yy = 1350 - v * tt
            xx = x + 22 * math.sin(tt * 2 + ph)
            paste(img, e, (xx, yy), clamp(1 - tt / 2.2) * clamp(tt * 3))

        a4 = ease_out_cubic(progress(t, 1.2, 0.6))
        paste(img, t_name, (W / 2, 1800 if not t_brand else 1770), a4)
        if t_brand:
            paste(img, t_brand, (W / 2, 1840), a4)
        fo = progress(t, NFRAMES / FPS - 0.3, 0.3)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), fo * 0.5)
        return img

    snd = None
    if audio:
        # 통통 튀는 실로폰 멜로디 (C major)
        notes = [(0.7, 72, 0.4, 0.7), (0.85, 79, 0.4, 0.5),
                 (1.2, 76, 0.3, 0.5), (1.4, 77, 0.3, 0.5), (1.6, 79, 0.5, 0.6), (2.0, 84, 0.5, 0.6),
                 (2.4, 81, 0.3, 0.5), (2.6, 79, 0.5, 0.55), (3.1, 76, 0.3, 0.5), (3.3, 77, 0.3, 0.5),
                 (3.5, 74, 0.5, 0.5), (3.9, 72, 1.2, 0.6), (3.9, 76, 1.2, 0.4), (3.9, 79, 1.2, 0.35)]
        snd = finish_audio(melody(notes, decay=5.0, harmonics=((1, 1.0), (4, 0.25), (6.2, 0.08))), vol=0.5)
    render_video(out, frame, snd)
    return {"message": msg, "tag": tag}
