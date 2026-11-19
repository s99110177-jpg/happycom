"""손그림 질감 도구: 종이 결, 수채화 번짐, 분필 질감, 스티커 테두리, 글씨 써지는 효과."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .render_common import H, W


def fbm(h, w, base, octaves, rng, gain=0.55, aspect=1.0):
    out = np.zeros((h, w), dtype=np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gx = max(2, int(w / (base * aspect) * 2 ** o))
        gy = max(2, int(h / base * 2 ** o))
        g = (rng.random((gy, gx)) * 255).astype(np.uint8)
        out += amp * np.asarray(Image.fromarray(g).resize((w, h), Image.BICUBIC), dtype=np.float32) / 255
        tot += amp
        amp *= gain
    return out / tot


def paper(color, seed, strength=10, size=(W, H)):
    """종이 결(미세한 섬유 + 큰 얼룩)."""
    w, h = size
    rng = np.random.default_rng(seed)
    fine = rng.normal(0, 1, (h, w)).astype(np.float32)
    fine = np.asarray(Image.fromarray(np.clip(fine * 40 + 128, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)),
                      dtype=np.float32) - 128
    blot = (fbm(h // 4, w // 4, 60, 4, rng) - 0.5)
    blot = np.asarray(Image.fromarray(((blot + 0.5) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), dtype=np.float32) / 255 - 0.5
    arr = np.array(color, dtype=np.float32)[None, None, :] + (fine * strength / 40 + blot * strength * 1.5)[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


def watercolor(mask: Image.Image, color, seed, opacity=0.85, edge=0.35, bleed=10, size=(W, H)):
    """도형 마스크(L)를 수채화 물감 번짐으로: 울퉁불퉁한 가장자리 + 가장자리 진하게 + 농담 얼룩."""
    w, h = size
    rng = np.random.default_rng(seed)
    m = np.asarray(mask.filter(ImageFilter.GaussianBlur(bleed)), dtype=np.float32) / 255
    noise = fbm(h // 2, w // 2, 40, 5, rng)
    noise = np.asarray(Image.fromarray((noise * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), dtype=np.float32) / 255
    a = np.clip((m - 0.5 + (noise - 0.5) * 0.6) * 6 + 0.5, 0, 1)        # 번진 가장자리
    a_img = Image.fromarray((a * 255).astype(np.uint8))
    inner = np.asarray(a_img.filter(ImageFilter.GaussianBlur(6)), dtype=np.float32) / 255
    rim = np.clip(a - inner, 0, 1) * 2.5                                  # 마르며 진해지는 테두리
    tone = 0.75 + 0.5 * fbm(h // 4, w // 4, 30, 3, rng)
    tone = np.asarray(Image.fromarray((np.clip(tone / 1.25, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC),
                      dtype=np.float32) / 255 * 1.25
    alpha = np.clip(a * opacity * tone + rim * edge, 0, 1)
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = color
    out[..., 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def multiply(base: Image.Image, layer: Image.Image) -> Image.Image:
    """수채화처럼 물감을 겹쳐 칠하기(곱하기 합성)."""
    b = np.asarray(base, dtype=np.float32) / 255
    l = np.asarray(layer, dtype=np.float32) / 255
    a = l[..., 3:4]
    mixed = b[..., :3] * (1 - a + a * l[..., :3])
    out = np.concatenate([mixed, b[..., 3:4]], axis=2)
    return Image.fromarray((out * 255).clip(0, 255).astype(np.uint8), "RGBA")


def chalkify(layer: Image.Image, seed, density=0.78):
    """글자/그림 레이어를 분필 질감으로(군데군데 비고 거친 입자)."""
    rng = np.random.default_rng(seed)
    a = np.asarray(layer.getchannel("A"), dtype=np.float32) / 255
    grain = rng.random(a.shape).astype(np.float32)
    streak = np.asarray(Image.fromarray((rng.random((a.shape[0] // 3 + 1, a.shape[1] // 12 + 1)) * 255).astype(np.uint8))
                        .resize((a.shape[1], a.shape[0]), Image.BILINEAR), dtype=np.float32) / 255
    keep = (grain * 0.6 + streak * 0.4) < density
    out = layer.copy()
    out.putalpha(Image.fromarray((a * keep * 235).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5)))
    return out


def sticker(img: Image.Image, border=10, shadow=True):
    """이모지/그림에 흰 스티커 테두리와 살짝 그림자."""
    pad = border + 14
    canvas = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    canvas.alpha_composite(img, (pad, pad))
    a = canvas.getchannel("A").point(lambda v: 255 if v > 30 else 0)
    grown = a.filter(ImageFilter.MaxFilter(border * 2 + 1)).filter(ImageFilter.GaussianBlur(1))
    out = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        sh.putalpha(grown.point(lambda v: v * 70 // 255))
        sh = sh.filter(ImageFilter.GaussianBlur(5))
        out.alpha_composite(sh, (3, 6))
    white = Image.new("RGBA", canvas.size, (255, 255, 255, 255))
    white.putalpha(grown)
    out.alpha_composite(white)
    out.alpha_composite(canvas)
    return out


def wipe(layer: Image.Image, frac: float, soft=30) -> Image.Image:
    """왼쪽에서 오른쪽으로 써지듯 드러내기 (여러 줄이면 줄마다 차례로)."""
    if frac >= 1:
        return layer
    if frac <= 0:
        return Image.new("RGBA", layer.size, (0, 0, 0, 0))
    a = np.asarray(layer.getchannel("A"), dtype=np.float32)
    rows = np.nonzero(a.max(axis=1) > 0)[0]
    if len(rows) == 0:
        return layer
    # 줄 구간 찾기
    lines, start = [], rows[0]
    for r0, r1 in zip(rows[:-1], rows[1:]):
        if r1 - r0 > 4:
            lines.append((start, r0 + 1))
            start = r1
    lines.append((start, rows[-1] + 1))
    total = len(lines)
    mask = np.zeros_like(a)
    xs = np.arange(a.shape[1], dtype=np.float32)
    for k, (y0, y1) in enumerate(lines):
        f = np.clip(frac * total - k, 0, 1)
        cols = np.nonzero(a[y0:y1].max(axis=0) > 0)[0]
        if f <= 0 or len(cols) == 0:
            continue
        edge = cols[0] + (cols[-1] - cols[0] + soft) * f
        mask[y0:y1] = np.clip((edge - xs) / soft, 0, 1)[None, :]
    out = layer.copy()
    out.putalpha(Image.fromarray((a * mask).astype(np.uint8)))
    return out


def scribble_ellipse(size, color, width=6, seed=0, turns=1.15):
    """손으로 그린 동그라미 (끝이 살짝 겹침). 반환: 점 목록 함수용 이미지 생성기."""
    rng = np.random.default_rng(seed)
    w, h = size
    pts = []
    n = 120
    for i in range(int(n * turns)):
        t = 2 * np.pi * i / n - 0.6
        r = 1 + 0.03 * np.sin(t * 3 + rng.random()) + 0.04 * (i / n)
        pts.append((w / 2 + (w / 2 - width) * r * np.cos(t), h / 2 + (h / 2 - width) * r * np.sin(t) * 0.96))

    def draw(frac):
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        k = max(2, int(len(pts) * frac))
        ImageDraw.Draw(img).line(pts[:k], fill=color, width=width, joint="curve")
        return img
    return draw
