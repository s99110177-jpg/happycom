"""영상 1: 부산 배경 + 아침 메시지 + 년월일 요일.

장면은 날짜에 따라 번갈아 사용된다.
  - gwangan : 광안대교 너머 해돋이
  - gamcheon: 감천문화마을의 알록달록한 아침
assets/busan/ 폴더에 직접 찍은 부산 사진(jpg/png)을 넣으면 사진 장면이 우선 사용된다.
"""
from __future__ import annotations

import datetime as dt
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from . import calendar_kr as cal
from .messages import morning_message
from .render_common import (FPS, H, NFRAMES, REPO, W, clamp, ease_in_out, ease_out_cubic, finish_audio, font,
                            lerp, melody, ocean_noise, paste, progress, radial_glow, render_video,
                            rounded_rect_layer, text_layer, vertical_gradient)

S = 2  # 정적 레이어 슈퍼샘플링 배율
PHOTO_DIR = REPO / "assets" / "busan"


def _ss(img_size=(W, H)):
    return Image.new("RGBA", (img_size[0] * S, img_size[1] * S), (0, 0, 0, 0))


def _down(img):
    return img.resize((img.width // S, img.height // S), Image.LANCZOS)


# ============================================================== 광안대교

HORIZON = 1185


def _gwangan_static(rng: random.Random):
    sky = vertical_gradient(W, H, [
        (0.00, (24, 34, 86)), (0.22, (70, 62, 128)), (0.42, (170, 98, 140)),
        (0.55, (245, 150, 120)), (HORIZON / H, (255, 214, 160)), (1.0, (255, 214, 160))]).convert("RGBA")

    # 원경: 왼쪽 마린시티 빌딩숲, 오른쪽 이기대 능선
    far = _ss()
    d = ImageDraw.Draw(far)
    col_far = (120, 88, 140, 255)
    x = -10
    while x < 330:
        bw = rng.randint(26, 52)
        bh = rng.randint(120, 330) if x < 220 else rng.randint(60, 170)
        top = HORIZON - bh
        d.rectangle((x * S, top * S, (x + bw) * S, HORIZON * S), fill=col_far)
        if rng.random() < 0.5:  # 둥근/뾰족 지붕
            d.polygon([(x * S, top * S), ((x + bw / 2) * S, (top - rng.randint(10, 30)) * S), ((x + bw) * S, top * S)], fill=col_far)
        x += bw + rng.randint(-6, 4)
    # 엘시티 3개 타워
    for bx, bh in ((70, 470), (112, 430), (150, 400)):
        d.rounded_rectangle((bx * S, (HORIZON - bh) * S, (bx + 30) * S, HORIZON * S), 10 * S, fill=(105, 76, 128, 255))
    # 오른쪽 능선
    pts = [(700 * S, HORIZON * S)]
    for i in range(0, 41):
        px = 700 + i * 10
        py = HORIZON - 38 - 30 * math.sin(i / 40 * math.pi) - 12 * math.sin(i / 5.0)
        pts.append((px * S, py * S))
    pts.append((1100 * S, HORIZON * S))
    d.polygon(pts, fill=(128, 90, 138, 255))
    far = _down(far.filter(ImageFilter.GaussianBlur(1.2 * S)))

    # 바다
    sea = vertical_gradient(W, H - HORIZON, [(0, (250, 190, 150)), (0.12, (196, 132, 140)),
                                            (0.45, (72, 70, 120)), (1, (20, 26, 60))]).convert("RGBA")
    sea_full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sea_full.paste(sea, (0, HORIZON))
    sd = ImageDraw.Draw(sea_full)
    for _ in range(90):  # 잔물결
        y = rng.uniform(HORIZON + 8, H)
        k = (y - HORIZON) / (H - HORIZON)
        x = rng.uniform(-50, W)
        L = lerp(20, 120, k)
        sd.line((x, y, x + L, y), fill=(255, 220, 200, int(lerp(22, 12, k))), width=max(1, int(lerp(1, 3, k))))

    # 광안대교 실루엣
    br = _ss()
    d = ImageDraw.Draw(br)
    bc = (30, 28, 62, 255)
    deck = 1112
    water = 1214
    towers = (300, 780)
    top = 862
    # 교각
    for px in list(range(-40, W + 60, 92)):
        d.rectangle(((px - 6) * S, deck * S, (px + 6) * S, water * S), fill=bc)
    # 상판(복층)
    d.rectangle((0, (deck - 10) * S, W * S, (deck + 8) * S), fill=bc)
    d.rectangle((0, (deck + 16) * S, W * S, (deck + 28) * S), fill=bc)
    for px in range(0, W, 18):
        d.line((px * S, (deck + 8) * S, (px + 9) * S, (deck + 16) * S), fill=bc, width=2 * S)

    def cable(x0, y0, x1, y1, sag):
        pts = []
        for i in range(61):
            t = i / 60
            xx = lerp(x0, x1, t)
            yy = lerp(y0, y1, t) + sag * 4 * t * (1 - t)
            pts.append((xx, yy))
        return pts

    spans = [cable(-120, deck - 8, towers[0], top + 6, 34),
             cable(towers[0], top + 6, towers[1], top + 6, 228),
             cable(towers[1], top + 6, W + 120, deck - 8, 34)]
    for pts in spans:
        d.line([(x * S, y * S) for x, y in pts], fill=bc, width=4 * S)
        for x, y in pts[1:-1:2]:
            if y < deck - 14:
                d.line((x * S, y * S, x * S, (deck - 10) * S), fill=(30, 28, 62, 200), width=max(1, S))
    # 주탑 (H형)
    for tx in towers:
        for off in (-24, 18):
            d.rectangle(((tx + off) * S, top * S, (tx + off + 8) * S, water * S), fill=bc)
        for by in (top + 18, top + 120, deck - 40):
            d.rectangle(((tx - 24) * S, by * S, (tx + 26) * S, (by + 10) * S), fill=bc)
    br = _down(br)
    # 다리 조명(희미한 점)
    bd = ImageDraw.Draw(br)
    for px in range(10, W, 36):
        bd.ellipse((px - 2, deck - 2, px + 2, deck + 2), fill=(255, 230, 170, 200))
    return sky, far, sea_full, br


class _Gull:
    def __init__(self, rng, y_range, scale_range, speed_range, start_x=None):
        self.y = rng.uniform(*y_range)
        self.s = rng.uniform(*scale_range)
        self.v = rng.uniform(*speed_range)
        self.x0 = start_x if start_x is not None else rng.uniform(W * 0.2, W * 1.2)
        self.ph = rng.uniform(0, 6.28)
        self.f = rng.uniform(2.2, 3.2)

    def draw(self, d: ImageDraw.ImageDraw, t, color=(40, 36, 70, 230)):
        x = self.x0 - self.v * t
        y = self.y + 8 * math.sin(t * 1.3 + self.ph)
        flap = math.sin(t * self.f * 2 * math.pi + self.ph)
        s = self.s
        wy = -10 * flap * s
        pts_l = [(x - 26 * s, y + wy), (x - 12 * s, y - 6 * s + wy * 0.3), (x, y)]
        pts_r = [(x, y), (x + 12 * s, y - 6 * s + wy * 0.3), (x + 26 * s, y + wy)]
        w = max(2, int(3.2 * s))
        d.line(pts_l, fill=color, width=w, joint="curve")
        d.line(pts_r, fill=color, width=w, joint="curve")


def _gwangan_frames(seed: int):
    rng = random.Random(seed)
    sky, far, sea, bridge = _gwangan_static(rng)
    sun_disc = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    ImageDraw.Draw(sun_disc).ellipse((10, 10, 170, 170), fill=(255, 244, 214, 255))
    sun_disc = sun_disc.filter(ImageFilter.GaussianBlur(1.5))
    glow_big = radial_glow(1300, (255, 180, 110), 200, 2.2)
    glow_small = radial_glow(460, (255, 230, 180), 255, 1.6)
    sparkles = []
    for _ in range(200):
        k = rng.random() ** 1.6
        y = HORIZON + 6 + k * (H - HORIZON - 6)
        spread = lerp(30, 200, k)
        sparkles.append((rng.gauss(0, spread * 0.4), y, lerp(8, 46, k), rng.uniform(0, 6.28), rng.uniform(2, 5), k))
    gulls = [_Gull(rng, (960, 1040), (0.9, 1.3), (60, 110)) for _ in range(3)] + \
            [_Gull(rng, (330, 420), (0.6, 0.8), (40, 70)) for _ in range(2)]

    def scene(t):
        p = t / (NFRAMES / FPS)
        sun_x = 560
        sun_y = lerp(1250, 1035, ease_in_out(p * 1.05))
        img = sky.copy()
        # 해가 떠오를수록 하늘이 밝아짐
        paste(img, glow_big, (sun_x, sun_y), alpha=lerp(0.55, 1.0, p))
        paste(img, glow_small, (sun_x, sun_y), alpha=0.9)
        paste(img, sun_disc, (sun_x, sun_y))
        img.alpha_composite(far)
        img.alpha_composite(sea)
        # 윤슬
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        rise = clamp((1250 - sun_y) / 200)
        for dx, y, L, ph, sp, k in sparkles:
            a = (0.5 + 0.5 * math.sin(ph + t * sp)) ** 3
            a *= (0.35 + 0.65 * rise) * (1 - 0.7 * k)
            if a < 0.05:
                continue
            x = sun_x + dx + 6 * math.sin(t * 0.8 + ph)
            ld.line((x - L / 2, y, x + L / 2, y), fill=(255, 236, 196, int(255 * a)), width=max(2, int(2 + 3 * k)))
        img.alpha_composite(layer)
        img.alpha_composite(bridge)
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(fx)
        for g in gulls:
            g.draw(gd, t)
        img.alpha_composite(fx)
        return img

    return scene


# ============================================================== 감천문화마을

GAM_COLORS = [(255, 179, 186), (255, 223, 150), (167, 222, 205), (152, 196, 240), (255, 160, 122),
              (200, 180, 240), (255, 255, 240), (120, 200, 190), (255, 205, 120)]


def _gamcheon_static(rng: random.Random):
    sky = vertical_gradient(W, H, [(0, (92, 160, 226)), (0.35, (150, 200, 240)), (0.55, (255, 222, 190)),
                                   (1, (255, 222, 190))]).convert("RGBA")
    # 먼 바다와 항구
    back = _ss()
    d = ImageDraw.Draw(back)
    sea_y = 960
    d.rectangle((0, sea_y * S, W * S, 1100 * S), fill=(96, 150, 196, 255))
    for i in range(30):
        y = sea_y + 6 + i * 4.5
        d.line((rng.uniform(0, W) * S, y * S, rng.uniform(0, W) * S, y * S), fill=(170, 210, 236, 120), width=S)
    # 먼 산(영도/송도 능선)
    pts = [(0, (sea_y) * S)]
    for i in range(55):
        x = i * 20
        y = sea_y - 30 - 40 * math.sin(i / 54 * math.pi * 1.3 + 0.4) - 10 * math.sin(i / 3)
        pts.append((x * S, y * S))
    pts.append((W * S, sea_y * S))
    d.polygon(pts, fill=(124, 156, 190, 255))
    back = _down(back.filter(ImageFilter.GaussianBlur(S)))

    # 산비탈 마을
    vil = _ss()
    d = ImageDraw.Draw(vil)

    def hill_y(x):
        return 1010 + 0.48 * (W - x) * 0 + 230 * (1 - x / W) ** 1.6 * 0 + (x / W) * 140

    # 언덕 바탕
    hill = [(0, 1060 * S)] + [(x * S, (hill_y(x) - 60) * S) for x in range(0, W + 20, 20)] + [(W * S, H * S), (0, H * S)]
    d.polygon(hill, fill=(132, 160, 120, 255))
    # 계단식 집들 (뒤 -> 앞)
    rows = 14
    for r in range(rows):
        base = 1080 + r * 62
        scale = 0.75 + r * 0.06
        x = -rng.uniform(0, 60)
        while x < W + 40:
            bw = rng.uniform(60, 110) * scale
            bh = rng.uniform(50, 90) * scale
            y0 = base + (x / W) * 140 - bh - rng.uniform(0, 14)
            col = rng.choice(GAM_COLORS)
            shade = tuple(int(c * 0.82) for c in col)
            d.rectangle((x * S, y0 * S, (x + bw) * S, (base + (x / W) * 140 + 30) * S), fill=col + (255,))
            d.rectangle(((x + bw * 0.78) * S, y0 * S, (x + bw) * S, (base + (x / W) * 140 + 30) * S), fill=shade + (255,))
            # 지붕(평지붕/박공)
            if rng.random() < 0.35:
                roof = rng.choice([(70, 120, 170), (210, 90, 80), (90, 150, 120)])
                d.polygon([((x - 4) * S, y0 * S), ((x + bw / 2) * S, (y0 - 22 * scale) * S), ((x + bw + 4) * S, y0 * S)], fill=roof + (255,))
            else:
                d.rectangle(((x - 3) * S, (y0 - 6) * S, (x + bw + 3) * S, y0 * S), fill=(235, 235, 235, 255))
            # 창문
            for wx in range(int(bw // (26 * scale))):
                if rng.random() < 0.75:
                    cx = x + 10 * scale + wx * 26 * scale
                    cy = y0 + 16 * scale
                    d.rectangle((cx * S, cy * S, (cx + 12 * scale) * S, (cy + 16 * scale) * S), fill=(70, 96, 130, 255))
            x += bw + rng.uniform(-6, 6)
    vil = _down(vil)
    # 앞쪽을 살짝 어둡게(텍스트 가독성)
    shade_layer = vertical_gradient(W, H, [(0, (0, 0, 0)), (0.62, (0, 0, 0)), (1, (0, 0, 0))]).convert("RGBA")
    a = np.zeros((H, W), dtype=np.uint8)
    ys = np.linspace(0, 1, H)
    top = np.clip(1 - ys / 0.5, 0, 1) ** 1.5 * 120
    bottom = np.clip((ys - 0.7) / 0.3, 0, 1) * 150
    a[:] = (top + bottom)[:, None].astype(np.uint8)
    shade_layer.putalpha(Image.fromarray(a))
    return sky, back, vil, shade_layer


def _cloud(rng, w):
    h = int(w * 0.5)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    for _ in range(7):
        r = rng.uniform(0.12, 0.22) * w
        cx = rng.uniform(r, w - r)
        cy = h - r - rng.uniform(0, 0.12) * w
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    d.rectangle((0.15 * w, h - 0.12 * w, 0.85 * w, h), fill=255)
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    img.putalpha(mask.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.92)))
    return img


def _gamcheon_frames(seed: int):
    rng = random.Random(seed)
    sky, back, vil, shade = _gamcheon_static(rng)
    sun = radial_glow(700, (255, 240, 200), 230, 1.8)
    clouds = [(_cloud(rng, rng.randint(240, 420)), rng.uniform(-100, W), rng.uniform(820, 900), rng.uniform(12, 30)) for _ in range(4)]
    gulls = [_Gull(rng, (880, 1000), (0.9, 1.2), (70, 120)) for _ in range(3)]

    def scene(t):
        img = sky.copy()
        paste(img, sun, (820, 820 - 14 * t))
        for c, x0, y, v in clouds:
            paste(img, c, ((x0 + v * t) % (W + 500) - 250, y))
        img.alpha_composite(back)
        img.alpha_composite(vil)
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(fx)
        for g in gulls:
            g.draw(gd, t, (60, 70, 90, 220))
        img.alpha_composite(fx)
        img.alpha_composite(shade)
        return img

    return scene


# ============================================================== 사진 모드

def _photo_frames(path: Path):
    src = Image.open(path).convert("RGB")
    src = ImageOps.exif_transpose(src)
    big = ImageOps.fit(src, (int(W * 1.12), int(H * 1.12)), Image.LANCZOS).convert("RGBA")
    a = np.zeros((H, W), dtype=np.uint8)
    prof = np.concatenate([np.linspace(150, 0, int(H * 0.35)), np.zeros(H - int(H * 0.35) - int(H * 0.3)),
                           np.linspace(0, 170, int(H * 0.3))])
    a[:] = prof[:, None].astype(np.uint8)
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shade.putalpha(Image.fromarray(a))
    rng = random.Random(str(path))
    gulls = [_Gull(rng, (700, 1100), (0.8, 1.2), (60, 110)) for _ in range(3)]

    def scene(t):
        p = ease_in_out(t / (NFRAMES / FPS))
        z = lerp(1.0, 1.08, p)
        cw, ch = big.width / z, big.height / z
        x0 = (big.width - cw) / 2
        y0 = (big.height - ch) / 2
        img = big.resize((int(W * 1.12 * 1.0), int(H * 1.12)), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
        img = img.crop((int(W * 0.06), int(H * 0.06), int(W * 0.06) + W, int(H * 0.06) + H))
        img.alpha_composite(shade)
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(fx)
        for g in gulls:
            g.draw(gd, t, (250, 250, 250, 220))
        img.alpha_composite(fx)
        return img

    return scene


# ============================================================== 텍스트/조립

SCENE_LABEL = {"gwangan": "부산 · 광안대교의 아침", "gamcheon": "부산 · 감천문화마을의 아침"}


def build(d: dt.date, out: Path, scene_name: str | None = None, brand: str = "", audio=True):
    photos = sorted(p for p in PHOTO_DIR.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")) \
        if PHOTO_DIR.exists() else []
    seed = d.toordinal()
    if scene_name is None:
        scene_name = "photo" if photos else ("gwangan", "gamcheon")[d.toordinal() % 2]
    if scene_name == "photo" and photos:
        photo = photos[d.toordinal() % len(photos)]
        scene = _photo_frames(photo)
        label = "부산의 아침"
    elif scene_name == "gamcheon":
        scene = _gamcheon_frames(seed)
        label = SCENE_LABEL["gamcheon"]
    else:
        scene_name = "gwangan"
        scene = _gwangan_frames(seed)
        label = SCENE_LABEL["gwangan"]

    shadow = (0, 4, 10, (10, 10, 40, 170))
    t_good = text_layer("GOOD MORNING", font("semibold", 40), (255, 255, 255), shadow=shadow)
    t_date = text_layer(f"{d.year}년 {d.month}월 {d.day}일", font("bold", 76), (255, 255, 255), shadow=shadow)
    t_wd = text_layer(cal.WEEKDAYS[d.weekday()], font("bold", 128), (255, 236, 190), shadow=shadow)
    msg = morning_message(d)
    t_msg = text_layer(msg, font("serif", 70), (255, 255, 255), line_gap=0.42,
                       shadow=(0, 4, 14, (10, 10, 40, 200)))
    t_label = text_layer(label, font("semibold", 36), (255, 255, 255), shadow=(0, 2, 6, (0, 0, 0, 160)))
    pill = rounded_rect_layer(t_label.width + 60, 72, 36, (20, 22, 50, 150), (255, 255, 255, 120), 2)
    t_brand = text_layer(brand, font("bold", 40), (255, 255, 255), shadow=(0, 2, 6, (0, 0, 0, 160))) if brand else None
    line = rounded_rect_layer(120, 6, 3, (255, 255, 255, 200))

    msg_y = 680

    def frame(t, i):
        img = scene(t)
        # 상단 날짜
        a1 = ease_out_cubic(progress(t, 0.15, 0.7))
        paste(img, t_good, (W / 2, 170 + 20 * (1 - a1)), a1)
        a2 = ease_out_cubic(progress(t, 0.3, 0.8))
        paste(img, t_date, (W / 2, 262 + 30 * (1 - a2)), a2)
        a3 = ease_out_cubic(progress(t, 0.45, 0.8))
        paste(img, t_wd, (W / 2, 385 + 30 * (1 - a3)), a3)
        a4 = ease_out_cubic(progress(t, 0.8, 0.6))
        paste(img, line, (W / 2, 478), a4)
        # 메시지 (한 줄씩 등장하는 효과: 위에서 아래로 와이프)
        am = progress(t, 1.0, 1.4)
        if am > 0:
            reveal = ease_in_out(am)
            hh = int(t_msg.height * reveal) + 1
            part = t_msg.crop((0, 0, t_msg.width, min(t_msg.height, hh + 40)))
            # 와이프 경계를 부드럽게
            grad = np.ones((part.height,), dtype=np.float32)
            edge = 40
            if hh < t_msg.height:
                grad[max(0, hh - edge):] = np.linspace(1, 0, part.height - max(0, hh - edge))
            alpha = np.array(part.getchannel("A"), dtype=np.float32) * grad[:, None]
            part.putalpha(Image.fromarray(alpha.astype(np.uint8)))
            img.alpha_composite(part, (int(W / 2 - t_msg.width / 2), int(msg_y - t_msg.height / 2 + 12 * (1 - reveal))))
        # 하단 장소 라벨
        a5 = ease_out_cubic(progress(t, 1.6, 0.8))
        by = 1740 if not t_brand else 1700
        paste(img, pill, (W / 2, by + 20 * (1 - a5)), a5)
        paste(img, t_label, (W / 2, by + 20 * (1 - a5)), a5)
        if t_brand:
            paste(img, t_brand, (W / 2, 1810), a5)
        # 마지막 0.4초 페이드 아웃
        fo = progress(t, (NFRAMES / FPS) - 0.35, 0.35)
        if fo > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), fo * 0.5)
        return img

    snd = None
    if audio:
        notes = [(0.3, 72, 2.5, 0.5), (0.9, 76, 2.5, 0.45), (1.5, 79, 2.5, 0.4), (2.3, 84, 2.8, 0.38),
                 (3.2, 79, 2.2, 0.3), (3.8, 81, 2.0, 0.3)]
        snd = finish_audio(ocean_noise(seed=seed) * 0.55 + melody(notes, decay=1.4) * 0.5, vol=0.5)
    render_video(out, frame, snd)
    return {"scene": scene_name, "message": msg}
