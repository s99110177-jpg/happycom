"""algorithmic-art 스킬 템플릿(viewer.html)에 '윤슬' 알고리즘을 끼워 넣어 대화형 뷰어를 만든다.

    python3 generative/build_viewer.py   ->  generative/viewer.html (브라우저로 바로 열 수 있는 단일 파일)

템플릿의 고정 부분(레이아웃, 브랜딩, 씨앗 컨트롤)은 그대로 두고 제목·매개변수·알고리즘만 바꾼다.
알고리즘 원본은 tidal_light.js 하나라서 영상 렌더러와 뷰어가 항상 같은 코드를 쓴다.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / ".claude" / "skills" / "algorithmic-art" / "templates" / "viewer.html"

PARAMS = [  # id, 라벨, min, max, step, 기본값
    ("particleCount", "Particle Count · 빛 입자 수", 600, 5000, 100, 2600),
    ("drift", "Drift · 흐름의 세기", 0.3, 2.0, 0.1, 1.0),
    ("tideScale", "Tide Grain · 조수의 결", 0.0008, 0.006, 0.0002, 0.0022),
    ("glintThreshold", "Glint Threshold · 반짝임 문턱", 0.2, 0.9, 0.05, 0.55),
    ("bridgeSag", "Hidden Curve · 숨은 곡선의 처짐", 0.05, 0.4, 0.01, 0.22),
    ("trailFade", "Trail Fade · 흔적이 사라지는 속도", 8, 80, 2, 26),
]
COLORS = [("color1", "Dawn · 새벽", "#2a2a6e"), ("color2", "Horizon · 수평선", "#f2946f"), ("color3", "Glint · 윤슬", "#ffe6b8")]


def build():
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("<title>Generative Art Viewer</title>", "<title>윤슬 · Tidal Light</title>")
    html = html.replace("<h1>TITLE - EDIT</h1>", "<h1>윤슬 · Tidal Light</h1>")
    html = html.replace('<div class="subtitle">SUBHEADER - EDIT</div>',
                        '<div class="subtitle">새벽 바다의 빛을 계산으로 짓는 생성 미학. 씨앗 = 날짜(YYYYMMDD)</div>')
    html = html.replace('value="12345" onchange="updateSeed()"', 'value="20261120" onchange="updateSeed()"')
    html = html.replace("max-width: 1000px;", "max-width: 480px;")

    # 매개변수 섹션
    a = html.index("                <!-- Particle Count -->")
    b = html.index("            <!-- Colors Section")
    groups = []
    for pid, label, lo, hi, step, val in PARAMS:
        groups.append(f'''                <div class="control-group">
                    <label>{label}</label>
                    <div class="slider-container">
                        <input type="range" id="{pid}" min="{lo}" max="{hi}" step="{step}" value="{val}" oninput="updateParam('{pid}', this.value)">
                        <span class="value-display" id="{pid}-value">{val}</span>
                    </div>
                </div>
''')
    html = html[:a] + "".join(groups) + "            </div>\n\n" + html[b:]

    # 색 섹션
    for i, (cid, label, val) in enumerate(COLORS):
        old_label = ["Primary Color", "Secondary Color", "Accent Color"][i]
        old_val = ["#d97757", "#6a9bcc", "#788c5d"][i]
        html = html.replace(f"<label>{old_label}</label>", f"<label>{label}</label>")
        html = html.replace(f'id="{cid}" value="{old_val}"', f'id="{cid}" value="{val}"')
        html = html.replace(f'<span class="color-value" id="{cid}-value">{old_val}</span>',
                            f'<span class="color-value" id="{cid}-value">{val}</span>')

    # 동작 버튼 (스킬 요구: 재생성, 초기화, PNG 저장)
    html = html.replace('''                <div class="button-row">
                    <button class="button" onclick="resetParameters()">Reset</button>
                </div>''', '''                <div class="button-row">
                    <button class="button" onclick="initializeSystem()">Regenerate</button>
                    <button class="button" onclick="resetParameters()">Reset</button>
                </div>
                <div class="button-row" style="margin-top:8px">
                    <button class="button secondary" onclick="saveCanvas('tidal-light-' + params.seed, 'png')">Download PNG</button>
                </div>''')

    # 알고리즘
    a = html.index("        let params = {")
    b = html.index("        // ═══════════════════════════════════════════════════════════════════════\n        // SEED CONTROL FUNCTIONS")
    algo = (HERE / "tidal_light.js").read_text(encoding="utf-8")
    defaults = ", ".join(f"{pid}: {val}" for pid, *_rest, val in PARAMS)
    colors = ", ".join(f"'{v}'" for _c, _l, v in COLORS)
    html = html[:a] + f'''        let params = {{ seed: 20261120, {defaults}, colorPalette: [{colors}] }};
        let defaultParams = JSON.parse(JSON.stringify(params));

{algo}
        function setup() {{
            pixelDensity(1);
            const canvas = createCanvas(TL.W, TL.H);
            canvas.parent('canvas-container');
            initializeSystem();
            document.querySelector('.loading').style.display = 'none';
        }}

        function draw() {{
            stepSystem();
        }}

        function updateParam(name, value) {{
            params[name] = parseFloat(value);
            document.getElementById(name + '-value').textContent = value;
            if (name === 'particleCount' || name === 'bridgeSag') initializeSystem();
        }}

        function updateColor(id, value) {{
            params.colorPalette[parseInt(id.slice(-1)) - 1] = value;
            document.getElementById(id + '-value').textContent = value;
            buildBackground();
        }}

''' + html[b:]

    # 초기화 함수: 새 매개변수 목록에 맞게 교체
    a = html.index("        function resetParameters() {")
    b = html.index("        // Initialize UI on load")
    resets = "\n".join(f"            document.getElementById('{pid}').value = params.{pid};\n"
                       f"            document.getElementById('{pid}-value').textContent = params.{pid};" for pid, *_ in PARAMS)
    colors_reset = "\n".join(f"            document.getElementById('{cid}').value = params.colorPalette[{i}];\n"
                             f"            document.getElementById('{cid}-value').textContent = params.colorPalette[{i}];"
                             for i, (cid, *_r) in enumerate(COLORS))
    html = html[:a] + f'''        function resetParameters() {{
            params = JSON.parse(JSON.stringify(defaultParams));
{resets}
{colors_reset}
            updateSeedDisplay();
            initializeSystem();
        }}

''' + html[b:]
    out = HERE / "viewer.html"
    out.write_text(html, encoding="utf-8")
    print("저장:", out)


if __name__ == "__main__":
    build()
