"""장면 미리보기: 영상을 인코딩하지 않고 몇 개 시점의 프레임을 한 장의 PNG 로 이어 붙인다.

    python -m morning_video.preview scene_busan3 --date 2026-11-20 --times 0.5,2,5 --out preview.png
    python -m morning_video.preview scene_anniversary3 --date 2026-11-11   # 추모일 등 경우별 확인
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib
import time
from pathlib import Path

from PIL import Image

from . import calendar_kr as cal


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("module", help="예: scene_busan3")
    ap.add_argument("--date", help="YYYY-MM-DD (기본: 오늘 KST)")
    ap.add_argument("--times", default="0.5,2.0,5.0", help="미리볼 시점(초), 쉼표 구분")
    ap.add_argument("--out", default="preview.png")
    ap.add_argument("--width", type=int, default=540, help="한 장면의 미리보기 폭")
    args = ap.parse_args(argv)

    mod = importlib.import_module(f"morning_video.{args.module}")
    d = dt.date.fromisoformat(args.date) if args.date else cal.today_kst()
    times = [float(x) for x in args.times.split(",")]
    shots = []

    def capture(path, frame_fn, audio=None):
        for t in times:
            t0 = time.time()
            im = frame_fn(t, int(t * 30)).convert("RGB")
            print(f"  t={t:.2f}s  {time.time() - t0:.2f}s/frame")
            shots.append(im.resize((args.width, int(args.width * im.height / im.width)), Image.LANCZOS))

    mod.render_video = capture  # 인코딩 대신 프레임만 수집
    meta = mod.build(d, Path("/dev/null"), audio=False)
    gap = 16
    sheet = Image.new("RGB", (len(shots) * (args.width + gap) - gap, shots[0].height), "white")
    for k, im in enumerate(shots):
        sheet.paste(im, (k * (args.width + gap), 0))
    sheet.save(args.out)
    print(f"저장: {args.out}  {meta}")


if __name__ == "__main__":
    main()
