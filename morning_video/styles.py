"""스타일 등록부.

새 스타일을 추가하려면 scene 모듈 3개(부산/기념일/캐릭터)를 만들고 아래 STYLES 에 한 줄 추가하면 된다.
각 scene 모듈은 build(d, out, brand="", audio=True, **kw) -> dict 를 제공해야 한다.
--style auto 는 등록 순서대로 날마다 돌아가며 쓴다 (auto=False 인 스타일은 제외).
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Style:
    key: str
    name: str
    busan: str
    anniversary: str
    character: str
    description: str
    auto: bool = True


STYLES: dict[str, Style] = {s.key: s for s in [
    Style("a", "기본", "scene_busan", "scene_anniversary", "scene_character",
          "광안대교 해돋이·감천문화마을 / 컬러 카드+이모지 / 해변의 해피 갈매기"),
    Style("b", "매거진", "scene_busan2", "scene_anniversary2", "scene_character2",
          "해운대 해변+잡지풍 타이포 / 일력(달력 넘기기) / 페이퍼컷 현수막 비행"),
    Style("c", "레트로", "scene_busan3", "scene_anniversary3", "scene_character4",
          "레트로 여행 포스터 / 네온사인 / 8비트 픽셀 게임"),
    Style("d", "손그림", "scene_busan4", "scene_anniversary4", "scene_character5",
          "수채화 태종대 등대 / 칠판 손글씨 / 다이어리 스크랩북 스티커"),
]}

# 단독 영상 (스타일 세트와 별개, --only 로 생성)
EXTRAS = {
    "photo": ("scene_photo", "실사풍 새벽 광안대교"),
    "anim": ("scene_character3", "캐릭터 애니메이션 (착지 → 화이팅 → 인사)"),
    "gif": ("scene_gif", "움직이는 인사 GIF 480x480 + 이모지 128x128 (slack-gif-creator 스킬)"),
    "motion": ("remotion", "Remotion 모션그래픽 3종 (remotion-best-practices 스킬, node 필요)"),
    "art": ("scene_generative", "제너러티브 아트 '윤슬' (algorithmic-art 스킬, p5.js, 날짜가 씨앗)"),
}


def auto_style(ordinal: int) -> str:
    keys = [k for k, s in STYLES.items() if s.auto]
    return keys[ordinal % len(keys)]


def module(name: str):
    return importlib.import_module(f"morning_video.{name}")
