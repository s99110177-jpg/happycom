"""Remotion(모션그래픽) 영상용 데이터 내보내기.

    python -m morning_video.export_remotion [--date YYYY-MM-DD]

remotion/public/ 에 today.json(날짜·메시지·기념일), 해피 갈매기 스프라이트 PNG, 배경음 WAV, 한글 폰트를 만든다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil

from . import calendar_kr as cal
from .messages import character_message, morning_message, weekday_tag
from .render_common import REPO, _find_file, finish_audio, melody, ocean_noise, write_wav
from .scene_anniversary import THEMES
from .scene_character import WEEK_STYLE, draw_gull

PUBLIC = REPO / "remotion" / "public"
WINGS = list(range(-60, 91, 10))
FONTS = {"round": "NanumSquareRoundEB.ttf", "bold": "NanumSquareEB.ttf", "serif": "NanumMyeongjoExtraBold.ttf",
         "pen": "NanumPen.ttf"}


def _hex(c):
    return "#%02x%02x%02x" % tuple(c)


def export(d: dt.date):
    PUBLIC.mkdir(parents=True, exist_ok=True)
    days = cal.days_of(d)
    dday = None
    if days:
        main, others = days[0], days[1:]
    else:
        nxt = cal.next_notable(d)
        main, dday = nxt if nxt else (cal.Day("평범해서 소중한 날", "특별한 일 없는 오늘도\n충분히 소중한 하루", "🍀", "green", "popular"), None)
        others = []
    top, bottom, accent = THEMES.get(main.theme, THEMES["blue"])
    wtop, wbottom, scarf = WEEK_STYLE[d.weekday()]
    data = {
        "date": d.isoformat(), "year": d.year, "month": d.month, "day": d.day,
        "weekday": cal.WEEKDAYS[d.weekday()], "weekdayShort": cal.WEEKDAYS_SHORT[d.weekday()],
        "weekdayEn": ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"][d.weekday()],
        "koreanDate": cal.korean_date(d),
        "message": morning_message(d), "characterMessage": character_message(d), "tag": weekday_tag(d),
        "anniversary": {"name": main.name, "desc": main.desc, "emoji": main.emoji, "solemn": main.solemn,
                        "upcoming": dday is not None, "dday": dday, "others": [o.name for o in others[:3]],
                        "colors": [_hex(top), _hex(bottom), _hex(accent)]},
        "week": {"top": _hex(wtop), "bottom": _hex(wbottom), "accent": _hex(scarf)},
        "wings": WINGS,
    }
    (PUBLIC / "today.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 캐릭터 스프라이트
    sp = PUBLIC / "gull"
    sp.mkdir(exist_ok=True)
    for w in WINGS:
        for blink, mouth, tag in ((0, 0.2, "n"), (1, 0.2, "b"), (0, 0.8, "o")):
            draw_gull(w, blink, mouth, scarf).save(sp / f"w{w}_{tag}.png")

    # 폰트
    fd = PUBLIC / "fonts"
    fd.mkdir(exist_ok=True)
    for key, name in FONTS.items():
        src = _find_file(name)
        if src:
            shutil.copy(src, fd / f"{key}.ttf")

    # 배경음
    write_wav(PUBLIC / "busan.wav", finish_audio(
        ocean_noise(seed=d.toordinal()) * 0.4 + melody([(0.1, 64, 1.5, .5), (0.4, 69, 1.5, .5), (0.7, 73, 2, .5),
                                                         (1.6, 76, 2.5, .45), (2.6, 81, 2.5, .4), (3.4, 78, 2, .35)],
                                                        decay=1.6), vol=0.5))
    write_wav(PUBLIC / "anniversary.wav", finish_audio(melody(
        [(0.3, 72, .4, .6), (0.45, 76, .4, .6), (0.6, 79, .4, .6), (0.75, 84, 1.2, .7), (1.6, 88, 1.0, .4),
         (2.4, 79, 1.5, .4), (2.4, 84, 1.5, .35), (3.4, 86, 1.6, .3)] if not main.solemn else
        [(0.3, 57, 3.5, .4), (1.5, 64, 3, .35), (2.8, 69, 2.5, .3)], decay=2.2 if not main.solemn else .7), vol=0.5))
    write_wav(PUBLIC / "character.wav", finish_audio(melody(
        [(0.25, 67, .3, .6), (0.4, 72, .5, .6), (1.0, 76, .3, .5), (1.15, 79, .3, .5), (1.3, 84, .6, .6),
         (2.0, 81, .3, .5), (2.2, 79, .3, .5), (2.4, 76, .3, .5), (2.6, 77, .3, .5), (2.8, 79, .8, .55),
         (3.6, 72, 1.4, .5), (3.6, 76, 1.4, .4), (3.6, 79, 1.4, .35)], decay=4.5,
        harmonics=((1, 1.0), (2, .4), (3, .15))), vol=0.5))
    return data


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    a = ap.parse_args(argv)
    d = dt.date.fromisoformat(a.date) if a.date else cal.today_kst()
    data = export(d)
    print(f"내보냄: {PUBLIC}  ({data['koreanDate']}, 기념일: {data['anniversary']['name']})")


if __name__ == "__main__":
    main()
