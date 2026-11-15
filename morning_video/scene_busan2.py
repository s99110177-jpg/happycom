"""영상 1 (스타일 B): 해운대 해변 + 잡지풍 타이포그래피."""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import calendar_kr as cal
from .messages import morning_message
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_in_out, ease_out_cubic, finish_audio, font, lerp,
                            melody, ocean_noise, paste, progress, radial_glow, render_video, text_layer,
                            vertical_gradient)
from .scene_busan import S, _down, _Gull, _ss

EN_WD = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
EN_MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
INK = (28, 40, 72)
HORIZON = 1110
SHORE = 1470


def _static(rng):
    sky = vertical_gradient(W, H, [(0, (150, 196, 232)), (0.32, (204, 226, 240)), (0.5, (252, 226, 206)),
                                   (HORIZON / H, (255, 214, 182)), (1, (255, 214, 182))]).convert("RGBA")
    far = _ss()
    d = ImageDraw.Draw(far)
    haze = (150, 160, 190, 255)
    # 왼쪽: 엘시티 3개 타워 + 달맞이 언덕
    pts = [(0, HORIZON * S)] + [(x * S, (HORIZON - 60 - 40 * math.sin(x / 300 * math.pi)) * S) for x in range(0, 330, 10)] + [(330 * S, HORIZON * S)]
    d.polygon(pts, fill=(140, 160, 170, 255))
    for bx, bh, bw in ((800, 500, 46), (858, 450, 42), (912, 410, 40)):
        top = HORIZON - bh
        d.polygon([(bx * S, HORIZON * S), (bx * S, (top + 30) * S), ((bx + bw / 2) * S, top * S),
                   ((bx + bw) * S, (top + 30) * S), ((bx + bw) * S, HORIZON * S)], fill=haze)
        for wy in range(int(top + 50), HORIZON - 20, 18):
            d.line(((bx + 6) * S, wy * S, (bx + bw - 6) * S, wy * S), fill=(170, 180, 205, 255), width=S)
    x = 0
    while x < 380:
        bw, bh = rng.randint(30, 50), rng.randint(40, 110)
        d.rectangle((x * S, (HORIZON - bh) * S, (x + bw) * S, HORIZON * S), fill=(165, 172, 198, 255))
        x += bw + rng.randint(0, 8)
    # 오른쪽: 동백섬 + 마린시티
    x = 960
    while x < W + 40:
        bw, bh = rng.randint(34, 56), rng.randint(150, 260)
        d.rounded_rectangle((x * S, (HORIZON - bh) * S, (x + bw) * S, HORIZON * S), 8 * S, fill=haze)
        x += bw + rng.randint(2, 10)
    pts = [(430 * S, HORIZON * S)] + [((430 + i * 8) * S, (HORIZON - 70 * math.sin(i / 40 * math.pi) ** 0.8) * S) for i in range(41)] + [(750 * S, HORIZON * S)]
    d.polygon(pts, fill=(96, 140, 120, 255))
    far = _down(far.filter(ImageFilter.GaussianBlur(S)))

    sea = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sea.paste(vertical_gradient(W, SHORE - HORIZON + 80, [(0, (150, 196, 214)), (1, (60, 150, 180))]), (0, HORIZON))
    sd = ImageDraw.Draw(sea)
    for _ in range(80):
        y = rng.uniform(HORIZON + 6, SHORE)
        k = (y - HORIZON) / (SHORE - HORIZON)
        x0 = rng.uniform(-40, W)
        sd.line((x0, y, x0 + lerp(20, 110, k), y), fill=(255, 255, 255, int(lerp(40, 70, k))), width=max(1, int(1 + 2 * k)))

    sand = vertical_gradient(W, H, [(0, (246, 222, 184)), (1, (232, 196, 150))]).convert("RGBA")
    # 파라솔
    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(deco)
    for px, py, col in ((150, 1640, (240, 90, 80)), (420, 1700, (60, 140, 220)), (860, 1660, (250, 190, 60)),
                        (650, 1820, (90, 190, 150))):
        pd.line((px, py, px + 8, py + 120), fill=(120, 90, 60, 255), width=6)
        pd.pieslice((px - 90, py - 50, px + 90, py + 50), 180, 360, fill=col + (255,))
        for k in range(1, 4):
            a = math.pi + k * math.pi / 4
            pd.line((px, py, px + 90 * math.cos(a), py + 50 * math.sin(a)), fill=(255, 255, 255, 200), width=3)
        pd.ellipse((px - 60, py + 112, px + 76, py + 132), fill=(0, 0, 0, 30))
    return sky, far, sea, sand, deco


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    rng = random.Random(d.toordinal() * 3 + 11)
    sky, far, sea, sand, deco = _static(rng)
    sun = radial_glow(620, (255, 246, 214), 255, 1.4)
    gulls = [_Gull(rng, (900, 980), (0.8, 1.1), (60, 110)) for _ in range(3)]

    t_wd_en = text_layer("  ".join(EN_WD[d.weekday()]), font("semibold", 34), INK)
    t_day = text_layer(f"{d.day}", font("bold", 300), INK)
    t_mon = text_layer(f"{EN_MON[d.month - 1]}  {d.year}", font("bold", 46), INK)
    t_kdate = text_layer(f"{d.year}년 {d.month}월 {d.day}일", font("semibold", 44), INK)
    t_kwd = text_layer(cal.WEEKDAYS[d.weekday()], font("bold", 78), (226, 92, 70))
    msg = morning_message(d)
    t_msg = text_layer(msg, font("serif", 62), INK, line_gap=0.45, align="left")
    t_place = text_layer("H A E U N D A E   ·   B U S A N", font("semibold", 30), (120, 86, 60))
    t_place_k = text_layer("부산 · 해운대의 아침", font("bold", 40), (110, 76, 50))
    t_brand = text_layer(brand, font("bold", 38), (110, 76, 50)) if brand else None
    LX = 84

    def frame(t, i):
        p = t / (NFRAMES / FPS)
        img = sky.copy()
        paste(img, sun, (830, lerp(1000, 900, ease_in_out(p))))
        img.alpha_composite(far)
        img.alpha_composite(sea)
        # 밀려왔다 빠지는 파도
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fx)
        reach = 50 * math.sin(t * 1.15 - 0.6)
        wet = [(x, SHORE + 60 + reach + 16 * math.sin(x / 90 + 1.3)) for x in range(0, W + 20, 20)]
        sand_mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(sand_mask).polygon([(x, y + 26) for x, y in wet] + [(W, H), (0, H)], fill=255)
        img.paste(sand, (0, 0), sand_mask)
        foam = [(x, SHORE + 40 + reach * 1.1 + 14 * math.sin(x / 70 + t * 1.8)) for x in range(0, W + 20, 20)]
        fd.polygon(foam + [(x, y + 40) for x, y in reversed(wet)], fill=(120, 190, 205, 150))
        fd.line(foam, fill=(255, 255, 255, 235), width=12, joint="curve")
        foam2 = [(x, SHORE - 10 + 10 * math.sin(x / 60 - t * 2.4)) for x in range(0, W + 20, 20)]
        fd.line(foam2, fill=(255, 255, 255, 160), width=6, joint="curve")
        img.alpha_composite(fx)
        img.alpha_composite(deco)
        gx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(gx)
        for g in gulls:
            g.draw(gd, t, (60, 70, 100, 220))
        img.alpha_composite(gx)

        # 잡지풍 날짜 블록 (왼쪽 정렬)
        a = ease_out_cubic(progress(t, 0.0, 0.6))
        paste(img, t_wd_en, (LX - 40 * (1 - a), 120), a, anchor="lt")
        a = ease_out_cubic(progress(t, 0.1, 0.7))
        paste(img, t_day, (LX - 4, 150 + 40 * (1 - a)), a, anchor="lt")
        dx = LX + t_day.width + 26
        a = ease_out_cubic(progress(t, 0.3, 0.6))
        paste(img, t_mon, (dx + 30 * (1 - a), 238), a, anchor="lt")
        paste(img, t_kwd, (dx + 30 * (1 - a), 300), a, anchor="lt")
        a = ease_out_cubic(progress(t, 0.45, 0.6))
        paste(img, t_kdate, (LX, 512), a, anchor="lt")
        bar_w = int(lerp(0, 120, ease_out_cubic(progress(t, 0.6, 0.6))))
        if bar_w > 1:
            ImageDraw.Draw(img).rectangle((LX, 600, LX + bar_w, 607), fill=(226, 92, 70, 255))
        # 메시지: 왼쪽에서 슬라이드
        am = ease_out_cubic(progress(t, 0.9, 0.9))
        paste(img, t_msg, (LX - 60 * (1 - am), 650), am, anchor="lt")
        # 하단 장소
        a = ease_out_cubic(progress(t, 1.5, 0.7))
        paste(img, t_place, (W / 2, 1600 + 10 * (1 - a)), a * 0.9)
        paste(img, t_place_k, (W / 2, 1560 + 10 * (1 - a)), a)
        if t_brand:
            paste(img, t_brand, (W / 2, 1860), a)
        fo = progress(t, NFRAMES / FPS - 0.35, 0.35)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), fo * 0.5)
        return img

    snd = None
    if audio:
        notes = [(0.2, 64, 2.4, 0.4), (0.8, 67, 2.4, 0.35), (1.4, 71, 2.6, 0.35), (2.1, 74, 2.6, 0.3),
                 (2.9, 71, 2.2, 0.3), (3.5, 76, 2.0, 0.3)]
        snd = finish_audio(ocean_noise(seed=d.toordinal() + 1) * 0.7 + melody(notes, decay=1.3) * 0.4, vol=0.5)
    render_video(out, frame, snd)
    return {"scene": "haeundae", "message": msg}
