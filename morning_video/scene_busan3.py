"""영상 1 (스타일 C): 레트로 여행 포스터 — 용두산 부산타워와 부산항, 리소그래프 질감."""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import calendar_kr as cal
from .messages import morning_message
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_out_back, ease_out_cubic, finish_audio, font, lerp,
                            melody, ocean_noise, paste, progress, render_video, text_layer)

# 제한된 포스터 팔레트
CREAM = (246, 234, 208)
NAVY = (30, 52, 90)
TEAL = (38, 128, 140)
CORAL = (232, 98, 74)
MUSTARD = (240, 180, 66)
SAND = (236, 200, 150)
INKC = (34, 30, 40)
EN_WD = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
EN_MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
FRAME = 48  # 포스터 테두리


def _grain(seed, strength=18):
    rng = np.random.default_rng(seed)
    g = rng.normal(0, strength, (H, W)).astype(np.float32)
    g = np.asarray(Image.fromarray(np.clip(g + 128, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)),
                   dtype=np.float32) - 128
    return g


def _poster(rng):
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    # 해 (큰 원 + 줄무늬)
    cx, cy, r = 560, 900, 300
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=MUSTARD)
    for k in range(6):
        y = cy + 80 + k * 38
        d.rectangle((cx - r, y, cx + r, y + 12 + k * 3), fill=CREAM)
    # 먼 산 (영도 봉래산)
    d.polygon([(FRAME, 1180), (220, 1060), (420, 1110), (640, 1010), (880, 1090), (W - FRAME, 1050), (W - FRAME, 1210),
               (FRAME, 1210)], fill=TEAL)
    # 용두산 + 부산타워
    d.ellipse((60, 1120, 640, 1560), fill=NAVY)
    tx = 330
    d.polygon([(tx - 20, 1160), (tx - 10, 760), (tx + 10, 760), (tx + 20, 1160)], fill=CORAL)
    d.ellipse((tx - 62, 712, tx + 62, 790), fill=CORAL)
    d.rectangle((tx - 48, 742, tx + 48, 760), fill=CREAM)
    d.rectangle((tx - 5, 620, tx + 5, 715), fill=CORAL)
    d.ellipse((tx - 10, 606, tx + 10, 626), fill=CORAL)
    # 항구 크레인 (오른쪽)
    for bx in (760, 900):
        d.rectangle((bx, 1020, bx + 14, 1240), fill=CORAL)
        d.rectangle((bx + 70, 1020, bx + 84, 1240), fill=CORAL)
        d.rectangle((bx - 60, 1000, bx + 150, 1022), fill=CORAL)
        d.line((bx + 40, 1000, bx + 40, 950), fill=CORAL, width=10)
        d.line((bx + 40, 950, bx - 60, 1000), fill=CORAL, width=5)
        d.line((bx + 40, 950, bx + 150, 1000), fill=CORAL, width=5)
    # 바다
    d.rectangle((FRAME, 1240, W - FRAME, 1640), fill=NAVY)
    # 컨테이너 더미
    for i, col in enumerate((CORAL, MUSTARD, TEAL, CREAM, CORAL, TEAL)):
        d.rectangle((700 + i * 52, 1196 - (i % 2) * 22, 748 + i * 52, 1240), fill=col)
    # 앞쪽 해변/부두
    d.polygon([(FRAME, 1640), (W - FRAME, 1590), (W - FRAME, H - FRAME), (FRAME, H - FRAME)], fill=SAND)
    return img


