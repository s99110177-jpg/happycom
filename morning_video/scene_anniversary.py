"""영상 2: 오늘의 기념일 (기념일이 없으면 다가오는 기념일 D-day)."""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import calendar_kr as cal
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_in_out, ease_out_back, ease_out_cubic, emoji_image,
                            finish_audio, fit_font, font, lerp, melody, paste, progress, radial_glow,
                            render_video, rounded_rect_layer, soft_shadow, text_layer, vertical_gradient)

THEMES = {
    #        top            bottom          accent          confetti
    "red":    ((255, 120, 110), (196, 40, 70), (255, 230, 120)),
    "orange": ((255, 190, 100), (240, 110, 60), (255, 250, 200)),
    "yellow": ((250, 190, 70), (225, 110, 40), (255, 250, 210)),
    "green":  ((150, 220, 140), (40, 140, 100), (255, 250, 190)),
    "teal":   ((120, 220, 210), (30, 120, 150), (255, 245, 190)),
    "blue":   ((120, 190, 255), (40, 80, 190), (255, 240, 170)),
    "navy":   ((70, 100, 180), (20, 30, 80), (255, 220, 130)),
    "purple": ((190, 150, 250), (90, 50, 160), (255, 230, 170)),
    "pink":   ((255, 180, 210), (220, 80, 140), (255, 250, 220)),
    "brown":  ((220, 170, 120), (120, 70, 40), (255, 240, 200)),
    "gray":   ((170, 180, 195), (70, 80, 100), (255, 240, 200)),
    "solemn": ((60, 70, 100), (14, 18, 34), (235, 225, 200)),
}
CONFETTI = [(255, 255, 255), (255, 230, 90), (255, 120, 150), (120, 220, 255), (150, 255, 170), (255, 170, 80)]


def _wrap_title(name: str, max_chars=11) -> str:
    if len(name) <= max_chars or " " not in name:
        return name
    words = name.split(" ")
    best, best_diff = name, 1e9
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        diff = abs(len(a) - len(b))
        if diff < best_diff:
            best, best_diff = f"{a}\n{b}", diff
    return best


def _bokeh(rng, n=14):
    items = []
    for _ in range(n):
        r = rng.randint(40, 160)
        g = radial_glow(r * 2, (255, 255, 255), rng.randint(40, 90), 0.8)
        items.append((g, rng.uniform(0, W), rng.uniform(0, H), rng.uniform(-14, 14), rng.uniform(-30, -8), rng.uniform(0, 6)))
    return items


