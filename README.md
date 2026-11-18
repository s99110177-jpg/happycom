# 매일 아침 영상 생성기

매일 아침 **9:16 세로, 5.5초** 영상 3개를 자동으로 만듭니다.
모든 영상에 그날의 **년·월·일·요일**이 들어갑니다.

| # | 영상 | 내용 |
|---|------|------|
| 1 | `YYYYMMDD_1_busan.mp4` | 부산 배경(광안대교 해돋이 / 감천문화마을)에 아침 메시지 + 날짜·요일 |
| 2 | `YYYYMMDD_2_anniversary.mp4` | 그날의 기념일(공휴일·법정기념일·부산 기념일·세시·절기·국제기념일). 없으면 다가오는 기념일 D-day |
| 3 | `YYYYMMDD_3_character.mp4` | 오리지널 캐릭터 '해피 갈매기'가 날개를 흔들며 말풍선으로 인사 |

- 1080×1920, 30fps, H.264 + AAC(합성 배경음) — 인스타 릴스, 유튜브 쇼츠, 카카오톡 프로필/상태에 바로 사용
- 메시지와 장면은 날짜에 따라 매일 바뀝니다.
- 추모일(현충일, 순국선열의 날, 유엔참전용사 국제추모의 날 등)은 축포 없이 차분한 분위기로 만듭니다.

### 스타일 B (`--style b`)

| # | 영상 | 내용 |
|---|------|------|
| 1 | `YYYYMMDD_1_busan_b.mp4` | 해운대 해변(파도·파라솔·엘시티) + 잡지풍 큰 날짜 타이포 |
| 2 | `YYYYMMDD_2_anniversary_b.mp4` | 일력: 어제 장이 뜯겨 나가고 오늘 날짜·음력·기념일이 나타남 |
| 3 | `YYYYMMDD_3_character_b.mp4` | 종이 공예(페이퍼컷) 부산 풍경 위로 해피 갈매기가 인사 현수막을 끌고 비행 |

`--style auto`로 실행하면 날마다 A/B 스타일이 번갈아 나옵니다. 매일 자동 생성은 기본으로 `auto`를 씁니다.
고정하려면 Settings → Secrets and variables → Actions → **Variables**에 `STYLE`을 `a` 또는 `b`로 추가하세요.

### 추가 영상

| 옵션 | 파일 | 내용 |
|------|------|------|
| `--only photo` | `YYYYMMDD_photo.mp4` | 실사풍: 새벽 광안대교를 사진처럼 계산해 그린 장면(구름, 윤슬, 빛 번짐, 렌즈 플레어, 필름 그레인) |
| `--only anim` | `YYYYMMDD_anim.mp4` | 캐릭터 애니메이션: 해피 갈매기가 착지 → 주먹 3번 "화이팅!" → 큰 제목과 인사. 수능일엔 '합격' 머리띠 |

실제 사진으로 만들고 싶다면 `assets/busan/`에 직접 찍은 사진을 넣고 기본 스타일(1번 영상)을 사용하세요.

## 매일 자동 생성 (GitHub Actions)

`.github/workflows/daily-morning-video.yml`이 **매일 07:00(한국시간)** 실행됩니다.
GitHub 예약 실행은 몇 분 늦어질 수 있습니다.

- 결과: 저장소의 **Releases** 탭에 `morning-YYYY-MM-DD`로 영상 3개가 올라옵니다. 휴대폰에서도 바로 받을 수 있습니다.
- 지금 바로 만들려면: **Actions → 매일 아침 영상 생성 → Run workflow**. 날짜와 하단 문구를 지정할 수 있습니다.
- 상호명을 매일 넣으려면: Settings → Secrets and variables → Actions → **Variables**에 `BRAND` (예: `해피컴`)를 추가합니다.

## 직접 실행

```bash
sudo apt install ffmpeg fonts-nanum fonts-nanum-extra fonts-noto-color-emoji
pip install -r requirements.txt

python -m morning_video                        # 오늘(한국시간) 영상 3개 → output/YYYY-MM-DD/
python -m morning_video --date 2026-12-25      # 특정 날짜
python -m morning_video --brand "해피컴"        # 하단에 상호 넣기
python -m morning_video --only busan --scene gamcheon
python -m morning_video --no-audio             # 무음
python -m morning_video --style b              # 스타일 B (해운대·일력·페이퍼컷)
```

## 내용 바꾸기

| 바꾸고 싶은 것 | 파일 |
|----------------|------|
| 아침 메시지, 캐릭터 대사, 요일 문구 | `morning_video/messages.py` |
| 기념일 추가·수정 (고정일 / N번째 요일 / 음력 / 연도별 행사) | `morning_video/calendar_kr.py` |
| 부산 배경을 직접 찍은 사진으로 | `assets/busan/`에 사진 넣기 |

기념일은 내장 목록과 계산으로 확인합니다. 음력은 `korean_lunar_calendar`, 대체공휴일·선거일은 `holidays` 패키지,
24절기는 태양 황경으로 계산합니다. 수능처럼 해마다 날짜가 바뀌는 행사는 `SPECIAL`에 연도별로 추가해 주세요.
