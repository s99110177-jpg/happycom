"""날짜/요일 표기, 한국 기념일·공휴일·절기 조회."""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
WEEKDAYS_SHORT = ["월", "화", "수", "목", "금", "토", "일"]


def today_kst() -> dt.date:
    return dt.datetime.now(KST).date()


def korean_date(d: dt.date) -> str:
    """2026년 11월 12일 목요일"""
    return f"{d.year}년 {d.month}월 {d.day}일 {WEEKDAYS[d.weekday()]}"


def dotted_date(d: dt.date) -> str:
    """2026.11.12 (목)"""
    return f"{d.year}.{d.month:02d}.{d.day:02d} ({WEEKDAYS_SHORT[d.weekday()]})"


# ---------------------------------------------------------------------------
# 기념일 데이터
# kind: holiday(공휴일) / busan(부산) / lunar(세시) / legal(법정기념일)
#       popular(생활 기념일) / intl(국제기념일) / term(절기) / special(연도별)
# theme: anniversary 영상 색상 테마, solemn=True 이면 추모 분위기(축포 없음)
# ---------------------------------------------------------------------------

@dataclass
class Day:
    name: str
    desc: str
    emoji: str
    theme: str = "blue"
    kind: str = "legal"
    solemn: bool = False
    priority: int = field(default=0)

    def __post_init__(self):
        if not self.priority:
            self.priority = {
                "holiday": 100, "special": 95, "lunar": 90, "busan": 85,
                "legal": 70, "popular": 60, "intl": 50, "term": 45,
            }.get(self.kind, 10)


def _d(name, desc, emoji, theme="blue", kind="legal", solemn=False):
    return Day(name, desc, emoji, theme, kind, solemn)


