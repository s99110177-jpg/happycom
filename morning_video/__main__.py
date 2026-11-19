"""사용법:
    python -m morning_video                    # 오늘(KST) 영상 3개 생성 -> output/YYYY-MM-DD/
    python -m morning_video --date 2026-12-25
    python -m morning_video --style c          # 스타일 지정 (auto = 날마다 순환)
    python -m morning_video --list-styles
    python -m morning_video --only photo --only anim
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time
from pathlib import Path

from . import calendar_kr as cal
from .render_common import REPO
from .styles import EXTRAS, STYLES, auto_style, module

JOBS = ["busan", "anniversary", "character"]


def render_motion(d, out_dir: Path) -> dict:
    """Remotion 모션그래픽 3종: 데이터 내보내기 → node render.mjs."""
    import subprocess
    from .export_remotion import export
    rdir = REPO / "remotion"
    if not (rdir / "node_modules").exists():
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=rdir, check=True)
    data = export(d)
    subprocess.run(["node", "render.mjs", str(out_dir)], cwd=rdir, check=True)
    return {"anniversary": data["anniversary"]["name"], "message": data["message"]}


NUM = {"busan": 1, "anniversary": 2, "character": 3}


def main(argv=None):
    ap = argparse.ArgumentParser(description="매일 아침 9:16 영상 3종 생성")
    ap.add_argument("--date", help="YYYY-MM-DD (기본: 오늘, 한국시간)")
    ap.add_argument("--out", default=str(REPO / "output"), help="출력 폴더")
    ap.add_argument("--only", choices=JOBS + list(EXTRAS), action="append",
                    help="특정 영상만 생성 (여러 번 지정 가능). " +
                         ", ".join(f"{k}={v[1]}" for k, v in EXTRAS.items()))
    ap.add_argument("--scene", choices=["gwangan", "gamcheon", "photo"], help="스타일 A 부산 장면 강제 지정")
    ap.add_argument("--style", choices=list(STYLES) + ["auto"], default="a",
                    help="; ".join(f"{k}: {s.description}" for k, s in STYLES.items()) + "; auto: 날마다 순환")
    ap.add_argument("--list-styles", action="store_true", help="등록된 스타일 목록 보기")
    ap.add_argument("--brand", default="", help="영상 하단에 넣을 상호/문구 (예: 해피컴)")
    ap.add_argument("--no-audio", action="store_true", help="배경음 없이 생성")
    args = ap.parse_args(argv)

    if args.list_styles:
        for k, s in STYLES.items():
            print(f"{k}  {s.name:<6} {s.description}{'' if s.auto else '  (auto 제외)'}")
        for k, (_m, desc) in EXTRAS.items():
            print(f"--only {k}: {desc}")
        return

    d = dt.date.fromisoformat(args.date) if args.date else cal.today_kst()
    out_dir = Path(args.out) / d.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = d.strftime("%Y%m%d")
    jobs = args.only or JOBS
    audio = not args.no_audio
    style_key = auto_style(d.toordinal()) if args.style == "auto" else args.style
    style = STYLES[style_key]
    suffix = "" if style_key == "a" else f"_{style_key}"
    info = {"date": d.isoformat(), "korean_date": cal.korean_date(d), "style": style_key, "videos": {}}

    print(f"▶ {cal.korean_date(d)} 영상 생성 시작 (스타일 {style_key.upper()} · {style.name}) → {out_dir}")
    for job in jobs:
        t0 = time.time()
        if job == "motion":
            path = out_dir / f"{stamp}_*_m.mp4"
            meta = render_motion(d, out_dir)
        elif job in EXTRAS:
            path = out_dir / (f"{stamp}_hello.gif" if job == "gif" else f"{stamp}_{job}.mp4")
            meta = module(EXTRAS[job][0]).build(d, path, brand=args.brand, audio=audio)
        else:
            path = out_dir / f"{stamp}_{NUM[job]}_{job}{suffix}.mp4"
            kw = {"scene_name": args.scene} if (style_key == "a" and job == "busan") else {}
            meta = module(getattr(style, job)).build(d, path, brand=args.brand, audio=audio, **kw)
        meta["file"] = path.name
        info["videos"][job] = meta
        print(f"  ✔ {path.name}  ({time.time() - t0:.1f}s)  {json.dumps(meta, ensure_ascii=False)}")

    info_name = "info_extra.json" if set(jobs) <= set(EXTRAS) else f"info{suffix}.json"
    (out_dir / info_name).write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print("완료!")


if __name__ == "__main__":
    main()
