"""사용법:
    python -m morning_video                 # 오늘(KST) 영상 3개 생성 -> output/YYYY-MM-DD/
    python -m morning_video --date 2026-12-25
    python -m morning_video --only busan --scene gamcheon --brand "해피컴"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time
from pathlib import Path

from . import calendar_kr as cal
from . import (scene_anniversary, scene_anniversary2, scene_busan, scene_busan2, scene_character,
               scene_character2, scene_character3, scene_photo, scene_busan3, scene_anniversary3,
               scene_character4)
from .render_common import REPO


def main(argv=None):
    ap = argparse.ArgumentParser(description="매일 아침 9:16 영상 3종 생성")
    ap.add_argument("--date", help="YYYY-MM-DD (기본: 오늘, 한국시간)")
    ap.add_argument("--out", default=str(REPO / "output"), help="출력 폴더")
    ap.add_argument("--only", choices=["busan", "anniversary", "character", "photo", "anim"], action="append",
                    help="특정 영상만 생성 (여러 번 지정 가능). photo=실사풍 광안대교, anim=캐릭터 애니메이션")
    ap.add_argument("--scene", choices=["gwangan", "gamcheon", "photo"], help="부산 장면 강제 지정")
    ap.add_argument("--style", choices=["a", "b", "c", "auto"], default="a",
                    help="a: 기본(광안대교·감천/카드/해변 캐릭터), b: 해운대·일력·페이퍼컷, "
                         "c: 레트로 포스터·네온사인·픽셀 게임, auto: 날마다 A→B→C 순환")
    ap.add_argument("--brand", default="", help="영상 하단에 넣을 상호/문구 (예: 해피컴)")
    ap.add_argument("--no-audio", action="store_true", help="배경음 없이 생성")
    args = ap.parse_args(argv)

    d = dt.date.fromisoformat(args.date) if args.date else cal.today_kst()
    out_dir = Path(args.out) / d.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = d.strftime("%Y%m%d")
    jobs = args.only or ["busan", "anniversary", "character"]
    audio = not args.no_audio
    info = {"date": d.isoformat(), "korean_date": cal.korean_date(d), "videos": {}}

    style = args.style if args.style != "auto" else ("a", "b", "c")[d.toordinal() % 3]
    busan_mod, anni_mod, char_mod = {
        "a": (scene_busan, scene_anniversary, scene_character),
        "b": (scene_busan2, scene_anniversary2, scene_character2),
        "c": (scene_busan3, scene_anniversary3, scene_character4),
    }[style]
    info["style"] = style
    print(f"▶ {cal.korean_date(d)} 영상 생성 시작 (스타일 {style.upper()}) → {out_dir}")
    for job in jobs:
        t0 = time.time()
        if job == "busan":
            path = out_dir / f"{stamp}_1_busan{'' if style == 'a' else '_' + style}.mp4"
            kw = {"scene_name": args.scene} if style == "a" else {}
            meta = busan_mod.build(d, path, brand=args.brand, audio=audio, **kw)
        elif job == "anniversary":
            path = out_dir / f"{stamp}_2_anniversary{'' if style == 'a' else '_' + style}.mp4"
            meta = anni_mod.build(d, path, brand=args.brand, audio=audio)
        elif job == "photo":
            path = out_dir / f"{stamp}_photo.mp4"
            meta = scene_photo.build(d, path, brand=args.brand, audio=audio)
        elif job == "anim":
            path = out_dir / f"{stamp}_anim.mp4"
            meta = scene_character3.build(d, path, brand=args.brand, audio=audio)
        else:
            path = out_dir / f"{stamp}_3_character{'' if style == 'a' else '_' + style}.mp4"
            meta = char_mod.build(d, path, brand=args.brand, audio=audio)
        meta["file"] = path.name
        info["videos"][job] = meta
        print(f"  ✔ {path.name}  ({time.time() - t0:.1f}s)  {json.dumps(meta, ensure_ascii=False)}")

    info_name = "info_extra.json" if set(jobs) <= {"photo", "anim"} else f"info{'' if style == 'a' else '_' + style}.json"
    (out_dir / info_name).write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print("완료!")


if __name__ == "__main__":
    main()