FIXED: dict[str, list[Day]] = {
    "01-01": [_d("새해 첫날", "새로운 한 해가 시작되는 날\n올해도 복 많이 받으세요", "🌅", "red", "holiday")],
    "01-27": [_d("국제 홀로코스트 희생자 추모의 날", "희생자를 기억하고\n평화를 다짐하는 날", "🕯️", "solemn", "intl", True)],
    "02-04": [_d("세계 암의 날", "암 예방과 조기 검진의\n중요성을 알리는 날", "🎗️", "purple", "intl")],
    "02-14": [_d("밸런타인데이", "고마운 사람에게\n달콤한 마음을 전하는 날", "🍫", "pink", "popular")],
    "02-28": [_d("2·28 민주운동 기념일", "1960년 대구 학생들의\n민주화 정신을 기리는 날", "🕊️", "solemn", "legal", True)],
    "03-01": [_d("삼일절", "1919년 대한독립 만세의\n함성을 기억하는 날", "🇰🇷", "red", "holiday"),
              _d("삼겹살데이", "3이 두 번! 고소한\n삼겹살 먹는 날", "🥓", "orange", "popular")],
    "03-03": [_d("납세자의 날", "성실한 납세자에게\n감사하는 날", "🧾", "teal"),
              _d("삼겹살데이", "3이 두 번! 고소한\n삼겹살 먹는 날", "🥓", "orange", "popular")],
    "03-08": [_d("세계 여성의 날", "여성의 권리와 평등을\n생각하는 날", "💐", "purple", "intl"),
              _d("3·8 민주의거 기념일", "1960년 대전 학생들의\n민주의거를 기리는 날", "🕊️", "solemn", "legal", True)],
    "03-14": [_d("화이트데이", "사탕처럼 달콤한\n마음을 전하는 날", "🍬", "pink", "popular"),
              _d("파이데이", "원주율 3.14를 기념하는\n수학의 날", "🥧", "orange", "popular")],
    "03-15": [_d("3·15 의거 기념일", "1960년 마산 시민들의\n민주의거를 기리는 날", "🕊️", "solemn", "legal", True)],
    "03-20": [_d("국제 행복의 날", "행복을 삶의 목표로\n생각해 보는 날", "😊", "yellow", "intl")],
    "03-21": [_d("세계 시의 날", "한 편의 시로\n마음을 채우는 날", "📜", "purple", "intl")],
    "03-22": [_d("세계 물의 날", "물의 소중함을 되새기고\n아껴 쓰는 날", "💧", "blue")],
    "03-23": [_d("세계 기상의 날", "날씨와 기후의\n소중함을 생각하는 날", "🌦️", "teal", "intl")],
    "04-02": [_d("세계 자폐인의 날", "자폐에 대한 이해와\n존중을 넓히는 날", "🧩", "blue", "intl")],
    "04-03": [_d("제주 4·3 희생자 추념일", "제주 4·3의 희생자를\n추모하는 날", "🕊️", "solemn", "legal", True)],
    "04-05": [_d("식목일", "나무를 심고 가꾸며\n푸른 내일을 준비하는 날", "🌳", "green")],
    "04-07": [_d("보건의 날", "국민 건강의 소중함을\n생각하는 날 (세계 보건의 날)", "🩺", "teal")],
    "04-11": [_d("대한민국 임시정부 수립 기념일", "1919년 임시정부 수립을\n기념하는 날", "🇰🇷", "navy")],
    "04-14": [_d("블랙데이", "짜장면 한 그릇으로\n서로를 응원하는 날", "🍜", "gray", "popular")],
    "04-16": [_d("국민안전의 날", "안전의 소중함을 되새기고\n희생자를 기억하는 날", "🎗️", "solemn", "legal", True)],
    "04-19": [_d("4·19 혁명 기념일", "1960년 4·19 혁명의\n민주 이념을 기리는 날", "🕊️", "solemn", "legal", True)],
    "04-20": [_d("장애인의 날", "장애에 대한 이해를 넓히고\n함께 살아가는 날", "🤝", "green")],
    "04-21": [_d("과학의 날", "과학기술의 중요성을\n되새기는 날", "🔬", "blue")],
    "04-22": [_d("정보통신의 날", "정보통신의 발전을\n기념하는 날", "📡", "blue"),
              _d("지구의 날", "지구를 위해\n작은 실천을 하는 날", "🌍", "green", "intl")],
    "04-23": [_d("세계 책의 날", "좋은 책 한 권과\n함께하는 날", "📚", "orange", "intl")],
    "04-25": [_d("법의 날", "법의 존엄성을\n생각하는 날", "⚖️", "navy")],
    "04-28": [_d("충무공 이순신 탄신일", "성웅 이순신 장군의\n탄신을 기념하는 날", "⚓", "navy")],
    "05-01": [_d("노동절", "땀 흘려 일하는 모든 분께\n감사하는 날", "🛠️", "orange", "holiday")],
    "05-05": [_d("어린이날", "어린이의 꿈과 웃음을\n응원하는 날", "🎈", "yellow", "holiday")],
    "05-08": [_d("어버이날", "부모님의 사랑에\n감사를 전하는 날", "💐", "pink")],
    "05-10": [_d("유권자의 날", "소중한 한 표의\n의미를 되새기는 날", "🗳️", "teal")],
    "05-11": [_d("입양의 날", "가정의 사랑으로\n하나 되는 날", "👨‍👩‍👧", "pink")],
    "05-14": [_d("로즈데이", "장미 한 송이로\n사랑을 전하는 날", "🌹", "red", "popular")],
    "05-15": [_d("스승의 날", "가르침에 감사하는\n마음을 전하는 날", "🌷", "pink")],
    "05-18": [_d("5·18 민주화운동 기념일", "1980년 광주 민주화운동의\n정신을 기리는 날", "🕊️", "solemn", "legal", True)],
    "05-19": [_d("발명의 날", "작은 아이디어가\n세상을 바꾸는 날", "💡", "yellow")],
    "05-20": [_d("세계인의 날", "다양한 문화가\n어우러지는 날", "🌏", "teal"),
              _d("세계 벌의 날", "꿀벌의 소중함을\n생각하는 날", "🐝", "yellow", "intl")],
    "05-21": [_d("부부의 날", "둘이 하나 되어\n서로에게 감사하는 날", "💑", "pink")],
    "05-25": [_d("방재의 날", "재난에 미리 대비하고\n안전을 점검하는 날", "🛡️", "teal")],
    "05-31": [_d("바다의 날", "바다의 소중함을 되새기는 날\n해양도시 부산의 날!", "🌊", "blue", "busan"),
              _d("세계 금연의 날", "건강을 위해\n금연을 다짐하는 날", "🚭", "teal", "intl")],
    "06-05": [_d("환경의 날", "푸른 지구를 위해\n환경을 생각하는 날", "🌿", "green")],
    "06-06": [_d("현충일", "나라를 위해 희생하신\n분들을 추모하는 날", "🕊️", "solemn", "holiday", True)],
    "06-08": [_d("세계 해양의 날", "푸른 바다를 지키는\n마음을 나누는 날", "🐋", "blue", "intl")],
    "06-10": [_d("6·10 민주항쟁 기념일", "1987년 6월 민주항쟁의\n정신을 기리는 날", "🕊️", "solemn", "legal", True)],
    "06-14": [_d("세계 헌혈자의 날", "생명을 나누는 헌혈자에게\n감사하는 날", "🩸", "red", "intl")],
    "06-21": [_d("세계 음악의 날", "좋아하는 음악과\n함께하는 날", "🎵", "purple", "intl")],
    "06-25": [_d("6·25 전쟁일", "6·25 전쟁의 희생을\n기억하는 날", "🕊️", "solemn", "legal", True)],
    "06-28": [_d("철도의 날", "철도의 발전을\n기념하는 날", "🚄", "blue")],
    "07-11": [_d("세계 인구의 날", "인구 문제를\n함께 생각하는 날", "👥", "teal", "intl")],
    "07-17": [_d("제헌절", "1948년 대한민국 헌법\n공포를 기념하는 날", "📜", "navy", "holiday")],
    "07-27": [_d("유엔군 참전의 날", "유엔군 참전용사의 희생과\n헌신을 기억하는 날", "🕊️", "solemn", "busan", True)],
    "08-12": [_d("국제 청소년의 날", "청소년의 꿈을\n응원하는 날", "🌱", "green", "intl")],
    "08-14": [_d("일본군 위안부 피해자 기림의 날", "피해자를 기억하고\n존엄을 기리는 날", "🦋", "solemn", "legal", True)],
    "08-15": [_d("광복절", "1945년 광복의 기쁨을\n기념하는 날", "🇰🇷", "red", "holiday")],
    "08-19": [_d("세계 인도주의의 날", "인도주의 활동가에게\n감사하는 날", "🤲", "teal", "intl")],
    "09-07": [_d("사회복지의 날", "모두가 행복한\n복지를 생각하는 날", "🤝", "green")],
    "09-10": [_d("해양경찰의 날", "바다를 지키는\n해양경찰에 감사하는 날", "⚓", "navy")],
    "09-21": [_d("치매극복의 날", "치매에 대한 이해와\n관심을 높이는 날", "🧠", "purple"),
              _d("국제 평화의 날", "평화의 소중함을\n생각하는 날", "☮️", "teal", "intl")],
    "09-27": [_d("세계 관광의 날", "여행의 즐거움을\n나누는 날", "🧳", "orange", "intl")],
    "10-01": [_d("국군의 날", "국군 장병의 노고에\n감사하는 날", "🎖️", "navy"),
              _d("세계 노인의 날", "어르신을 공경하는\n마음을 나누는 날", "👵", "orange", "intl")],
    "10-02": [_d("노인의 날", "어르신의 지혜와 헌신에\n감사하는 날", "👴", "orange")],
    "10-03": [_d("개천절", "단군의 고조선 건국을\n기념하는 날", "🏔️", "navy", "holiday")],
    "10-05": [_d("부산시민의 날", "1592년 부산포해전 승리를\n기념하는 부산의 날", "⚓", "blue", "busan"),
              _d("세계 한인의 날", "세계 곳곳의 한인과\n함께하는 날", "🌏", "teal"),
              _d("세계 교사의 날", "선생님께\n감사하는 날", "🍎", "red", "intl")],
    "10-09": [_d("한글날", "세종대왕의 한글 창제를\n기념하는 날", "📖", "navy", "holiday")],
    "10-15": [_d("체육의 날", "몸을 움직이며\n건강을 챙기는 날", "🏃", "orange"),
              _d("흰지팡이의 날", "시각장애인의 안전과\n자립을 응원하는 날", "🦯", "gray")],
    "10-16": [_d("부마민주항쟁 기념일", "1979년 부산·마산 시민의\n민주항쟁을 기리는 날", "🕊️", "solemn", "busan", True),
              _d("세계 식량의 날", "음식의 소중함을\n생각하는 날", "🌾", "orange", "intl")],
    "10-21": [_d("경찰의 날", "시민의 안전을 지키는\n경찰에 감사하는 날", "👮", "navy")],
    "10-24": [_d("국제연합일", "유엔(UN)의 창설을\n기념하는 날", "🇺🇳", "blue")],
    "10-25": [_d("독도의 날", "우리 땅 독도를\n기억하는 날", "🏝️", "blue", "popular")],
    "10-28": [_d("교정의 날", "교정 공무원의 노고에\n감사하는 날", "🏛️", "navy")],
    "10-31": [_d("핼러윈", "재미있는 분장과\n호박 등불의 날", "🎃", "orange", "popular")],
    "11-03": [_d("학생독립운동 기념일", "1929년 학생들의\n항일 독립운동을 기리는 날", "📚", "navy")],
    "11-09": [_d("소방의 날", "119! 생명을 지키는\n소방관에 감사하는 날", "🚒", "red")],
    "11-11": [_d("유엔참전용사 국제추모의 날", "11시, 부산 유엔기념공원을\n향해 묵념하는 날", "🕊️", "solemn", "busan", True),
              _d("농업인의 날", "흙(土)이 겹치는 날\n농업인에게 감사하는 날", "🌾", "green"),
              _d("보행자의 날", "두 다리로 걷기 좋은\n보행 안전의 날", "🚶", "teal"),
              _d("가래떡데이", "우리 쌀 가래떡을\n나눠 먹는 날", "🍡", "yellow", "popular"),
              _d("빼빼로데이", "막대 과자로\n마음을 전하는 날", "🍫", "pink", "popular")],
    "11-12": [_d("세계 폐렴의 날", "폐렴 예방과 건강을\n생각하는 날", "🫁", "teal", "intl")],
    "11-13": [_d("세계 친절의 날", "작은 친절로\n하루를 밝히는 날", "💛", "yellow", "intl")],
    "11-14": [_d("세계 당뇨의 날", "당뇨 예방과\n건강을 챙기는 날", "💙", "blue", "intl")],
    "11-16": [_d("국제 관용의 날", "서로 다름을\n존중하는 날", "🤝", "teal", "intl")],
    "11-17": [_d("순국선열의 날", "나라를 위해 목숨 바친\n순국선열을 기리는 날", "🕊️", "solemn", "legal", True)],
    "11-19": [_d("세계 화장실의 날", "깨끗한 위생 환경을\n생각하는 날", "🚻", "teal", "intl"),
              _d("국제 남성의 날", "남성의 건강과\n행복을 응원하는 날", "🙋‍♂️", "blue", "intl")],
    "11-20": [_d("세계 어린이의 날", "어린이의 권리를\n생각하는 날", "🧒", "yellow", "intl")],
    "11-21": [_d("세계 텔레비전의 날", "텔레비전과 미디어를\n생각하는 날", "📺", "purple", "intl")],
    "12-01": [_d("세계 에이즈의 날", "에이즈에 대한 이해와\n관심을 높이는 날", "🎗️", "red", "intl")],
    "12-03": [_d("소비자의 날", "현명한 소비를\n생각하는 날", "🛒", "teal"),
              _d("세계 장애인의 날", "장애인의 권리를\n생각하는 날", "🤝", "green", "intl")],
    "12-05": [_d("무역의 날", "무역 강국 대한민국을\n기념하는 날", "🚢", "blue"),
              _d("국제 자원봉사자의 날", "나눔을 실천하는\n봉사자에게 감사하는 날", "🙌", "orange", "intl")],
    "12-10": [_d("세계 인권의 날", "모든 사람의 존엄과\n권리를 생각하는 날", "🕊️", "teal", "intl")],
    "12-24": [_d("크리스마스 이브", "설레는 마음으로\n성탄을 기다리는 밤", "🎄", "green", "popular")],
    "12-25": [_d("성탄절", "메리 크리스마스!\n사랑과 기쁨을 나누는 날", "🎄", "red", "holiday")],
    "12-31": [_d("한 해의 마지막 날", "올 한 해도\n정말 수고 많으셨어요", "🎆", "navy", "popular")],
}

