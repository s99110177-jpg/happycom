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

### 스타일 C (`--style c`)

| # | 영상 | 내용 |
|---|------|------|
| 1 | `YYYYMMDD_1_busan_c.mp4` | 레트로 여행 포스터: 용두산 부산타워·부산항 크레인·배, 리소그래프 질감, 날짜 우표 도장 |
| 2 | `YYYYMMDD_2_anniversary_c.mp4` | 네온사인: 벽돌 벽에 날짜와 기념일 이름이 '지직' 하며 켜짐 |
| 3 | `YYYYMMDD_3_character_c.mp4` | 8비트 픽셀 게임: 해피 갈매기가 걸어와 점프 → 보물상자 → RPG 대화창 인사, 칩튠 사운드 |

### 스타일 D (`--style d`)

| # | 영상 | 내용 |
|---|------|------|
| 1 | `YYYYMMDD_1_busan_d.mp4` | 수채화: 태종대 절벽과 하얀 등대, 물감이 번지며 그림이 완성되고 손글씨 날짜·메시지 |
| 2 | `YYYYMMDD_2_anniversary_d.mp4` | 칠판: 날짜와 오늘의 기념일이 분필로 써지고 동그라미·별 낙서, 분필 소리 |
| 3 | `YYYYMMDD_3_character_d.mp4` | 다이어리 스크랩북: 모눈 노트에 폴라로이드 속 해피 갈매기, 마스킹테이프·스티커, 손글씨 한마디 |

`python -m morning_video --list-styles`로 전체 목록을 볼 수 있습니다.

`--style auto`로 실행하면 날마다 등록된 스타일(A → B → C → D …)이 돌아가며 나옵니다. 매일 자동 생성은 기본으로 `auto`를 씁니다.
고정하려면 Settings → Secrets and variables → Actions → **Variables**에 `STYLE`을 `a`, `b`, `c`, `d` 중 하나로 추가하세요.

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

## 무료 인기 영상 스킬로 만드는 영상

| 명령 | 사용 스킬 | 결과 |
|---|---|---|
| `python -m morning_video --only motion` | Remotion 공식 스킬 (React 코드 모션그래픽) | 모션그래픽 3종 `*_m.mp4` |
| `python -m morning_video --only art` | Anthropic `algorithmic-art` (p5.js) | 제너러티브 아트 '윤슬' `*_art.mp4` + 대화형 뷰어 `generative/viewer.html` |
| `python -m morning_video --only gif` | Anthropic `slack-gif-creator` | 인사 GIF `*_hello.gif` + 이모지 `*_hello_emoji.gif` |

node가 필요합니다: `cd remotion && npm install`, `cd generative && npm install`. 출처와 라이선스는 `.claude/skills/THIRD_PARTY.md`에 있습니다.

## Claude Code 스킬: 새 스타일 늘리기

`.claude/skills/morning-video/`에 영상 제작 스킬이 들어 있습니다. Claude Code에서 이 저장소를 열고
"오늘 영상 만들어줘", "새로운 스타일로 만들어줘"처럼 요청하면 스킬이 절차를 안내합니다.

- 스타일 등록부: `morning_video/styles.py` (장면 모듈 3개 + 한 줄 등록 = 새 스타일)
- 빠른 미리보기: `python -m morning_video.preview scene_busan4 --times 0.5,2,4.8 --out preview.png`
- 손그림 질감 도구: `morning_video/handmade.py` (수채화, 분필, 스티커, 손글씨 써지는 효과)
- 다음 스타일 후보: `.claude/skills/morning-video/references/style-ideas.md`

## 내용 바꾸기

| 바꾸고 싶은 것 | 파일 |
|----------------|------|
| 아침 메시지, 캐릭터 대사, 요일 문구 | `morning_video/messages.py` |
| 기념일 추가·수정 (고정일 / N번째 요일 / 음력 / 연도별 행사) | `morning_video/calendar_kr.py` |
| 부산 배경을 직접 찍은 사진으로 | `assets/busan/`에 사진 넣기 |

기념일은 내장 목록과 계산으로 확인합니다. 음력은 `korean_lunar_calendar`, 대체공휴일·선거일은 `holidays` 패키지,
24절기는 태양 황경으로 계산합니다. 수능처럼 해마다 날짜가 바뀌는 행사는 `SPECIAL`에 연도별로 추가해 주세요.
