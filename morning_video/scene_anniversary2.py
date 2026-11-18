"""영상 2 (스타일 B): 일력(한 장씩 넘기는 달력) — 어제 장이 뜯겨 나가고 오늘의 기념일이 나타난다."""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from . import calendar_kr as cal
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_in_out, ease_out_back, ease_out_cubic, emoji_image,
                            finish_audio, fit_font, font, lerp, melody, paste, progress, render_video,
                            text_layer, vertical_gradient)
from .scene_anniversary import _wrap_title

PW, PH = 880, 1360          # 종이 크기
PAPER = (253, 249, 238)
INK = (40, 40, 52)
RED = (214, 58, 52)
BLUE = (48, 96, 196)


def _lunar(d: dt.date) -> str:
    try:
        from korean_lunar_calendar import KoreanLunarCalendar
        c = KoreanLunarCalendar()
        c.setSolarDate(d.year, d.month, d.day)
        iso = c.LunarIsoFormat()
        y, m, dd = iso[:10].split("-")
        leap = "윤" if "Intercalation" in iso else ""
        return f"음력 {leap}{int(m)}월 {int(dd)}일"
    except Exception:
        return ""


def _day_color(d: dt.date, days):
    if d.weekday() == 6 or any(x.kind == "holiday" for x in days):
        return RED
    if d.weekday() == 5:
        return BLUE
    return INK


