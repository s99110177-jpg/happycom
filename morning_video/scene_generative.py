"""제너러티브 아트 영상 (algorithmic-art 스킬): '윤슬(Tidal Light)' p5.js 알고리즘.

generative/render.html 을 헤드리스 Chromium(Playwright)으로 열어 프레임을 캡처한 뒤,
날짜·메시지 자막과 배경음을 얹어 9:16 영상으로 만든다. 씨앗(seed)은 날짜(YYYYMMDD)라 날마다 다른 바다가 생긴다.
필요: node, generative/ 에서 `npm install`, playwright(node 패키지).
"""
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from . import calendar_kr as cal
from .messages import morning_message
from .render_common import (FPS, H, NFRAMES, REPO, W, ease_out_cubic, finish_audio, font, melody, ocean_noise, paste,
                            progress, render_video, text_layer)

GEN = REPO / "generative"


def _capture(seed: int, n: int, out_dir: Path):
    if not (GEN / "node_modules" / "p5").exists():
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=GEN, check=True)
    subprocess.run(["node", str(GEN / "capture.js"), str(seed), str(n), str(out_dir)], cwd=GEN, check=True)


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    seed = int(d.strftime("%Y%m%d"))
    tmp = Path(tempfile.mkdtemp(prefix="tidal_"))
    try:
        _capture(seed, NFRAMES, tmp)
        frames = sorted(tmp.glob("*.png"))
        msg = morning_message(d)
        sh = (0, 3, 14, (0, 0, 10, 200))
        t_kicker = text_layer("T I D A L   L I G H T   ·   윤 슬", font("semibold", 30), (255, 214, 180), shadow=sh)
        t_date = text_layer(f"{d.month}월 {d.day}일 {cal.WEEKDAYS[d.weekday()]}", font("serif", 92), (255, 255, 255), shadow=sh)
        t_year = text_layer(f"{d.year}", font("regular", 40), (230, 220, 240), shadow=sh)
        t_msg = text_layer(msg, font("serif", 62), (255, 255, 255), line_gap=0.5, shadow=(0, 3, 18, (0, 0, 10, 220)))
        t_seed = text_layer(f"오늘의 바다는 오늘만 생깁니다 · seed {seed}", font("regular", 28), (200, 190, 220), shadow=sh)
        t_brand = text_layer(brand, font("semibold", 36), (255, 255, 255), shadow=sh) if brand else None

        def frame(t, i):
            img = Image.open(frames[min(i, len(frames) - 1)]).convert("RGBA")
            a = ease_out_cubic(progress(t, 0.2, 1.0))
            paste(img, t_kicker, (W / 2, 150), a)
            paste(img, t_year, (W / 2, 215), a)
            a = ease_out_cubic(progress(t, 0.4, 1.0))
            paste(img, t_date, (W / 2, 300 + 16 * (1 - a)), a)
            a = ease_out_cubic(progress(t, 1.1, 1.4))
            paste(img, t_msg, (W / 2, 520 + 16 * (1 - a)), a)
            a = ease_out_cubic(progress(t, 2.0, 1.0))
            paste(img, t_seed, (W / 2, H - 90), a)
            if t_brand:
                paste(img, t_brand, (W / 2, H - 150), a)
            fo = progress(t, NFRAMES / FPS - 0.4, 0.4)
            if fo > 0:
                img = Image.blend(img, Image.new("RGBA", (W, H), (0, 0, 0, 255)), fo * 0.6)
            return img

        snd = None
        if audio:
            notes = [(0.1, 50, 4.5, 0.35), (0.1, 57, 4.5, 0.3), (0.8, 69, 2.5, 0.25), (1.6, 74, 2.5, 0.22),
                     (2.4, 76, 2.5, 0.22), (3.2, 81, 2.2, 0.2), (3.9, 79, 1.6, 0.18)]
            snd = finish_audio(ocean_noise(seed=seed % 10000) * 0.6 + melody(notes, decay=0.5, harmonics=((1, 1), (2, .15))),
                               vol=0.5)
        render_video(out, frame, snd)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {"scene": "generative tidal-light", "seed": seed, "message": msg}
