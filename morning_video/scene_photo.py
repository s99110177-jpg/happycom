"""실사풍(사진 같은 렌더링) 영상: 새벽 광안대교와 바다.

외부 사진 없이 노이즈 구름, 하늘 산란광, 반짝이는 수면, 빛 번짐, 렌즈 플레어, 필름 그레인으로
사진처럼 보이도록 계산해서 그린다. assets/busan/ 에 실제 사진이 있으면 scene_busan 의 사진 모드를 쓰는 편이 더 사실적이다.
"""
from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import calendar_kr as cal
from .messages import morning_message
from .render_common import (FPS, H, NFRAMES, W, clamp, ease_in_out, ease_out_cubic, finish_audio, font, lerp,
                            melody, ocean_noise, paste, progress, render_video, text_layer)
from .scene_busan import _gwangan_static

HOR = 1180  # 수평선


def _fbm(h, w, base_x, base_y, octaves, rng, gain=0.55):
    out = np.zeros((h, w), dtype=np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gx = max(2, int(w / base_x * 2 ** o))
        gy = max(2, int(h / base_y * 2 ** o))
        g = rng.random((gy, gx)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += amp * np.asarray(im, dtype=np.float32) / 255.0
        tot += amp
        amp *= gain
    return out / tot


def _grad(h, stops):
    ys = np.linspace(0, 1, h)
    cols = np.array([s[1] for s in stops], dtype=np.float32)
    pos = [s[0] for s in stops]
    return np.stack([np.interp(ys, pos, cols[:, c]) for c in range(3)], axis=1)  # (h,3)


def _static(seed):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    # 하늘: 새벽 산란광
    sky_col = _grad(H, [(0, (18, 28, 62)), (0.25, (46, 58, 108)), (0.45, (128, 96, 128)),
                        (0.56, (226, 134, 98)), (HOR / H, (255, 196, 136)), (1, (255, 196, 136))])
    sky = np.repeat(sky_col[:, None, :], W, axis=1)

    # 구름: 가로로 길게 늘어진 층운
    small = _fbm(H // 4, W // 4, 260, 60, 6, rng)
    cloud = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), dtype=np.float32) / 255
    band = np.clip(1 - np.abs(yy - 760) / 520, 0, 1) ** 0.7
    cov = np.clip((cloud - 0.44) * 2.6, 0, 1) * band
    cov[HOR - 20:] = 0
    return rng, sky, cov, xx, yy


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    seed = d.toordinal()
    rng, sky, cov, xx, yy = _static(seed)
    sun_x = 600.0

    # 실루엣 (광안대교 + 해운대 스카이라인) — 일러스트 레이어의 형태만 사용
    import random as _r
    _, far, _, br = _gwangan_static(_r.Random(seed))
    far_a = np.asarray(far.filter(ImageFilter.GaussianBlur(1.5)).getchannel("A"), dtype=np.float32) / 255
    br_a = np.asarray(br.filter(ImageFilter.GaussianBlur(0.6)).getchannel("A"), dtype=np.float32) / 255
    lights = np.zeros((H, W), dtype=np.float32)
    lrng = np.random.default_rng(seed + 5)
    ys_, xs_ = np.nonzero(far_a[: HOR - 4] > 0.9)
    pick = lrng.choice(len(ys_), size=min(260, len(ys_)), replace=False)
    lights[ys_[pick], xs_[pick]] = lrng.uniform(0.4, 1, len(pick))
    for x in range(10, W, 36):   # 다리 조명
        lights[1112, x] = 1.0
    lights = np.asarray(Image.fromarray((lights * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)),
                        dtype=np.float32) / 255 * 6

    # 수면 리플 텍스처 (가로로 매우 길쭉한 노이즈, 원근감 위해 아래로 갈수록 크게)
    wrng = np.random.default_rng(seed + 9)
    ripple_a = _fbm(H // 2, W // 2, 50, 3, 4, wrng)
    ripple_b = _fbm(H // 2, W // 2, 90, 5, 4, wrng)
    ripple_a = np.asarray(Image.fromarray((ripple_a * 255).astype(np.uint8)).resize((W, H * 2), Image.BICUBIC), dtype=np.float32) / 255
    ripple_b = np.asarray(Image.fromarray((ripple_b * 255).astype(np.uint8)).resize((W, H * 2), Image.BICUBIC), dtype=np.float32) / 255

    depth = np.clip((yy - HOR) / (H - HOR), 0, 1)
    vign = 1 - 0.55 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.7)) ** 2)
    vign = np.clip(vign, 0.35, 1)[..., None]

    # 텍스트
    msg = morning_message(d)
    days = cal.days_of(d)
    sub = days[0].name if days and days[0].kind in ("special", "holiday", "busan") else ""
    sh = (0, 3, 12, (0, 0, 0, 170))
    en = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][d.weekday()]
    t_small = text_layer(f"{d.year} . {d.month:02d} . {d.day:02d}   {en}", font("regular", 36), (255, 240, 225), shadow=sh)
    t_date = text_layer(f"{d.month}월 {d.day}일 {cal.WEEKDAYS[d.weekday()]}", font("serif", 84), (255, 255, 255), shadow=sh)
    t_sub = text_layer(sub, font("semibold", 44), (255, 214, 160), shadow=sh) if sub else None
    t_msg = text_layer(msg, font("serif", 64), (255, 255, 255), line_gap=0.5, shadow=(0, 3, 16, (0, 0, 0, 200)))
    t_loc = text_layer("BUSAN · GWANGANDAEGYO", font("regular", 30), (255, 240, 225), shadow=sh)
    t_brand = text_layer(brand, font("semibold", 38), (255, 255, 255), shadow=sh) if brand else None
    line = Image.new("RGBA", (90, 3), (255, 255, 255, 200))

    def scene(t):
        p = t / (NFRAMES / FPS)
        sun_y = lerp(1215, 1110, ease_in_out(p))
        rise = clamp((1215 - sun_y) / 105)
        dx, dy = xx - sun_x, yy - sun_y
        r2 = dx * dx + dy * dy
        # 하늘 + 태양 산란(미 산란)
        glow = (np.exp(-r2 / (2 * 140 ** 2)) * 1.2 + np.exp(-r2 / (2 * 520 ** 2)) * 0.55) * (0.6 + 0.6 * rise)
        img = sky + glow[..., None] * np.array([255, 170, 100], dtype=np.float32)
        # 구름: 태양 쪽은 밝은 주황 테두리, 나머지는 푸른 회색
        lit = np.exp(-r2 / (2 * 600 ** 2))[..., None]
        cloud_col = (np.array([84, 80, 116], dtype=np.float32) * (1 - lit) + np.array([300, 170, 120], dtype=np.float32) * lit)
        c = np.roll(cov, int(t * 6), axis=1)[..., None]
        img = img * (1 - c * 0.85) + cloud_col * c * 0.85
        # 태양 원반
        disc = np.clip((62 - np.sqrt(r2)) / 3, 0, 1)[..., None]
        img = img * (1 - disc) + np.array([1400, 1250, 1000], dtype=np.float32) * disc
        # 원경 실루엣 (대기 원근: 푸른 안개)
        img = img * (1 - far_a[..., None] * 0.75) + np.array([120, 92, 120], dtype=np.float32) * far_a[..., None] * 0.75
        # 바다
        dep = depth[HOR:, :, None]
        off = int(t * 22) % H
        ra = ripple_a[off:off + H - HOR]
        rb = ripple_b[H - (off // 2) - (H - HOR): H - (off // 2)]
        rip = (ra * 0.6 + rb * 0.4)
        shift = ((rip - 0.5) * 30).astype(np.int32)
        rows = np.arange(H - HOR)[:, None]
        mirror = np.flipud(img[2 * HOR - H:HOR])  # 하늘 반사 (물결에 일렁임)
        rr = np.clip(rows + shift // 3, 0, H - HOR - 1)
        rcx = np.clip(xx[HOR:].astype(np.int32) + shift, 0, W - 1)
        refl = mirror[rr, rcx]
        base = refl * (0.55 - 0.25 * dep) + np.array([10, 18, 40], dtype=np.float32) * (0.45 + 0.25 * dep)
        spec_w = 30 + 190 * depth[HOR:]
        column = np.exp(-((xx[HOR:] - sun_x) ** 2) / (2 * spec_w ** 2))
        glint = np.clip((rip - 0.58) * 10, 0, 1) ** 2 * column * (0.5 + 0.9 * rise)
        broad = np.clip((rip - 0.45) * 3, 0, 1) * column * 0.5
        sea = base + (glint[..., None] * np.array([255, 230, 180], dtype=np.float32) * 3.0
                      + broad[..., None] * np.array([255, 150, 90], dtype=np.float32))
        # 다리 반사 (일렁임)
        ry = np.clip(2 * HOR - yy[HOR:].astype(np.int32) + shift, 0, H - 1)
        rx = np.clip(xx[HOR:].astype(np.int32) + shift // 2, 0, W - 1)
        bref = br_a[ry, rx] * 0.35 * (1 - dep[..., 0]) ** 1.5
        sea = sea * (1 - bref[..., None])
        img[HOR:] = sea
        # 다리 실루엣 + 조명
        img = img * (1 - br_a[..., None] * 0.96) + np.array([16, 14, 30], dtype=np.float32) * br_a[..., None] * 0.96
        flick = 0.85 + 0.15 * math.sin(t * 9)
        img += lights[..., None] * np.array([255, 200, 120], dtype=np.float32) * 0.25 * flick
        # 블룸
        bright = np.clip(img - 225, 0, None)
        bl = Image.fromarray(np.clip(bright * 3, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
        bl = bl.filter(ImageFilter.GaussianBlur(14)).resize((W, H), Image.BILINEAR)
        img += np.asarray(bl, dtype=np.float32) * 0.9
        # 렌즈 플레어 (태양-화면 중심 축 위의 고스트)
        cx, cy = W / 2, H / 2
        for k, (rad, col, a) in enumerate(((40, (255, 200, 140), 0.10), (90, (140, 200, 255), 0.06),
                                           (24, (255, 160, 220), 0.12), (140, (255, 220, 160), 0.04))):
            f = 0.6 + k * 0.45
            gx, gy = sun_x + (cx - sun_x) * 2 * f, sun_y + (cy - sun_y) * 2 * f
            g = np.exp(-((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * rad ** 2)) * a * rise
            img += g[..., None] * np.array(col, dtype=np.float32)
        # 색보정 + 비네팅 + 필름 그레인
        img = img * vign
        img = 255 * (1 - np.exp(-img * 1.45 / 255))  # 부드러운 톤매핑 (밝은 부분만 압축)
        grain = np.random.default_rng(int(t * 1000)).normal(0, 4.5, (H, W, 1)).astype(np.float32)
        img = np.clip(img + grain, 0, 255).astype(np.uint8)
        frame = Image.fromarray(img, "RGB")
        # 천천히 다가가는 카메라
        z = lerp(1.0, 1.05, ease_in_out(p))
        cw, ch = W / z, H / z
        x0, y0 = (W - cw) / 2 + (sun_x - W / 2) * (1 - 1 / z) * 0.5, (H - ch) / 2
        frame = frame.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
        return frame.convert("RGBA")

    def frame(t, i):
        img = scene(t)
        a = ease_out_cubic(progress(t, 0.2, 0.9))
        paste(img, t_small, (W / 2, 190 + 14 * (1 - a)), a)
        a = ease_out_cubic(progress(t, 0.4, 1.0))
        paste(img, t_date, (W / 2, 280 + 18 * (1 - a)), a)
        y = 365
        if t_sub:
            a = ease_out_cubic(progress(t, 0.6, 0.9))
            paste(img, t_sub, (W / 2, y + 12 * (1 - a)), a)
            y += 70
        paste(img, line, (W / 2, y + 10), ease_out_cubic(progress(t, 0.8, 0.8)))
        a = ease_out_cubic(progress(t, 1.1, 1.3))
        paste(img, t_msg, (W / 2, y + 60 + t_msg.height / 2 + 16 * (1 - a)), a)
        a = ease_out_cubic(progress(t, 1.8, 1.0))
        paste(img, t_loc, (W / 2, 1800), a * 0.9)
        if t_brand:
            paste(img, t_brand, (W / 2, 1740), a)
        fo = progress(t, NFRAMES / FPS - 0.4, 0.4)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (0, 0, 0, 255)), fo * 0.6)
        return img

    snd = None
    if audio:
        notes = [(0.2, 57, 3.5, 0.35), (0.2, 64, 3.5, 0.3), (1.2, 69, 3.0, 0.3), (2.2, 71, 3.0, 0.28),
                 (3.0, 76, 2.5, 0.25)]
        snd = finish_audio(ocean_noise(seed=seed + 3) * 0.8 + melody(notes, decay=0.6) * 0.45, vol=0.5)
    render_video(out, frame, snd)
    return {"scene": "photo-real gwangan", "message": msg, "subtitle": sub}