def _ship():
    s = Image.new("RGBA", (300, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    d.polygon([(10, 80), (290, 80), (250, 130), (40, 130)], fill=CORAL + (255,))
    d.rectangle((80, 40, 200, 80), fill=CREAM + (255,))
    d.rectangle((150, 10, 172, 40), fill=INKC + (255,))
    for x in range(95, 190, 26):
        d.rectangle((x, 52, x + 12, 64), fill=NAVY + (255,))
    return s


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    rng = random.Random(d.toordinal() * 41)
    base = _poster(rng)
    grain = _grain(d.toordinal())
    ship = _ship()
    msg = morning_message(d)

    t_busan = text_layer("BUSAN", font("bold", 230), CORAL, stroke=0)
    t_tag = text_layer("GOOD MORNING FROM KOREA", font("semibold", 34), NAVY)
    t_daynum = text_layer(f"{d.day:02d}", font("bold", 150), NAVY)
    t_mon = text_layer(f"{EN_MON[d.month - 1]} {d.year}", font("bold", 40), NAVY)
    t_wd = text_layer(f"{cal.WEEKDAYS[d.weekday()]} · {EN_WD[d.weekday()]}", font("bold", 40), CORAL)
    t_kdate = text_layer(cal.korean_date(d), font("semibold", 40), INKC)
    t_msg = text_layer(msg, font("serif", 58), INKC, line_gap=0.4)
    t_loc = text_layer("YONGDUSAN · BUSAN TOWER · BUSAN PORT", font("semibold", 26), NAVY)
    t_brand = text_layer(brand, font("bold", 36), NAVY) if brand else None
    stamp = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    sd.ellipse((6, 6, 214, 214), outline=CORAL + (255,), width=8)
    sd.ellipse((26, 26, 194, 194), outline=CORAL + (255,), width=3)
    st = text_layer(f"{d.month}.{d.day}", font("bold", 62), CORAL)
    stamp.alpha_composite(st, ((220 - st.width) // 2, 64))
    st2 = text_layer(EN_WD[d.weekday()], font("bold", 30), CORAL)
    stamp.alpha_composite(st2, ((220 - st2.width) // 2, 140))

    def frame(t, i):
        img = base.copy().convert("RGBA")
        dr = ImageDraw.Draw(img)
        # 파도 줄무늬 (움직임)
        for k in range(7):
            y = 1280 + k * 50
            off = (t * (30 + k * 6) + k * 40) % 120
            for x in range(FRAME - 120, W - FRAME, 120):
                xx = x + off
                dr.arc((xx, y - 14, xx + 60, y + 14), 200, 340, fill=CREAM + (255,), width=5)
        # 배
        sx = lerp(W - 300, 520, ease_out_cubic(t / (NFRAMES / FPS)))
        img.alpha_composite(ship, (int(sx), int(1300 + 5 * math.sin(t * 2.5))))
        # 갈매기 두 마리 (포스터풍 V)
        for k, (gx0, gy) in enumerate(((560, 1010), (700, 940))):
            gx = gx0 + 40 * t
            flap = 14 * math.sin(t * 6 + k)
            dr.line([(gx - 34, gy + flap), (gx, gy), (gx + 34, gy + flap)], fill=INKC + (255,), width=7, joint="curve")
        # 리소 질감(그레인)
        arr = np.asarray(img.convert("RGB"), dtype=np.float32) + grain[..., None]
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        dr = ImageDraw.Draw(img)
        # 테두리
        dr.rectangle((FRAME / 2, FRAME / 2, W - FRAME / 2, H - FRAME / 2), outline=NAVY + (255,), width=6)

        # 타이포
        a = ease_out_cubic(progress(t, 0.0, 0.6))
        paste(img, t_tag, (W / 2, 120 - 20 * (1 - a)), a)
        a = ease_out_cubic(progress(t, 0.15, 0.7))
        paste(img, t_busan, (W / 2, 250 + 40 * (1 - a)), a)
        a = ease_out_cubic(progress(t, 0.4, 0.6))
        x0 = W / 2 - (t_daynum.width + 30 + max(t_mon.width, t_wd.width)) / 2
        paste(img, t_daynum, (x0, 380 + 20 * (1 - a)), a, anchor="lt")
        paste(img, t_mon, (x0 + t_daynum.width + 30, 410), a, anchor="lt")
        paste(img, t_wd, (x0 + t_daynum.width + 30, 470), a, anchor="lt")
        # 메시지: 크림색 띠 위
        am = ease_out_cubic(progress(t, 0.9, 0.8))
        if am > 0:
            bw = int(lerp(0, t_msg.width + 120, am))
            box_h = t_msg.height + 60
            by = H - FRAME - 70 - box_h
            dr.rectangle((W / 2 - bw / 2, by, W / 2 + bw / 2, by + box_h), fill=CREAM + (255,), outline=NAVY + (255,), width=4)
            paste(img, t_msg, (W / 2, by + box_h / 2), clamp((am - 0.5) * 2))
        a = ease_out_cubic(progress(t, 1.4, 0.6))
        paste(img, t_kdate, (W / 2, 590), a)
        paste(img, t_loc, (W / 2, H - FRAME - 24), a)
        if t_brand:
            paste(img, t_brand, (W / 2, H - FRAME - 64), a)
        # 우표 도장 '쾅'
        ps = progress(t, 1.8, 0.35)
        if ps > 0:
            sc = lerp(1.8, 1.0, ease_out_cubic(ps))
            s2 = stamp.resize((int(220 * sc), int(220 * sc)), Image.BILINEAR).rotate(-14, Image.BICUBIC, expand=True)
            paste(img, s2, (880, 650), clamp(ps * 2) * 0.9)
        fo = progress(t, NFRAMES / FPS - 0.3, 0.3)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), CREAM + (255,)), fo * 0.5)
        return img

    snd = None
    if audio:
        notes = [(0.2, 67, 0.5, 0.5), (0.45, 71, 0.5, 0.5), (0.7, 74, 0.8, 0.55), (1.8, 60, 0.4, 0.8),
                 (2.2, 72, 0.5, 0.45), (2.45, 74, 0.5, 0.45), (2.7, 76, 0.5, 0.45), (2.95, 79, 1.4, 0.5),
                 (3.8, 74, 1.4, 0.35), (3.8, 71, 1.4, 0.3)]
        snd = finish_audio(melody(notes, decay=2.6) + ocean_noise(seed=d.toordinal() + 7) * 0.3, vol=0.5)
    render_video(out, frame, snd)
    return {"scene": "retro-poster yongdusan", "message": msg}
