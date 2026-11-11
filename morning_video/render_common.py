"""렌더링 공통 도구: 폰트, 텍스트 레이어, 이징, ffmpeg 인코딩, 효과음 합성."""
from __future__ import annotations

import math
import os
import subprocess
import tempfile
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920          # 9:16
FPS = 30
DURATION = 5.5             # 6초 이내
NFRAMES = int(FPS * DURATION)

REPO = Path(__file__).resolve().parent.parent
FONT_DIRS = [REPO / "fonts", Path("/usr/share/fonts"), Path.home() / ".fonts",
             Path("/usr/local/share/fonts"), Path("/Library/Fonts"), Path("C:/Windows/Fonts")]

FONT_CANDIDATES = {
    "bold": ["NanumSquareEB.ttf", "NanumSquare_acEB.ttf", "NanumGothicExtraBold.ttf", "NotoSansCJK-Black.ttc", "NotoSansCJK-Bold.ttc"],
    "semibold": ["NanumSquareB.ttf", "NanumSquare_acB.ttf", "NanumGothicBold.ttf", "NotoSansCJK-Bold.ttc"],
    "regular": ["NanumSquareR.ttf", "NanumSquare_acR.ttf", "NanumGothic.ttf", "NotoSansCJK-Regular.ttc"],
    "round": ["NanumSquareRoundEB.ttf", "NanumSquareRoundB.ttf", "NanumSquareEB.ttf", "NotoSansCJK-Bold.ttc"],
    "serif": ["NanumMyeongjoExtraBold.ttf", "NanumMyeongjoBold.ttf", "NotoSerifCJK-Bold.ttc", "NanumSquareB.ttf"],
    "pen": ["NanumPen.ttf", "NanumBarunpenB.ttf", "NanumSquareRoundB.ttf", "NotoSansCJK-Medium.ttc"],
    "emoji": ["NotoColorEmoji.ttf"],
}


@lru_cache(maxsize=None)
def _find_file(name: str) -> str | None:
    for base in FONT_DIRS:
        if not base.exists():
            continue
        direct = base / name
        if direct.exists():
            return str(direct)
        for root, _dirs, files in os.walk(base):
            if name in files:
                return os.path.join(root, name)
    return None


@lru_cache(maxsize=None)
def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for name in FONT_CANDIDATES[kind]:
        path = _find_file(name)
        if path:
            idx = 1 if path.endswith(".ttc") else 0  # Noto CJK ttc: 1 = KR
            try:
                return ImageFont.truetype(path, size, index=idx if "Noto" in path and "CJK" in path else 0)
            except OSError:
                continue
    raise FileNotFoundError(
        f"한글 폰트({kind})를 찾을 수 없습니다. 'sudo apt install fonts-nanum fonts-nanum-extra fonts-noto-color-emoji' "
        "로 설치하거나 fonts/ 폴더에 폰트 파일을 넣어 주세요.")


# ---------------------------------------------------------------- 이징/수학

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.70158):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def progress(t, start, dur):
    return clamp((t - start) / dur)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


def hex2rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- 그리기

def vertical_gradient(w, h, stops):
    """stops: [(pos 0..1, (r,g,b)), ...] -> RGB Image"""
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, 3), dtype=np.float32)
    pos = [s[0] for s in stops]
    cols = np.array([s[1] for s in stops], dtype=np.float32)
    for c in range(3):
        out[:, c] = np.interp(ys, pos, cols[:, c])
    arr = np.repeat(out[:, None, :], w, axis=1)
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB")


def radial_glow(size, color, inner_alpha=255, power=2.0):
    """원형 글로우 RGBA"""
    r = size / 2
    y, x = np.mgrid[0:size, 0:size]
    d = np.sqrt((x - r + 0.5) ** 2 + (y - r + 0.5) ** 2) / r
    a = (1 - np.clip(d, 0, 1)) ** power * inner_alpha
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def with_alpha(img: Image.Image, k: float) -> Image.Image:
    if k >= 0.999:
        return img
    img = img.copy()
    a = img.getchannel("A").point(lambda v: int(v * max(0.0, k)))
    img.putalpha(a)
    return img


def paste(base: Image.Image, layer: Image.Image, xy, alpha=1.0, anchor="mm"):
    """RGBA layer 를 base(RGBA) 위에 합성. anchor: mm(중앙) / lt(좌상단)"""
    if alpha <= 0.003:
        return
    layer = with_alpha(layer, alpha)
    x, y = xy
    if anchor == "mm":
        x -= layer.width / 2
        y -= layer.height / 2
    elif anchor == "mt":
        x -= layer.width / 2
    base.alpha_composite(layer, (int(round(x)), int(round(y))))


