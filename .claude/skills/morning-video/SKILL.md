---
name: morning-video
description: 매일 아침 9:16 세로 영상(부산 배경 아침 메시지 / 오늘의 기념일 / 해피 갈매기 캐릭터)을 만들고, 새로운 영상 스타일을 추가한다. "오늘 영상 만들어줘", "다른 스타일로", "새 스타일 추가", "수능/명절에 맞게", "실사풍", "애니메이션", "릴스/쇼츠용 아침 인사 영상"처럼 이 저장소의 아침 영상 제작·스타일 확장을 요청하면 반드시 사용한다. Generates the daily 9:16 morning videos in this repo and adds new visual styles through the style registry.
---

# 아침 영상 제작 스킬

이 저장소(`morning_video/`)는 매일 아침 **9:16(1080×1920), 6초 이내(5.5초)** 영상 3개를 만든다.

| 번호 | 역할 | 반드시 들어가는 것 |
|---|---|---|
| 1 | 부산 배경 + 아침 메시지 | 년·월·일·요일, `messages.morning_message(d)` |
| 2 | 오늘의 기념일 | 년·월·일·요일, `calendar_kr.days_of(d)` 첫 항목. 없으면 `next_notable(d)` D-day |
| 3 | 캐릭터(해피 갈매기) | 년·월·일·요일, `messages.character_message(d)`, `weekday_tag(d)` |

스타일은 `morning_video/styles.py`의 `STYLES`에 등록된다. `--style auto`는 등록 순서대로 날마다 돌아간다.

## 1. 오늘 영상 만들기

```bash
python -m morning_video --list-styles             # 스타일 목록
python -m morning_video --style auto              # 오늘(KST), 자동 순환 스타일
python -m morning_video --style d --date 2026-11-20
python -m morning_video --only photo --only anim  # 단독 영상(실사풍, 캐릭터 애니메이션)
```

- 결과: `output/YYYY-MM-DD/YYYYMMDD_{1_busan|2_anniversary|3_character}[_스타일].mp4`와 `info*.json`
- 날짜는 **한국시간(KST)** 기준이다. 사용자가 "오늘"이라고 하면 `TZ=Asia/Seoul date`로 확인한다.
- 만든 뒤 `ffprobe`로 1080×1920 / 5.5초 / h264+aac를 확인한다. 각 영상의 마지막 프레임을 뽑아(`ffmpeg -ss 4.8 -frames:v 1`) 눈으로 본 다음에 전달한다.

### 외부 무료 스킬로 만드는 영상

이 저장소에는 무료로 공개된 인기 영상 스킬 3개가 같이 들어 있다(`.claude/skills/THIRD_PARTY.md`). 해당 작업을 할 때는 그 스킬을 먼저 불러온다.

| 명령 | 스킬 | 결과 |
|---|---|---|
| `python -m morning_video --only motion` | `remotion-best-practices` (Remotion, React 코드로 만드는 모션그래픽) | `*_1_busan_m.mp4`, `*_2_anniversary_m.mp4`, `*_3_character_m.mp4` |
| `python -m morning_video --only art` | `algorithmic-art` (p5.js 제너러티브 아트, 씨앗=날짜) | `*_art.mp4`, 대화형 뷰어 `generative/viewer.html` |
| `python -m morning_video --only gif` | `slack-gif-creator` (GIF 스티커) | `*_hello.gif`(480×480), `*_hello_emoji.gif`(128×128) |

- Remotion: `remotion/`가 프로젝트다. `python -m morning_video.export_remotion`이 `public/today.json`(날짜·메시지·기념일), 갈매기 스프라이트, 폰트, 배경음을 만든다. 장면은 `remotion/src/Motion*.tsx`. 미리보기는 `cd remotion && npx remotion studio`. 애니메이션은 `interpolate`/`Easing.spring`으로만 만들고 CSS 애니메이션은 쓰지 않는다. 회사 규모에 따라 Remotion 라이선스가 필요할 수 있다.
- 제너러티브: 알고리즘 원본은 `generative/tidal_light.js` 하나다. 영상(`render.html` + `capture.js`)과 뷰어(`python3 generative/build_viewer.py`)가 이 파일을 함께 쓴다. 미학 설명은 `generative/philosophy.md`.
- GIF: `morning_video/scene_gif.py`가 스킬의 `GIFBuilder`, 이징, `validate_gif`를 사용한다. 글자는 나눔 폰트로 그리고 이모지 글꼴은 쓰지 않는다.
- node 패키지 설치: `cd remotion && npm install`, `cd generative && npm install`. 헤드리스 Chromium이 필요하다(Playwright).

## 2. 특별한 날 맞춤 (수능, 명절 등)