def _page(d: dt.date, header_col, with_body=True):
    """일력 한 장 (본문 기념일 영역은 따로 애니메이션하므로 비워 둘 수 있음)."""
    days = cal.days_of(d)
    img = Image.new("RGBA", (PW, PH), PAPER + (255,))
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, 0, PW, 150), fill=header_col + (255,))
    ht = text_layer(f"{d.year}  ·  {d.month}월", font("bold", 56), (255, 255, 255))
    img.alpha_composite(ht, ((PW - ht.width) // 2, 52))
    col = _day_color(d, days)
    big = text_layer(str(d.day), font("bold", 380), col)
    img.alpha_composite(big, ((PW - big.width) // 2, 175))
    wd = text_layer(cal.WEEKDAYS[d.weekday()], font("bold", 84), col)
    img.alpha_composite(wd, ((PW - wd.width) // 2, 610))
    lu = text_layer(_lunar(d), font("regular", 38), (130, 126, 120))
    img.alpha_composite(lu, ((PW - lu.width) // 2, 725))
    # 점선 절취선
    for x in range(40, PW - 40, 26):
        dr.line((x, 805, x + 13, 805), fill=(200, 192, 176, 255), width=3)
    # 종이 결
    rng = random.Random(d.toordinal())
    for _ in range(500):
        x, y = rng.uniform(0, PW), rng.uniform(150, PH)
        dr.point((x, y), fill=(230, 222, 204, 255))
    return img


def _binder():
    img = Image.new("RGBA", (PW + 40, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 40, PW + 39, 100), 16, fill=(70, 66, 74, 255))
    d.rounded_rectangle((6, 44, PW + 33, 60), 8, fill=(110, 106, 116, 255))
    for x in (PW * 0.25, PW * 0.75):
        d.rounded_rectangle((x - 16, 0, x + 56, 110), 30, outline=(150, 150, 160, 255), width=12)
    return img


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    days = cal.days_of(d)
    dday = None
    if days:
        main, others = days[0], days[1:]
        head = "오늘은"
    else:
        nxt = cal.next_notable(d)
        main, dday = nxt if nxt else (cal.Day("평범해서 소중한 날", "특별한 일 없는 오늘도\n충분히 소중한 하루", "🍀", "green", "popular"), None)
        others = []
        head = "다가오는 기념일" if dday else "오늘은"
    solemn = main.solemn
    header_col = (70, 76, 96) if solemn else (RED if _day_color(d, days) == RED else (36, 52, 92))
    prev = d - dt.timedelta(days=1)

    bg_top, bg_bot = ((226, 220, 210), (186, 176, 162)) if not solemn else ((120, 124, 136), (60, 62, 74))
    bg = vertical_gradient(W, H, [(0, bg_top), (1, bg_bot)]).convert("RGBA")
    bd = ImageDraw.Draw(bg)
    rng = random.Random(d.toordinal() + 99)
    for _ in range(260):  # 벽지 도트
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        bd.ellipse((x - 3, y - 3, x + 3, y + 3), fill=tuple(int(c * 0.94) for c in bg_top) + (255,))

    page_today = _page(d, header_col)
    page_prev = _page(prev, (70, 76, 96))
    stack = Image.new("RGBA", (PW + 20, PH + 24), (0, 0, 0, 0))   # 아래쪽 남은 장들
    sd = ImageDraw.Draw(stack)
    for k in range(4, 0, -1):
        sd.rectangle((k * 3, k * 5, PW - 1 + k * 3, PH - 1 + k * 5), fill=(236, 230, 214, 255), outline=(210, 202, 186, 255))
    shadow = Image.new("RGBA", (PW + 120, PH + 120), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle((60, 70, PW + 60, PH + 70), fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(26))
    binder = _binder()
    cx, top = W / 2, 330

    t_head = text_layer(head, font("semibold", 42), header_col)
    emo = emoji_image(main.emoji, 160)
    title = _wrap_title(main.name, 12)
    t_title = text_layer(title, fit_font(title, "bold", PW - 120, 92 if "\n" not in title else 70), INK, line_gap=0.15)
    t_desc = text_layer(main.desc.replace("\n", " ") if len(main.desc) < 24 else main.desc,
                        font("semibold", 42), (96, 92, 88), line_gap=0.35)
    t_dday = text_layer(f"D-{dday}", font("bold", 64), RED) if dday else None
    t_others = text_layer("함께하는 날 · " + " · ".join(o.name for o in others[:3]), font("semibold", 34), (60, 56, 60) if not solemn else (240, 240, 245)) if others else None
    t_top = text_layer("오늘의 기념일", font("bold", 56), (60, 56, 60) if not solemn else (240, 240, 245))
    t_brand = text_layer(brand, font("bold", 40), (60, 56, 60) if not solemn else (240, 240, 245)) if brand else None

    body_y = top + 830   # 절취선 아래

    def frame(t, i):
        img = bg.copy()
        paste(img, t_top, (W / 2, 190), ease_out_cubic(progress(t, 0.0, 0.5)))
        paste(img, shadow, (cx, top + PH / 2))
        paste(img, stack, (cx - PW / 2, top), anchor="lt")
        img.alpha_composite(page_today, (int(cx - PW / 2), top))
        # 오늘 본문: 기념일
        a = ease_out_cubic(progress(t, 1.2, 0.5))
        paste(img, t_head, (cx, body_y + 30 + 20 * (1 - a)), a)
        pe = progress(t, 1.35, 0.6)
        if pe > 0:
            sc = clamp(ease_out_back(pe) if not solemn else ease_out_cubic(pe), 0.01, 2)
            e2 = emo.resize((max(1, int(emo.width * sc)), max(1, int(emo.height * sc))), Image.BICUBIC)
            paste(img, e2, (cx, body_y + 150 + 5 * math.sin(t * 2.5)), clamp(pe * 2))
        a = ease_out_cubic(progress(t, 1.55, 0.5))
        ty = body_y + 255 + t_title.height / 2
        paste(img, t_title, (cx, ty + 24 * (1 - a)), a)
        y2 = ty + t_title.height / 2 + 20
        if t_dday:
            a2 = clamp(ease_out_back(progress(t, 1.8, 0.5)))
            paste(img, t_dday, (cx, y2 + t_dday.height / 2), a2)
            y2 += t_dday.height + 10
        a = ease_out_cubic(progress(t, 1.8, 0.5))
        paste(img, t_desc, (cx, y2 + t_desc.height / 2 + 10), a)
        if t_others:
            paste(img, t_others, (cx, top + PH + 70), ease_out_cubic(progress(t, 2.1, 0.5)))
        # 어제 장 뜯겨 날아감
        pt = progress(t, 0.35, 0.9)
        if pt < 1:
            k = ease_in_out(pt)
            ang = -lerp(0, 38, k)
            pg = page_prev.rotate(ang, Image.BICUBIC, expand=True)
            x = cx + lerp(0, 900, k ** 1.4)
            y = top + PH / 2 - lerp(0, 520, k) + 260 * k * k
            if pt <= 0:
                img.alpha_composite(page_prev, (int(cx - PW / 2), top))
            else:
                paste(img, pg, (x, y), 1 - k * 0.3)
        img.alpha_composite(binder, (int(cx - binder.width / 2), top - 70))
        if t_brand:
            paste(img, t_brand, (W / 2, 1850), ease_out_cubic(progress(t, 2.0, 0.5)))
        fo = progress(t, NFRAMES / FPS - 0.3, 0.3)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), fo * 0.35)
        return img

    snd = None
    if audio:
        import numpy as np
        from .render_common import SR, DURATION
        n = int(DURATION * SR)
        rip = np.zeros(n)
        st = int(0.4 * SR)
        L = int(0.45 * SR)
        noise = np.random.default_rng(1).standard_normal(L)
        env = np.exp(-np.linspace(0, 5, L)) * (0.6 + 0.4 * np.random.default_rng(2).random(L))
        rip[st:st + L] = noise * env * 0.5          # 종이 찢는 소리
        notes = ([(1.3, 67, 1.5, 0.5), (1.5, 72, 1.5, 0.5), (1.7, 76, 2.5, 0.55), (2.6, 79, 2.5, 0.4)]
                 if not solemn else [(1.3, 60, 3.5, 0.4), (2.2, 64, 3.0, 0.35)])
        snd = finish_audio(rip + melody(notes, decay=2.0 if not solemn else 0.8), vol=0.5)
    render_video(out, frame, snd)
    return {"main": main.name, "others": [o.name for o in others], "dday": dday}