# (월, 주차(-1=마지막), 요일 0=월) 규칙형 기념일
NTH_WEEKDAY: list[tuple[int, int, int, Day]] = [
    (3, 3, 2, _d("상공의 날", "상공인의 노고를\n격려하는 날", "🏭", "blue")),
    (3, 4, 4, _d("서해수호의 날", "서해를 지킨 용사들을\n기억하는 날", "🕊️", "solemn", "legal", True)),
    (5, 3, 0, _d("성년의 날", "어른이 된 것을\n축하하는 날", "🎓", "purple")),
    (10, -1, 1, _d("금융의 날", "저축과 금융의 의미를\n되새기는 날", "🏦", "teal")),
]

# 음력 기념일 (음력 월, 일)
LUNAR: list[tuple[int, int, Day]] = [
    (1, 1, _d("설날", "새해 복 많이 받으세요\n온 가족이 함께하는 설", "🧧", "red", "holiday")),
    (1, 15, _d("정월대보름", "부럼 깨고 오곡밥 먹으며\n한 해 건강을 비는 날", "🌕", "navy", "lunar")),
    (4, 8, _d("부처님오신날", "자비와 평화의\n연등을 밝히는 날", "🪷", "orange", "holiday")),
    (5, 5, _d("단오", "창포물에 머리 감고\n여름을 맞이하는 날", "🌿", "green", "lunar")),
    (7, 7, _d("칠석", "견우와 직녀가\n오작교에서 만나는 날", "🌌", "purple", "lunar")),
    (8, 15, _d("추석", "풍성한 한가위\n보름달처럼 넉넉하세요", "🌕", "orange", "holiday")),
]

