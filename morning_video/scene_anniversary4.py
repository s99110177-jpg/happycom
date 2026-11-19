"""영상 2 (스타일 D): 칠판 손글씨 — 날짜와 오늘의 기념일이 분필로 써지고, 동그라미·별 낙서가 그려진다."""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from . import calendar_kr as cal
from .handmade import chalkify, fbm, scribble_ellipse, wipe
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_out_cubic, emoji_image, finish_audio, fit_font, font,
                            progress, render_video, text_layer)
from .scene_anniversary import _wrap_title

CHALK = (244, 244, 236)
YELLOW = (255, 226, 120)
PINK = (255, 168, 190)
BLUE = (160, 210, 255)


def _board(seed):
    rng = np.random.default_rng(seed)
    img = Image.new("RGB", (W, H), (120, 80, 50))
    d = ImageDraw.Draw(img)
    # 나무 테두리 결
    for y in range(0, H, 6):
        c = 110 + int(14 * math.sin(y / 23)) + int(rng.integers(-6, 6))
        d.line((0, y, W, y), fill=(c, int(c * 0.66), int(c * 0.42)))
    # 칠판 면 (얼룩진 지운 자국)
    smudge = fbm(H // 4, W // 4, 50, 4, rng)
    smudge = np.asarray(Image.fromarray((smudge * 255).astype(np.uint8)).resize((W - 100, H - 230), Image.BICUBIC),
                        dtype=np.float32) / 255
    base = np.array((34, 64, 52), dtype=np.float32)
    arr = base[None, None, :] + (smudge[..., None] - 0.5) * 30 + rng.normal(0, 3, (H - 230, W - 100, 1))
    # 지우개 자국 (가로로 긴 밝은 띠)
    erase = np.zeros(arr.shape[:2], dtype=np.float32)
    for _ in range(6):
        y0 = int(rng.integers(0, H - 330))
        x0 = int(rng.integers(0, W - 400))
        erase[y0:y0 + 90, x0:x0 + 380] = 8
    erase = np.asarray(Image.fromarray(erase.astype(np.uint8) * 30).filter(ImageFilter.GaussianBlur(30)), dtype=np.float32) / 30
    arr += erase[..., None]
    board = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    img.paste(board, (50, 50))
    # 분필 받침대 + 분필 + 지우개
    d.rectangle((30, H - 190, W - 30, H - 150), fill=(150, 100, 64))
    d.rectangle((30, H - 152, W - 30, H - 140), fill=(96, 62, 40))
    d.rounded_rectangle((140, H - 210, 230, H - 190), 6, fill=(250, 250, 245))
    d.rounded_rectangle((260, H - 208, 330, H - 190), 6, fill=(255, 190, 200))
    d.rounded_rectangle((W - 330, H - 230, W - 160, H - 190), 8, fill=(60, 70, 120))
    d.rectangle((W - 330, H - 205, W - 160, H - 190), fill=(220, 220, 210))
    return img.convert("RGBA")


def _chalk_text(text, kind, size, color, seed, line_gap=0.3):
    t = text_layer(text, font(kind, size), color, line_gap=line_gap)
    return chalkify(t, seed)


def _chalk_emoji(ch, size, seed):
    """이모지를 분필 낙서처럼: 윤곽선만 남기기."""
    e = emoji_image(ch, size)
    pad = 20
    canvas = Image.new("RGBA", (e.width + pad * 2, e.height + pad * 2), (0, 0, 0, 0))
    canvas.alpha_composite(e, (pad, pad))
    gray = ImageOps.grayscale(canvas.convert("RGB"))
    a = canvas.getchannel("A")
    edges = gray.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
    outline = a.filter(ImageFilter.MaxFilter(5)).point(lambda v: 255 if v > 100 else 0)
    inner = a.filter(ImageFilter.MinFilter(5)).point(lambda v: 255 if v > 100 else 0)
    ring = Image.fromarray(np.maximum(np.asarray(outline) - np.asarray(inner), 0).astype(np.uint8))
    mask = Image.fromarray(np.maximum(np.asarray(ring), np.asarray(edges) * (np.asarray(inner) > 0)).astype(np.uint8))
    # 원래 색을 흐리게 깔아 색분필 느낌
    out = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    tint = canvas.copy()
    tint.putalpha(a.point(lambda v: v * 70 // 255))
    out.alpha_composite(tint)
    line = Image.new("RGBA", canvas.size, CHALK + (255,))
    line.putalpha(mask)
    out.alpha_composite(line)
    return chalkify(out, seed, density=0.85)


def _star(size, color):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    r = size / 2 - 4
    pts = []
    for k in range(11):
        a = -math.pi / 2 + k * 4 * math.pi / 5
        pts.append((size / 2 + r * math.cos(a), size / 2 + r * math.sin(a)))
    ImageDraw.Draw(img).line(pts, fill=color + (255,), width=6, joint="curve")
    return img


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    seed = d.toordinal()
    rng = random.Random(seed)
    days = cal.days_of(d)
    dday = None
    if days:
        main, others = days[0], days[1:]
        head = "오늘의 기념일"
    else:
        nxt = cal.next_notable(d)
        main, dday = nxt if nxt else (cal.Day("평범해서 소중한 날", "특별한 일 없는 오늘도\n충분히 소중한 하루", "🍀", "green", "popular"), None)
        others = []
        head = "다가오는 기념일"
    board = _board(seed)
    solemn = main.solemn

    # 칠판 오른쪽 위: 날짜 (선생님이 쓰는 방식)
    t_date = _chalk_text(f"{d.month}월 {d.day}일 ({cal.WEEKDAYS_SHORT[d.weekday()]})", "pen", 92, CHALK, seed + 1)
    t_year = _chalk_text(f"{d.year}년 {cal.WEEKDAYS[d.weekday()]}", "pen", 60, BLUE, seed + 2)
    t_head = _chalk_text(head, "pen", 78, YELLOW, seed + 3)
    title = _wrap_title(main.name, 9)
    tf = fit_font(title, "pen", 860, 150 if "\n" not in title else 120)
    t_title = chalkify(text_layer(title, tf, CHALK, line_gap=0.1), seed + 4)
    t_desc = _chalk_text(main.desc, "pen", 84, CHALK, seed + 5, line_gap=0.25)
    t_dday = _chalk_text(f"D-{dday}", "pen", 120, PINK, seed + 6) if dday else None
    t_others = _chalk_text("같은 날: " + ", ".join(o.name for o in others[:3]), "pen", 52, BLUE, seed + 7) if others else None
    t_brand = _chalk_text(brand, "pen", 60, CHALK, seed + 8) if brand else None
    emo = _chalk_emoji(main.emoji, 210, seed + 9)
    circle = scribble_ellipse((t_title.width + 120, t_title.height + 90), PINK + (230,), 7, seed)
    under = Image.new("RGBA", (t_head.width + 20, 20), (0, 0, 0, 0))
    ImageDraw.Draw(under).line([(0, 12), (t_head.width * 0.5, 8), (t_head.width + 20, 12)], fill=YELLOW + (220,), width=6)
    stars = [(_star(rng.randint(50, 80), rng.choice([YELLOW, PINK, BLUE])),
              rng.choice([rng.uniform(110, 190), rng.uniform(890, 970)]), rng.uniform(560, 1500))
             for _ in range(5)] if not solemn else []

    title_y = 1010
    desc_y = title_y + t_title.height / 2 + 70 + (150 if t_dday else 0) + t_desc.height / 2

    def frame(t, i):
        img = board.copy()
        # 시간 순서대로 써 내려감
        img.alpha_composite(wipe(t_date, progress(t, 0.0, 0.7)), (W - 90 - t_date.width, 110))
        img.alpha_composite(wipe(t_year, progress(t, 0.5, 0.5)), (W - 90 - t_year.width, 230))
        img.alpha_composite(wipe(t_head, progress(t, 0.8, 0.6)), (110, 380))
        img.alpha_composite(wipe(under, progress(t, 1.3, 0.3)), (100, 380 + t_head.height + 4))
        pe = ease_out_cubic(progress(t, 1.3, 0.6))
        if pe > 0:
            e2 = emo.copy()
            e2.putalpha(e2.getchannel("A").point(lambda v: int(v * pe)))
            img.alpha_composite(e2, (int(W / 2 - e2.width / 2), int(700 - e2.height / 2 + 4 * math.sin(t * 2))))
        img.alpha_composite(wipe(t_title, progress(t, 1.7, 0.9)), (int(W / 2 - t_title.width / 2), int(title_y - t_title.height / 2)))
        if not solemn:
            cf = progress(t, 2.6, 0.6)
            if cf > 0:
                c = circle(cf)
                img.alpha_composite(c, (int(W / 2 - c.width / 2), int(title_y - c.height / 2)))
        if t_dday:
            img.alpha_composite(wipe(t_dday, progress(t, 2.6, 0.4)),
                                (int(W / 2 - t_dday.width / 2), int(title_y + t_title.height / 2 + 60)))
        img.alpha_composite(wipe(t_desc, progress(t, 2.9, 1.1)), (int(W / 2 - t_desc.width / 2), int(desc_y - t_desc.height / 2)))
        if t_others:
            img.alpha_composite(wipe(t_others, progress(t, 3.8, 0.6)), (int(W / 2 - t_others.width / 2), int(desc_y + t_desc.height / 2 + 60)))
        if t_brand:
            img.alpha_composite(wipe(t_brand, progress(t, 3.9, 0.5)), (110, H - 300))
        for k, (s, x, y) in enumerate(stars):
            sp = progress(t, 3.4 + k * 0.15, 0.3)
            if sp > 0:
                s2 = s.copy()
                s2.putalpha(s2.getchannel("A").point(lambda v: int(v * sp)))
                img.alpha_composite(s2, (int(x - s.width / 2), int(y - s.height / 2)))
        fo = progress(t, NFRAMES / FPS - 0.3, 0.3)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (20, 40, 32, 255)), fo * 0.5)
        return img

    snd = None
    if audio:
        from .render_common import SR, DURATION
        n = int(DURATION * SR)
        rng2 = np.random.default_rng(seed)
        sig = np.zeros(n)
        # 분필 사각사각: 글씨 쓰는 구간마다 짧은 노이즈 버스트
        for st, du in ((0.0, 0.7), (0.5, 0.5), (0.8, 0.6), (1.7, 0.9), (2.6, 0.6), (2.9, 1.1), (3.8, 0.6)):
            t = np.arange(int(du * SR)) / SR
            noise = rng2.standard_normal(len(t))
            env = (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 7 * t))) * 0.18
            i0 = int(st * SR)
            sig[i0:i0 + len(t)] += (noise * env)[: n - i0]
        k = np.ones(8) / 8
        sig = np.convolve(sig, k, mode="same")
        snd = finish_audio(sig, vol=0.35)
    render_video(out, frame, snd)
    return {"main": main.name, "others": [o.name for o in others], "dday": dday}
