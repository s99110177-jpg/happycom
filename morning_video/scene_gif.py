"""움직이는 인사 GIF (slack-gif-creator 스킬): 메시지용 480x480 GIF + 이모지용 128x128 GIF.

카카오톡·슬랙·문자에 바로 붙여 넣을 수 있는 가벼운 '좋은 아침' 스티커. 스킬의 GIFBuilder·이징·검증 도구를 쓴다.
"""
from __future__ import annotations

import datetime as dt
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from . import calendar_kr as cal
from .render_common import REPO, font, text_layer
from .scene_character import CH, CW, INK, WEEK_STYLE, draw_gull

SKILL = REPO / ".claude" / "skills" / "slack-gif-creator"
if str(SKILL) not in sys.path:
    sys.path.insert(0, str(SKILL))

from core.easing import interpolate  # noqa: E402
from core.frame_composer import create_gradient_background, draw_star  # noqa: E402
from core.gif_builder import GIFBuilder  # noqa: E402
from core.validators import validate_gif  # noqa: E402


def _gull_cache(accent):
    cache = {}

    def get(wing, blink, mouth, scale):
        key = (round(wing / 5) * 5, blink, round(mouth, 1), scale)
        if key not in cache:
            g = draw_gull(key[0], key[1], key[2], accent)
            cache[key] = g.resize((int(CW * scale), int(CH * scale)), Image.LANCZOS)
        return cache[key]
    return get


def _message_gif(d: dt.date, path: Path):
    top, bottom, accent = WEEK_STYLE[d.weekday()]
    S, FPS, N = 480, 15, 36  # 2.4초
    gull = _gull_cache(accent)
    t_date = text_layer(f"{d.month}.{d.day} {cal.WEEKDAYS[d.weekday()]}", font("round", 44), (255, 255, 255),
                        stroke=6, stroke_fill=INK)
    t_hi = text_layer("좋은 아침!", font("round", 62), INK)
    builder = GIFBuilder(width=S, height=S, fps=FPS)
    for i in range(N):
        t = i / (N - 1)
        frame = create_gradient_background(S, S, top, bottom).convert("RGBA")
        dr = ImageDraw.Draw(frame)
        # 반짝이는 별 (안쪽 작은 별 겹쳐 깊이감)
        for k, (sx, sy) in enumerate(((70, 120), (410, 150), (60, 330), (420, 360))):
            pulse = 0.75 + 0.35 * math.sin((t * 2 + k * 0.25) * 2 * math.pi)
            draw_star(frame, (sx, sy), int(20 * pulse), fill_color=(255, 220, 90), outline_color=INK, outline_width=3)
            draw_star(frame, (sx, sy), int(8 * pulse), fill_color=(255, 250, 220))
        # 바닥 무대
        dr.ellipse((-60, 420, S + 60, 600), fill=(255, 255, 255, 255), outline=INK + (255,), width=5)
        # 갈매기: 위에서 통통 떨어져 착지 후 손 흔들기
        y_off = interpolate(-360, 0, min(1, t / 0.35), "bounce_out")
        wing = -55 if t < 0.35 else 35 + 35 * math.sin((t - 0.35) * 5 * 2 * math.pi)
        blink = 1 if 0.78 < t < 0.84 else 0
        g = gull(wing, blink, 0.6 if t > 0.4 else 0.2, 0.36)
        frame.alpha_composite(g, (int(S / 2 - g.width / 2), int(440 - g.height + y_off)))
        # 날짜 (위에서 미끄러져 내려옴, 살짝 튕김)
        dy = interpolate(-80, 0, min(1, t / 0.3), "back_out")
        frame.alpha_composite(t_date, (int(S / 2 - t_date.width / 2), int(28 + dy)))
        # '좋은 아침!' 말풍선 팝
        if t > 0.4:
            k = interpolate(0.2, 1.0, min(1, (t - 0.4) / 0.2), "elastic_out")
            bw, bh = int((t_hi.width + 50) * k), int((t_hi.height + 30) * k)
            if bw > 10:
                bub = Image.new("RGBA", (bw + 10, bh + 30), (0, 0, 0, 0))
                bd = ImageDraw.Draw(bub)
                bd.rounded_rectangle((3, 3, bw + 3, bh + 3), int(24 * k), fill=(255, 255, 255, 255), outline=INK + (255,), width=4)
                bd.polygon([(bw * 0.4, bh), (bw * 0.55, bh), (bw * 0.45, bh + 24 * k)], fill=(255, 255, 255, 255), outline=INK + (255,))
                if k > 0.8:
                    hi = t_hi.resize((max(1, int(t_hi.width * k)), max(1, int(t_hi.height * k))), Image.LANCZOS)
                    bub.alpha_composite(hi, (int((bw - hi.width) / 2) + 3, int((bh - hi.height) / 2) + 3))
                frame.alpha_composite(bub, (int(S / 2 - bw / 2 + 60), 105))
        builder.add_frame(frame.convert("RGB"))
    info = builder.save(path, num_colors=128)
    return info


def _emoji_gif(d: dt.date, path: Path):
    _top, _bottom, accent = WEEK_STYLE[d.weekday()]
    S, FPS, N = 128, 12, 24  # 2초, 투명 대신 흰 원 배경(슬랙 다크/라이트 모두 보이게)
    gull = _gull_cache(accent)
    builder = GIFBuilder(width=S, height=S, fps=FPS)
    for i in range(N):
        t = i / N
        frame = Image.new("RGBA", (S, S), (255, 255, 255, 255))
        ImageDraw.Draw(frame).ellipse((2, 2, S - 3, S - 3), fill=(255, 236, 200, 255), outline=INK + (255,), width=3)
        hop = -10 * abs(math.sin(t * 2 * math.pi))
        wing = 35 + 40 * math.sin(t * 4 * math.pi)
        g = gull(wing, 1 if 0.7 < t < 0.76 else 0, 0.5, 0.15)
        frame.alpha_composite(g, (int(S / 2 - g.width / 2), int(S - 8 - g.height + hop)))
        builder.add_frame(frame.convert("RGB"))
    return builder.save(path, num_colors=48, optimize_for_emoji=True)


def build(d: dt.date, out: Path, brand: str = "", audio=True, **_):
    out = Path(out).with_suffix(".gif")
    emoji = out.with_name(out.stem + "_emoji.gif")
    _message_gif(d, out)
    _emoji_gif(d, emoji)
    ok_msg, _ = validate_gif(out, is_emoji=False, verbose=False)
    ok_emoji, _ = validate_gif(emoji, is_emoji=True, verbose=False)
    return {"gif": out.name, "emoji": emoji.name, "message_ok": ok_msg, "emoji_ok": ok_emoji,
            "message_kb": round(out.stat().st_size / 1024), "emoji_kb": round(emoji.stat().st_size / 1024)}