# 해마다 날짜가 바뀌는 행사 (YYYY-MM-DD)
SPECIAL: dict[str, list[Day]] = {
    "2026-11-19": [_d("대학수학능력시험", "수험생 여러분\n그동안 정말 수고했어요!", "✏️", "navy", "special")],
    "2027-11-18": [_d("대학수학능력시험", "수험생 여러분\n그동안 정말 수고했어요!", "✏️", "navy", "special")],
}

SOLAR_TERMS = [  # 태양황경 0°부터 15° 간격
    "춘분", "청명", "곡우", "입하", "소만", "망종", "하지", "소서", "대서", "입추", "처서", "백로",
    "추분", "한로", "상강", "입동", "소설", "대설", "동지", "소한", "대한", "입춘", "우수", "경칩",
]
SOLAR_TERM_DESC = {
    "입춘": ("봄이 시작되는 날\n입춘대길 건양다경", "🌱", "green"),
    "우수": ("눈이 녹아 비가 되는\n봄비의 절기", "🌧️", "teal"),
    "경칩": ("개구리가 겨울잠에서\n깨어나는 절기", "🐸", "green"),
    "춘분": ("낮과 밤의 길이가\n같아지는 봄날", "🌸", "pink"),
    "청명": ("하늘이 맑고\n화창해지는 절기", "🌤️", "blue"),
    "곡우": ("봄비가 내려\n곡식을 기름지게 하는 절기", "🌾", "green"),
    "입하": ("여름이 시작되는\n초록의 절기", "🌿", "green"),
    "소만": ("햇볕이 풍부해\n만물이 자라는 절기", "☀️", "yellow"),
    "망종": ("씨 뿌리기 좋은\n초여름 절기", "🌾", "green"),
    "하지": ("1년 중 낮이\n가장 긴 날", "🌞", "yellow"),
    "소서": ("본격적인 더위가\n시작되는 절기", "🍉", "red"),
    "대서": ("1년 중 가장\n무더운 절기", "🔥", "orange"),
    "입추": ("가을이 시작되는\n절기", "🍂", "orange"),
    "처서": ("더위가 한풀 꺾이는\n절기", "🍃", "teal"),
    "백로": ("풀잎에 흰 이슬이\n맺히는 절기", "💧", "blue"),
    "추분": ("낮과 밤의 길이가\n같아지는 가을날", "🍁", "orange"),
    "한로": ("찬 이슬이 맺히는\n깊은 가을", "🍁", "brown"),
    "상강": ("서리가 내리기\n시작하는 절기", "❄️", "blue"),
    "입동": ("겨울이 시작되는\n김장의 절기", "🥬", "teal"),
    "소설": ("첫눈이 내린다는\n절기", "🌨️", "blue"),
    "대설": ("눈이 많이 내린다는\n절기", "☃️", "blue"),
    "동지": ("밤이 가장 긴 날\n팥죽 한 그릇 드세요", "🥣", "navy"),
    "소한": ("1년 중 가장\n추운 때", "🧣", "blue"),
    "대한": ("큰 추위의 절기\n겨울의 마지막 고비", "🧤", "navy"),
}


