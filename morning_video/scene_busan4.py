"""영상 1 (스타일 D): 수채화 — 태종대 절벽과 하얀 등대, 물감이 번지며 그림이 완성된다."""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import calendar_kr as cal
from .handmade import fbm, multiply, paper, watercolor
from .messages import morning_message
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_in_out, ease_out_cubic, finish_audio, font, melody,
                            ocean_noise, paste, progress, render_video, text_layer)

INK = (52, 58, 80)
CLIFF = [(600, 1780), (630, 1450), (670, 1290), (720, 1180), (780, 1110), (850, 1075), (960, 1060), (W - 40, 1066),
         (W - 40, 1780)]


def _mask(draw_fn):
    m = Image.new("L", (W, H), 0)
    draw_fn(ImageDraw.Draw(m))
    return m


def _painting(seed):
    rng = random.Random(seed)
    base = paper((250, 246, 236), seed, strength=12)
    layers = []
    # 하늘 워시 (위는 푸르게, 수평선 근처는 살구빛)
    layers.append(watercolor(_mask(lambda d: d.rectangle((40, 60, W - 40, 1150), fill=255)), (150, 196, 232), seed + 1,
                             opacity=0.55, bleed=30))
    layers.append(watercolor(_mask(lambda d: d.ellipse((40, 820, W - 40, 1240), fill=255)), (255, 196, 150), seed + 2,
                             opacity=0.5, bleed=40))
    # 해
    layers.append(watercolor(_mask(lambda d: d.ellipse((220, 840, 380, 1000), fill=255)), (255, 170, 90), seed + 3,
                             opacity=0.7, bleed=6))
    # 먼 섬(주전자섬/영도 능선)
    layers.append(watercolor(_mask(lambda d: d.polygon([(40, 1130), (150, 1090), (300, 1110), (380, 1135), (40, 1150)], fill=255)),
                             (130, 150, 180), seed + 4, opacity=0.6, bleed=4))
    # 바다
    def sea(d):
        d.rectangle((40, 1140, W - 40, 1780), fill=255)
        d.polygon(CLIFF, fill=0)
    layers.append(watercolor(_mask(sea), (70, 140, 190), seed + 5, opacity=0.7, bleed=8))
    def sea2(d):
        d.polygon([(40, 1460), (W - 40, 1380), (W - 40, 1780), (40, 1780)], fill=255)
        d.polygon(CLIFF, fill=0)
    layers.append(watercolor(_mask(sea2), (40, 100, 160), seed + 6, opacity=0.35, bleed=50))
    # 절벽 (오른쪽)
    layers.append(watercolor(_mask(lambda d: d.polygon(CLIFF, fill=255)), (214, 168, 120), seed + 7, opacity=0.8, bleed=5))
    layers.append(watercolor(_mask(lambda d: d.polygon([(640, 1780), (680, 1520), (720, 1380), (790, 1560), (770, 1780)], fill=255)),
                             (150, 110, 90), seed + 8, opacity=0.45, bleed=8))
    # 절벽 위 소나무 숲
    def pines(d):
        for _ in range(16):
            x = rng.uniform(760, W - 30)
            y = 1080 - rng.uniform(0, 30)
            r = rng.uniform(26, 48)
            d.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.6), fill=255)
    layers.append(watercolor(_mask(pines), (60, 120, 80), seed + 9, opacity=0.8, bleed=4))
    # 등대 (하얀 몸통 = 종이 여백, 그림자와 지붕만 칠함)
    lx = 830
    layers.append(watercolor(_mask(lambda d: d.polygon([(lx - 6, 1040), (lx + 34, 1040), (lx + 30, 820), (lx + 14, 820)], fill=255)),
                             (150, 160, 190), seed + 10, opacity=0.55, bleed=2))
    layers.append(watercolor(_mask(lambda d: d.polygon([(lx - 24, 820), (lx + 34, 820), (lx + 5, 770)], fill=255)),
                             (200, 80, 70), seed + 11, opacity=0.85, bleed=2))
    img = base
    for l in layers:
        img = multiply(img, l)
    # 등대 외곽선 + 절벽 결 (펜)
    d = ImageDraw.Draw(img)
    d.line(CLIFF[:-1], fill=INK + (150,), width=3, joint="curve")
    for k in range(7):
        y = 1180 + k * 80
        d.line([(720 + k * 12, y), (800 + k * 10, y + 14), (880, y + 6), (960, y + 22)], fill=(120, 80, 60, 110), width=3)
    d.line([(lx - 34, 1040), (lx - 22, 820), (lx + 34, 820), (lx + 34, 1040)], fill=INK + (200,), width=3)
    d.line([(lx - 24, 820), (lx + 5, 770), (lx + 34, 820)], fill=INK + (200,), width=3)
    for wy in (870, 930, 990):
        d.rectangle((lx - 4, wy, lx + 10, wy + 22), outline=INK + (180,), width=2)
    return img


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    seed = d.toordinal()
    painting = _painting(seed)
    blank = paper((250, 246, 236), seed, strength=12)
    # 물감이 번지며 그림이 드러나는 순서 (노이즈 임계값)
    rng = np.random.default_rng(seed + 50)
    reveal = fbm(H // 4, W // 4, 70, 4, rng)
    reveal = np.asarray(Image.fromarray((reveal * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), dtype=np.float32) / 255
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    reveal = reveal * 0.55 + yy * 0.45
    p_arr, b_arr = np.asarray(painting, dtype=np.float32), np.asarray(blank, dtype=np.float32)

    msg = morning_message(d)
    t_date = text_layer(f"{d.year}. {d.month}. {d.day}.", font("pen", 96), INK)
    t_wd = text_layer(cal.WEEKDAYS[d.weekday()], font("pen", 130), (200, 80, 70))
    t_msg = text_layer(msg, font("pen", 84), INK, line_gap=0.25)
    t_loc = text_layer("부산 영도 · 태종대의 아침", font("pen", 56), (110, 90, 80))
    t_brand = text_layer(brand, font("pen", 56), INK) if brand else None

    def frame(t, i):
        k = clamp(ease_in_out(progress(t, 0.0, 1.6)) * 1.25)
        if k < 1:
            m = np.clip((k * 1.15 - reveal) * 10, 0, 1)[..., None]
            img = Image.fromarray((b_arr * (1 - m) + p_arr * m).astype(np.uint8), "RGBA")
        else:
            img = painting.copy()
        dr = ImageDraw.Draw(img)
        # 파도 붓터치 (흰 물감 점) 와 갈매기
        for j in range(18):
            x = (j * 131 + t * (18 + j % 5 * 4)) % (W - 80) + 40
            y = 1200 + (j * 47) % 520
            if x < 600:
                a = int(150 + 80 * math.sin(t * 2 + j))
                dr.line((x, y, x + 26 + j % 3 * 10, y - 2), fill=(255, 255, 255, a), width=4)
        for g, (x0, y0) in enumerate(((260, 760), (380, 800), (480, 740))):
            x, y = x0 + 30 * t, y0 + 6 * math.sin(t * 2 + g)
            f = 10 * math.sin(t * 7 + g)
            dr.line([(x - 26, y + f), (x - 10, y - 4), (x, y), (x + 10, y - 4), (x + 26, y + f)], fill=INK + (220,),
                    width=4, joint="curve")
        a = ease_out_cubic(progress(t, 0.8, 0.8))
        paste(img, t_date, (W / 2, 190 + 20 * (1 - a)), a)
        a = ease_out_cubic(progress(t, 1.0, 0.8))
        paste(img, t_wd, (W / 2, 320 + 20 * (1 - a)), a)
        a = ease_out_cubic(progress(t, 1.6, 1.0))
        paste(img, t_msg, (W / 2, 560 + 20 * (1 - a)), a)
        a = ease_out_cubic(progress(t, 2.2, 0.8))
        paste(img, t_loc, (W / 2, 1840), a)
        if t_brand:
            paste(img, t_brand, (W / 2, 1770), a)
        fo = progress(t, NFRAMES / FPS - 0.3, 0.3)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (250, 246, 236, 255)), fo * 0.5)
        return img

    snd = None
    if audio:
        notes = [(0.2, 69, 2.2, 0.4), (0.7, 72, 2.2, 0.35), (1.2, 76, 2.4, 0.35), (1.9, 74, 2.4, 0.3),
                 (2.6, 72, 2.4, 0.3), (3.3, 77, 2.2, 0.3), (3.3, 81, 2.2, 0.25)]
        snd = finish_audio(melody(notes, decay=1.1, harmonics=((1, 1.0), (2, 0.2))) + ocean_noise(seed=seed + 2) * 0.35,
                           vol=0.5)
    render_video(out, frame, snd)
    return {"scene": "watercolor taejongdae", "message": msg}
