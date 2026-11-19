"""영상 2 (스타일 C): 네온사인 — 어두운 벽돌 벽에 기념일 이름이 '지직' 켜지는 네온."""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import calendar_kr as cal
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_out_cubic, emoji_image, finish_audio, fit_font, font,
                            lerp, melody, paste, progress, render_video, text_layer)
from .scene_anniversary import _wrap_title

NEON = {  # theme -> (메인 네온색, 보조 네온색)
    "red": ((255, 70, 90), (255, 200, 80)), "orange": ((255, 140, 50), (90, 220, 255)),
    "yellow": ((255, 220, 60), (255, 90, 170)), "green": ((80, 255, 140), (255, 220, 80)),
    "teal": ((60, 240, 230), (255, 110, 200)), "blue": ((80, 170, 255), (255, 220, 90)),
    "navy": ((120, 150, 255), (255, 200, 90)), "purple": ((200, 110, 255), (90, 230, 255)),
    "pink": ((255, 100, 200), (100, 230, 255)), "brown": ((255, 170, 90), (120, 220, 255)),
    "gray": ((210, 220, 240), (255, 200, 120)), "solemn": ((230, 230, 245), (180, 200, 255)),
}


def _bricks(seed, dark=False):
    rng = np.random.default_rng(seed)
    img = Image.new("RGB", (W, H), (22, 18, 26))
    d = ImageDraw.Draw(img)
    bw, bh = 150, 64
    for row in range(H // bh + 1):
        off = (bw // 2) * (row % 2)
        for col in range(-1, W // bw + 2):
            x, y = col * bw + off, row * bh
            v = rng.integers(-8, 9)
            base = (54 + v, 34 + v, 38 + v) if not dark else (40 + v, 40 + v, 48 + v)
            d.rectangle((x + 4, y + 4, x + bw - 4, y + bh - 4), fill=base)
    arr = np.asarray(img, dtype=np.float32)
    arr += rng.normal(0, 5, arr.shape)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.7 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2.2
    arr *= np.clip(vig, 0.25, 1)[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


def _neon(text, size, color, kind="round", glow=1.0):
    """튜브(흰 심지+색 테두리) + 두 겹 글로우."""
    f = font(kind, size)
    core = text_layer(text, f, (255, 255, 255), stroke=max(2, size // 22), stroke_fill=color, line_gap=0.2)
    pad = 70
    canvas = Image.new("RGBA", (core.width + pad * 2, core.height + pad * 2), (0, 0, 0, 0))
    mask = Image.new("L", canvas.size, 0)
    mask.paste(core.getchannel("A"), (pad, pad))
    for blur, a in ((34, 0.9), (12, 1.0)):
        g = Image.new("RGBA", canvas.size, color + (0,))
        g.putalpha(mask.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: min(255, int(v * a * glow * 1.6))))
        canvas.alpha_composite(g)
    canvas.alpha_composite(core, (pad, pad))
    return canvas


def _flicker(t, start, seed):
    """켜지는 순간 지직거리다가 안정."""
    if t < start:
        return 0.0
    tt = t - start
    if tt > 0.5:
        return 0.93 + 0.07 * math.sin(t * 37 + seed)
    pattern = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1]
    return 0.15 + 0.85 * pattern[min(len(pattern) - 1, int(tt / 0.05))]


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    days = cal.days_of(d)
    dday = None
    if days:
        main, others = days[0], days[1:]
        head = "TODAY IS"
    else:
        nxt = cal.next_notable(d)
        main, dday = nxt if nxt else (cal.Day("평범해서 소중한 날", "특별한 일 없는 오늘도\n충분히 소중한 하루", "🍀", "green", "popular"), None)
        others = []
        head = "COMING SOON"
    c1, c2 = NEON.get(main.theme, NEON["blue"])
    wall = _bricks(d.toordinal(), dark=main.solemn)

    title = _wrap_title(main.name, 9)
    tsize = fit_font(title, "round", 860, 140 if "\n" not in title else 112).size
    n_head = _neon(head, 60, c2, "bold")
    n_title = _neon(title, tsize, c1)
    n_date = _neon(f"{d.month}.{d.day}  {cal.WEEKDAYS[d.weekday()]}", 92, c2)
    n_dday = _neon(f"D-{dday}", 120, c2) if dday else None
    t_year = text_layer(cal.korean_date(d), font("semibold", 40), (230, 225, 240))
    t_desc = text_layer(main.desc, font("semibold", 48), (240, 236, 245), line_gap=0.4,
                        shadow=(0, 0, 16, c1 + (160,)))
    t_others = text_layer("함께하는 날 · " + " · ".join(o.name for o in others[:3]), font("semibold", 34), (200, 196, 214)) if others else None
    emo = emoji_image(main.emoji, 210)
    t_brand = text_layer(brand, font("bold", 38), (230, 225, 240)) if brand else None
    n_bye = _neon("좋은 하루 보내세요", 64, c2)

    # 네온 테두리 프레임
    frame_l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame_l)
    fd.rounded_rectangle((70, 560, W - 70, 1420), 60, outline=c1 + (255,), width=10)
    glow_f = frame_l.filter(ImageFilter.GaussianBlur(18))
    frame_l = Image.alpha_composite(Image.alpha_composite(glow_f, glow_f), frame_l)
    fd2 = ImageDraw.Draw(frame_l)
    fd2.rounded_rectangle((70, 560, W - 70, 1420), 60, outline=(255, 255, 255, 230), width=3)

    title_y = 1000 if not n_dday else 940

    def frame(t, i):
        img = wall.copy()
        # 바닥에 비친 네온 빛 (벽 전체가 은은하게 물듦)
        on = _flicker(t, 0.6, 1)
        if on > 0:
            tint = Image.new("RGBA", (W, H), c1 + (int(26 * on),))
            img.alpha_composite(tint)
        paste(img, n_date, (W / 2, 230), _flicker(t, 0.1, 3))
        paste(img, t_year, (W / 2, 350), ease_out_cubic(progress(t, 0.3, 0.6)) * 0.9)
        paste(img, frame_l, (W / 2, H / 2), _flicker(t, 0.35, 5))
        paste(img, n_head, (W / 2, 660), _flicker(t, 0.5, 7))
        pe = ease_out_cubic(progress(t, 0.9, 0.6))
        paste(img, emo, (W / 2, 800 + 10 * math.sin(t * 2.2)), pe)
        paste(img, n_title, (W / 2, title_y), on)
        if n_dday:
            paste(img, n_dday, (W / 2, title_y + n_title.height / 2 + 30), _flicker(t, 1.3, 11))
        a = ease_out_cubic(progress(t, 1.6, 0.7))
        paste(img, t_desc, (W / 2, 1260 + 20 * (1 - a)), a)
        if t_others:
            paste(img, t_others, (W / 2, 1520), ease_out_cubic(progress(t, 2.0, 0.6)))
        paste(img, n_bye, (W / 2, 1680), _flicker(t, 2.2, 13))
        if t_brand:
            paste(img, t_brand, (W / 2, 1820), ease_out_cubic(progress(t, 2.0, 0.6)))
        fo = progress(t, NFRAMES / FPS - 0.35, 0.35)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (0, 0, 0, 255)), fo * 0.6)
        return img

    snd = None
    if audio:
        from .render_common import SR, DURATION
        n = int(DURATION * SR)
        tt = np.arange(n) / SR
        hum = 0.08 * np.sin(2 * np.pi * 120 * tt) * (tt > 0.6)  # 네온 웅 소리
        buzz = np.zeros(n)
        rng = np.random.default_rng(3)
        for st in (0.1, 0.35, 0.5, 0.6):  # 지직
            i0, L = int(st * SR), int(0.18 * SR)
            buzz[i0:i0 + L] += rng.standard_normal(L) * 0.25 * (rng.random(L) > 0.6)
        notes = ([(1.0, 64, 2.0, 0.4), (1.0, 71, 2.0, 0.3), (1.8, 69, 2.5, 0.35), (2.6, 76, 2.5, 0.3)]
                 if not main.solemn else [(1.0, 57, 3.5, 0.35), (2.0, 64, 3.0, 0.3)])
        snd = finish_audio(hum + buzz + melody(notes, decay=1.0), vol=0.5)
    render_video(out, frame, snd)
    return {"main": main.name, "others": [o.name for o in others], "dday": dday}