def _sun_longitude(jd: float) -> float:
    """태양의 겉보기 황경(도), Meeus 저정밀 공식."""
    t = (jd - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = math.radians(357.52911 + 35999.05029 * t - 0.0001537 * t * t)
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m)
         + (0.019993 - 0.000101 * t) * math.sin(2 * m) + 0.000289 * math.sin(3 * m))
    omega = math.radians(125.04 - 1934.136 * t)
    return (l0 + c - 0.00569 - 0.00478 * math.sin(omega)) % 360.0


def _jd_kst_midnight(d: dt.date) -> float:
    utc = dt.datetime(d.year, d.month, d.day, tzinfo=KST).astimezone(dt.timezone.utc)
    return utc.timestamp() / 86400.0 + 2440587.5


def solar_term(d: dt.date) -> str | None:
    """해당 날짜(KST)에 절기가 들면 이름을 돌려준다."""
    a = _sun_longitude(_jd_kst_midnight(d))
    b = _sun_longitude(_jd_kst_midnight(d + dt.timedelta(days=1)))
    ia, ib = int(a // 15), int(b // 15)
    if ia != ib:
        return SOLAR_TERMS[ib % 24]
    return None


def _nth_weekday(year: int, month: int, n: int, weekday: int) -> dt.date:
    if n > 0:
        first = dt.date(year, month, 1)
        offset = (weekday - first.weekday()) % 7
        return first + dt.timedelta(days=offset + 7 * (n - 1))
    nxt = dt.date(year + (month == 12), month % 12 + 1, 1)
    last = nxt - dt.timedelta(days=1)
    return last - dt.timedelta(days=(last.weekday() - weekday) % 7)


def _lunar_to_solar(year: int, lm: int, ld: int) -> dt.date | None:
    from korean_lunar_calendar import KoreanLunarCalendar
    cal = KoreanLunarCalendar()
    if not cal.setLunarDate(year, lm, ld, False):
        return None
    return dt.date.fromisoformat(cal.SolarIsoFormat())


def days_of(d: dt.date) -> list[Day]:
    """해당 날짜의 기념일 목록(우선순위 높은 순)."""
    out: list[Day] = []
    out += SPECIAL.get(d.isoformat(), [])
    out += FIXED.get(f"{d.month:02d}-{d.day:02d}", [])
    for m, n, wd, day in NTH_WEEKDAY:
        if m == d.month and _nth_weekday(d.year, m, n, wd) == d:
            out.append(day)
    for lm, ld, day in LUNAR:
        for y in (d.year, d.year - 1):  # 음력 설이 양력 다음 해일 수 있음
            try:
                if _lunar_to_solar(y, lm, ld) == d:
                    out.append(day)
            except Exception:
                pass
    # 설·추석 연휴 전날/다음날
    for lm, ld, name in ((1, 1, "설날"), (8, 15, "추석")):
        for y in (d.year, d.year - 1):
            try:
                base = _lunar_to_solar(y, lm, ld)
            except Exception:
                base = None
            if base and abs((d - base).days) == 1:
                label = f"{name} 연휴"
                out.append(_d(label, "가족과 함께하는\n따뜻한 연휴 보내세요", "🏡", "orange", "holiday"))
    term = solar_term(d)
    if term:
        desc, emoji, theme = SOLAR_TERM_DESC[term]
        out.append(_d(f"절기 {term}", desc, emoji, theme, "term"))
    # 대체공휴일·선거일 등은 holidays 라이브러리에서 보완
    try:
        import holidays
        for name in holidays.KR(years=d.year, language="ko").get_list(d):
            if any(k in name for k in ("대체", "선거", "임시")):
                sub = _d(name, "쉬어가는 날\n편안한 하루 보내세요", "🗓️", "teal", "holiday")
                sub.priority = 75
                out.append(sub)
    except Exception:
        pass
    seen, uniq = set(), []
    for day in out:
        if day.name not in seen:
            seen.add(day.name)
            uniq.append(day)
    uniq.sort(key=lambda x: -x.priority)
    return uniq


def next_notable(d: dt.date, horizon: int = 60) -> tuple[Day, int] | None:
    """기념일이 없는 날을 위해, 다가오는 가장 가까운 기념일과 D-day."""
    for i in range(1, horizon):
        cand = [x for x in days_of(d + dt.timedelta(days=i)) if x.kind in ("holiday", "special", "lunar", "busan", "legal")]
        if cand:
            return cand[0], i
    return None