def text_layer(text: str, fnt: ImageFont.FreeTypeFont, fill=(255, 255, 255), *,
               line_gap=0.28, stroke=0, stroke_fill=(0, 0, 0), shadow=None,
               align="center") -> Image.Image:
    """여러 줄 텍스트를 RGBA 레이어로. shadow=(dx, dy, blur, (r,g,b,a))"""
    lines = text.split("\n")
    asc, desc = fnt.getmetrics()
    lh = asc + desc
    gap = int(lh * line_gap)
    widths = [fnt.getbbox(l, stroke_width=stroke)[2] if l else 0 for l in lines]
    tw = max(widths) + stroke * 2
    th = lh * len(lines) + gap * (len(lines) - 1) + stroke * 2
    pad = 0 if not shadow else shadow[2] * 3 + max(abs(shadow[0]), abs(shadow[1]))
    img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))

    def draw_lines(d, col, off=(0, 0), sw=stroke, sf=stroke_fill):
        y = pad + stroke + off[1]
        for l, w in zip(lines, widths):
            if align == "center":
                x = pad + (tw - w) / 2 + off[0]
            elif align == "right":
                x = pad + tw - w + off[0]
            else:
                x = pad + stroke + off[0]
            d.text((x, y), l, font=fnt, fill=col, stroke_width=sw, stroke_fill=sf)
            y += lh + gap

    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_lines(ImageDraw.Draw(sh), shadow[3], (shadow[0], shadow[1]), stroke, shadow[3])
        if shadow[2]:
            sh = sh.filter(ImageFilter.GaussianBlur(shadow[2]))
        img.alpha_composite(sh)
    draw_lines(ImageDraw.Draw(img), fill)
    return img


def fit_font(text: str, kind: str, max_w: int, start: int, min_size=30) -> ImageFont.FreeTypeFont:
    size = start
    while size > min_size:
        f = font(kind, size)
        if max(f.getbbox(l)[2] for l in text.split("\n") if l) <= max_w:
            return f
        size -= 4
    return font(kind, min_size)


@lru_cache(maxsize=64)
def emoji_image(ch: str, size: int) -> Image.Image:
    f = font("emoji", 109)  # 컬러 비트맵 폰트는 109px 고정
    im = Image.new("RGBA", (300, 200), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    bb = im.getbbox()
    if not bb:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    im = im.crop(bb)
    scale = size / max(im.size)
    return im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)


def rounded_rect_layer(w, h, r, fill, outline=None, width=0) -> Image.Image:
    s = 2
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, w * s - 1, h * s - 1), r * s, fill=fill,
                                          outline=outline, width=width * s)
    return img.resize((w, h), Image.LANCZOS)


def soft_shadow(layer: Image.Image, blur=18, color=(0, 0, 0, 90), spread=40) -> Image.Image:
    sh = Image.new("RGBA", (layer.width + spread * 2, layer.height + spread * 2), (0, 0, 0, 0))
    mask = layer.getchannel("A").point(lambda v: 255 if v > 10 else 0)
    col = Image.new("RGBA", layer.size, color)
    sh.paste(col, (spread, spread), mask)
    return sh.filter(ImageFilter.GaussianBlur(blur))


# ---------------------------------------------------------------- 인코딩

class VideoWriter:
    def __init__(self, path: Path, audio: np.ndarray | None = None, sr=44100):
        self.path = Path(path)
        self.tmp_audio = None
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        if audio is not None:
            fd, self.tmp_audio = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            write_wav(self.tmp_audio, audio, sr)
            cmd += ["-i", self.tmp_audio, "-c:a", "aac", "-b:a", "160k", "-shortest"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                "-profile:v", "high", "-movflags", "+faststart", "-t", f"{DURATION:.2f}", str(self.path)]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, frame: Image.Image):
        self.proc.stdin.write(frame.convert("RGB").tobytes())

    def close(self):
        self.proc.stdin.close()
        rc = self.proc.wait()
        if self.tmp_audio:
            os.unlink(self.tmp_audio)
        if rc != 0:
            raise RuntimeError(f"ffmpeg 인코딩 실패: {self.path}")


def render_video(path: Path, frame_fn, audio=None):
    vw = VideoWriter(path, audio)
    try:
        for i in range(NFRAMES):
            vw.write(frame_fn(i / FPS, i))
    finally:
        vw.close()


# ---------------------------------------------------------------- 오디오

SR = 44100


def write_wav(path, samples: np.ndarray, sr=SR):
    s = np.clip(samples, -1, 1)
    if s.ndim == 1:
        s = np.stack([s, s], axis=1)
    data = (s * 32767).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data)


def _note(freq, dur, sr=SR, decay=3.0, harmonics=((1, 1.0), (2, 0.35), (3, 0.12))):
    t = np.arange(int(dur * sr)) / sr
    env = np.exp(-decay * t) * np.clip(t / 0.008, 0, 1)
    sig = sum(a * np.sin(2 * np.pi * freq * k * t) for k, a in harmonics)
    return sig * env


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def melody(notes, total=DURATION, sr=SR, **kw):
    """notes: [(start_sec, midi, dur, vel)]"""
    out = np.zeros(int(total * sr) + sr)
    for st, n, d, v in notes:
        s = _note(midi(n), d, sr, **kw) * v
        i = int(st * sr)
        out[i:i + len(s)] += s[: len(out) - i]
    return out[: int(total * sr)]


def ocean_noise(total=DURATION, sr=SR, seed=1):
    rng = np.random.default_rng(seed)
    n = int(total * sr)
    white = rng.standard_normal(n)
    # 간단한 저역통과(파도 소리)
    k = 400
    kernel = np.hanning(k)
    kernel /= kernel.sum()
    brown = np.convolve(white, kernel, mode="same")
    t = np.arange(n) / sr
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 4.2 - 1.2) ** 2
    return brown * swell / (np.abs(brown).max() + 1e-9)


def finish_audio(sig, vol=0.6, fade_in=0.15, fade_out=0.8, sr=SR):
    n = len(sig)
    env = np.ones(n)
    fi, fo = int(fade_in * sr), int(fade_out * sr)
    env[:fi] = np.linspace(0, 1, fi)
    env[n - fo:] = np.linspace(1, 0, fo)
    peak = np.abs(sig).max() + 1e-9
    return sig / peak * vol * env