def build(d: dt.date, out: Path, brand: str = "", audio=True):
    days = cal.days_of(d)
    rng = random.Random(d.toordinal() * 7 + 1)
    dday = None
    if days:
        main, others = days[0], days[1:]
        label = "오늘은"
    else:
        nxt = cal.next_notable(d)
        main, dday = (nxt if nxt else (cal.Day("평범해서 소중한 날", "특별한 일 없는 오늘도\n충분히 소중한 하루", "🍀", "green", "popular"), None))
        others = []
        label = "다가오는 기념일" if dday else "오늘은"
    solemn = main.solemn
    top, bottom, accent = THEMES.get(main.theme, THEMES["blue"])
    bg = vertical_gradient(W, H, [(0, top), (1, bottom)]).convert("RGBA")
    # 은은한 비네팅
    vg = radial_glow(int(H * 1.6), (255, 255, 255), 50, 1.2)
    paste(bg, vg, (W / 2, H * 0.4))
    bokeh = _bokeh(rng)

    text_col = (255, 255, 255)
    shadow = (0, 4, 12, (0, 0, 0, 90))
    pill_txt = text_layer(cal.korean_date(d), font("bold", 44), text_col)
    pill = rounded_rect_layer(pill_txt.width + 80, 92, 46, (255, 255, 255, 50), (255, 255, 255, 150), 3)
    t_label = text_layer(label, font("semibold", 52), accent, shadow=shadow)

    circle_r = 210
    circle = Image.new("RGBA", (circle_r * 4, circle_r * 4), (0, 0, 0, 0))
    ImageDraw.Draw(circle).ellipse((0, 0, circle_r * 4 - 1, circle_r * 4 - 1),
                                   fill=(255, 255, 255, 235) if not solemn else (255, 255, 255, 40),
                                   outline=None)
    circle = circle.resize((circle_r * 2, circle_r * 2), Image.LANCZOS)
    ring = Image.new("RGBA", (circle_r * 4 + 80, circle_r * 4 + 80), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, ring.width - 1, ring.height - 1), outline=(255, 255, 255, 130), width=8)
    ring = ring.resize((ring.width // 2, ring.height // 2), Image.LANCZOS)
    circle_sh = soft_shadow(circle, 24, (0, 0, 0, 70))
    emo = emoji_image(main.emoji, 250)

    title = _wrap_title(main.name)
    tf = fit_font(title, "bold", 960, 118 if "\n" not in title else 96)
    t_title = text_layer(title, tf, text_col, line_gap=0.18, shadow=(0, 6, 16, (0, 0, 0, 110)))
    t_desc = text_layer(main.desc, font("semibold", 50), (255, 255, 255), line_gap=0.4, shadow=shadow)
    t_dday = text_layer(f"D-{dday}", font("bold", 120), accent, shadow=shadow) if dday else None

    t_others = None
    if others:
        names = [o.name for o in others[:4]]
        lines, cur = [], ""
        for n in names:
            cand = f"{cur} · {n}" if cur else n
            if font("semibold", 38).getbbox(cand)[2] > 900 and cur:
                lines.append(cur)
                cur = n
            else:
                cur = cand
        lines.append(cur)
        t_others_head = text_layer("함께하는 날", font("bold", 36), accent)
        t_others = text_layer("\n".join(lines), font("semibold", 38), (255, 255, 255), line_gap=0.35)
    doy = d.timetuple().tm_yday
    left = (dt.date(d.year, 12, 31) - d).days
    t_year = text_layer(f"올해의 {doy}번째 날 · 올해 남은 날 {left}일", font("regular", 34), (255, 255, 255))
    t_brand = text_layer(brand, font("bold", 38), (255, 255, 255)) if brand else None

    # 파티클
    confetti = []
    if not solemn:
        for _ in range(70):
            confetti.append([rng.uniform(0, W), rng.uniform(-500, -20), rng.uniform(200, 420), rng.uniform(-60, 60),
                             rng.uniform(0, 6.28), rng.uniform(2, 6), rng.choice(CONFETTI + [accent]),
                             rng.uniform(14, 26), rng.uniform(0.4, 3.0)])
    lights = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(3, 9), rng.uniform(20, 60), rng.uniform(0, 6.28))
              for _ in range(60)]

    title_y = 1105 if "\n" not in title else 1135
    desc_y = title_y + t_title.height / 2 + 40 + t_desc.height / 2
    if t_dday:
        desc_y += 150

    def frame(t, i):
        img = bg.copy()
        for g, x0, y0, vx, vy, ph in bokeh:
            paste(img, g, ((x0 + vx * t) % (W + 300) - 150, (y0 + vy * t) % (H + 300) - 150),
                  0.6 + 0.4 * math.sin(t + ph))
        if solemn:
            fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(fx)
            for x, y0, r, v, ph in lights:
                y = (y0 - v * t) % H
                a = int(120 * (0.5 + 0.5 * math.sin(t * 1.5 + ph)))
                ld.ellipse((x - r, y - r, x + r, y + r), fill=(255, 240, 200, a))
            img.alpha_composite(fx)
        # 날짜 필
        a = ease_out_cubic(progress(t, 0.0, 0.5))
        paste(img, pill, (W / 2, 220 - 30 * (1 - a)), a)
        paste(img, pill_txt, (W / 2, 220 - 30 * (1 - a)), a)
        a = ease_out_cubic(progress(t, 0.15, 0.5))
        paste(img, t_label, (W / 2, 400 + 20 * (1 - a)), a)
        # 이모지 원
        pe = progress(t, 0.25, 0.8)
        if pe > 0:
            sc = ease_out_back(pe) if not solemn else ease_out_cubic(pe)
            sc = max(0.01, sc)
            bob = 10 * math.sin((t - 0.25) * 2.4) if not solemn else 4 * math.sin(t * 1.2)
            cy = 720 + bob
            rp = ease_out_cubic(progress(t, 0.6, 1.4))
            if rp > 0 and rp < 1:
                rr = ring.resize((max(1, int(ring.width * (0.9 + 0.4 * rp))),) * 2, Image.BILINEAR)
                paste(img, rr, (W / 2, cy), (1 - rp) * 0.9)
            for layer, k in ((circle_sh, 1.0), (circle, 1.0)):
                l2 = layer.resize((max(1, int(layer.width * sc)), max(1, int(layer.height * sc))), Image.BILINEAR)
                paste(img, l2, (W / 2, cy + (14 if layer is circle_sh else 0)), min(1, pe * 2))
            ang = 6 * math.sin(t * 2.0) if not solemn else 0
            e2 = emo.resize((max(1, int(emo.width * sc)), max(1, int(emo.height * sc))), Image.BICUBIC).rotate(ang, Image.BICUBIC, expand=True)
            paste(img, e2, (W / 2, cy), min(1, pe * 2))
        # 제목/설명
        a = ease_out_cubic(progress(t, 0.6, 0.6))
        paste(img, t_title, (W / 2, title_y + 40 * (1 - a)), a)
        if t_dday:
            a2 = ease_out_back(progress(t, 0.9, 0.6))
            paste(img, t_dday, (W / 2, title_y + t_title.height / 2 + 90), clamp(a2))
        a = ease_out_cubic(progress(t, 1.0, 0.6))
        paste(img, t_desc, (W / 2, desc_y + 30 * (1 - a)), a)
        if t_others:
            a = ease_out_cubic(progress(t, 1.4, 0.6))
            base_y = desc_y + t_desc.height / 2 + 70
            paste(img, t_others_head, (W / 2, base_y), a)
            paste(img, t_others, (W / 2, base_y + 30 + t_others.height / 2), a)
        a = ease_out_cubic(progress(t, 1.7, 0.6))
        paste(img, t_year, (W / 2, 1800 if not t_brand else 1760), a * 0.85)
        if t_brand:
            paste(img, t_brand, (W / 2, 1830), a)
        # 컨페티
        if confetti:
            fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            cd = ImageDraw.Draw(fx)
            for c in confetti:
                x0, y0, vy, vx, ph, spin, col, size, delay = c
                tt = t - delay
                if tt < 0:
                    continue
                y = y0 + vy * tt
                if y > H + 40:
                    continue
                x = x0 + vx * tt + 30 * math.sin(tt * 2 + ph)
                ang = ph + spin * tt
                w = size * abs(math.cos(ang))
                h = size * 0.5
                ca, sa = math.cos(ang * 0.7), math.sin(ang * 0.7)
                pts = [(x + dx * ca - dy * sa, y + dx * sa + dy * ca) for dx, dy in
                       ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
                cd.polygon(pts, fill=col + (235,))
            img.alpha_composite(fx)
        fo = progress(t, NFRAMES / FPS - 0.3, 0.3)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (0, 0, 0, 255) if solemn else (255, 255, 255, 255)), fo * 0.4)
        return img

    snd = None
    if audio:
        if solemn:
            notes = [(0.3, 57, 3.5, 0.5), (0.3, 64, 3.5, 0.35), (1.6, 60, 3.5, 0.4), (2.8, 64, 3.0, 0.35), (2.8, 69, 3.0, 0.3)]
            snd = finish_audio(melody(notes, decay=0.7), vol=0.45)
        else:
            notes = [(0.5, 72, 0.8, 0.6), (0.62, 76, 0.8, 0.6), (0.74, 79, 0.8, 0.6), (0.86, 84, 1.6, 0.7),
                     (1.5, 88, 1.2, 0.35), (1.7, 91, 1.2, 0.3), (2.4, 84, 1.8, 0.4), (2.4, 79, 1.8, 0.3),
                     (3.4, 86, 1.5, 0.3), (3.6, 88, 2.0, 0.35)]
            snd = finish_audio(melody(notes, decay=2.5), vol=0.5)
    render_video(out, frame, snd)
    return {"main": main.name, "others": [o.name for o in others], "dday": dday}