- 기념일 추가·수정: `calendar_kr.py`의 `FIXED`(매년 같은 날), `NTH_WEEKDAY`(N번째 요일), `LUNAR`(음력), `SPECIAL`(연도별 날짜)
- 그날만 쓰는 문구: `messages.py`의 `SPECIAL_DAYS[날짜] = {"morning", "character", "tag", "headband"}`. 수능처럼 해마다 날짜가 바뀌는 행사는 날짜별로 넣는다.
- 추모일(`solemn=True`)은 축포·통통 튀는 효과 없이 차분하게 만든다. 새 스타일도 `main.solemn`을 확인해 이 규칙을 지킨다.

## 3. 새 스타일 추가 절차

사용자가 "다른 스타일", "새로운 스타일"을 원하면 이 절차를 따른다. 지금까지 쓴 스타일과 겹치지 않는 표현 방식을 고른다. 아이디어는 `references/style-ideas.md`에 있다.

1. **방향 정하기**: 세 영상의 매체·질감을 서로 다르게 고른다(예: 수채화 / 칠판 / 스크랩북). 이미 등록된 스타일은 `--list-styles`로 확인한다.
2. **장면 모듈 3개 작성**: 파일 이름은 `morning_video/scene_<역할><번호>.py`로 한다. 각 모듈은 아래 계약을 지킨다.
   ```python
   def build(d: dt.date, out: Path, brand: str = "", audio=True, **_) -> dict:
       ...
       def frame(t: float, i: int) -> Image.Image:  # RGBA 1080x1920, t=0..5.5초
           ...
       render_video(out, frame, snd)  # snd: numpy 오디오 또는 None
       return {"message": ...}       # info.json 에 남길 요약
   ```
   - 공용 도구: `render_common.py`(폰트 `font(kind,size)`: bold/semibold/regular/round/serif/pen/emoji, `text_layer`, `paste`, `emoji_image`, 이징, `melody`, `ocean_noise`, `finish_audio`)
   - 손그림 질감: `handmade.py`(`paper`, `watercolor`, `multiply`, `chalkify`, `sticker`, `wipe`, `scribble_ellipse`, `fbm`)
   - 캐릭터: `scene_character.draw_gull(wing_angle, blink, mouth, scarf_color)`. 프레임마다 다시 그리지 말고 각도를 양자화해 캐시한다.
   - 무거운 배경은 `build` 안에서 한 번만 만들고, `frame`에서는 움직이는 요소만 합성한다(프레임당 0.3초 이하 권장).
3. **등록**: `styles.py`의 `STYLES`에 `Style("e", "이름", "scene_busan5", "scene_anniversary5", "scene_character6", "설명")` 한 줄을 추가한다. `.github/workflows/daily-morning-video.yml`의 `style` 선택지와 README 표에도 추가한다.
4. **미리보기로 다듬기**: 인코딩 없이 여러 시점을 한 장으로 본다.
   ```bash
   python -m morning_video.preview scene_busan5 --date 2026-11-20 --times 0.5,2,4.8 --out /tmp/p.png
   python -m morning_video.preview scene_anniversary5 --date 2026-11-11   # 추모일(여러 기념일)
   python -m morning_video.preview scene_anniversary5 --date 2026-11-25   # 기념일 없는 날(D-day)
   ```
   PNG를 직접 열어 보고 아래 점검표를 통과할 때까지 고친다.
5. **최종 렌더 → 확인 → 커밋**: `python -m morning_video --style e`로 만들고 `ffprobe`로 확인한 뒤 커밋한다.

## 4. 품질 점검표 (전달 전에 매번 확인)

- [ ] 9:16, 1080×1920, 6초 이내, 소리 포함(또는 `--no-audio`)
- [ ] 세 영상 모두 **년·월·일·요일**이 보이고, 첫 1초 안에 날짜가 나타난다
- [ ] 글자와 배경의 대비가 충분하다. 글자가 건물·구름·캐릭터와 겹치지 않는다
- [ ] 글자가 화면 밖으로 나가지 않는다. 긴 기념일 이름(예: "일본군 위안부 피해자 기림의 날")은 `_wrap_title`이나 `fit_font`로 맞춘다
- [ ] 기념일이 여러 개인 날, 없는 날(D-day), 추모일을 각각 미리보기로 확인했다
- [ ] 마지막 0.3초 페이드로 반복 재생할 때 자연스럽다

## 5. 하지 말 것

- 기존 캐릭터·게임·애니메이션을 따라 만들지 않는다(이름, 생김새, 상징 아이템 포함). 예: 부산시 캐릭터, 특정 게임의 "?" 블록·배관. 해피 갈매기는 이 저장소의 오리지널 캐릭터다.
- 실제 기업·브랜드 로고와 남의 사진·그림을 쓰지 않는다. 실제 사진이 필요하면 사용자가 직접 찍은 사진을 `assets/busan/`에 넣도록 안내한다. 스타일 A의 1번 영상이 사진 모드를 지원한다.
- 기념일 날짜·설명을 추측으로 넣지 않는다. 확실하지 않으면 검색으로 확인하거나 사용자에게 묻는다.
- `output/`은 커밋하지 않는다(.gitignore). 영상은 사용자에게 파일로 전달하거나, 매일 자동 실행이 GitHub Releases에 올린다.
