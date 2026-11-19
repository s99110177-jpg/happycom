// 윤슬 (Tidal Light) — p5.js 전역 모드 알고리즘.
// viewer.html(대화형)과 render.html(영상 프레임 캡처)이 같은 코드를 쓴다.
// 사용하는 쪽에서 전역 `params` 를 정의한 뒤 initializeSystem() 과 stepSystem() 을 호출한다.

const TL = {
  W: 1080,
  H: 1920,
  HORIZON: 0.56,          // 수평선 높이(비율)
  particles: [],
  frame: 0,
};

function tlPalette() {
  return params.colorPalette.map((c) => color(c));
}

function tlBridgeY(x) {
  // 보이지 않는 현수선: 두 주탑 사이에서 처지는 곡선
  const hz = TL.H * TL.HORIZON;
  const t1 = TL.W * 0.27, t2 = TL.W * 0.73, top = hz - TL.H * 0.15;
  if (x < t1) return hz - 12 - (hz - 12 - top) * pow(x / t1, 1.8);
  if (x > t2) return hz - 12 - (hz - 12 - top) * pow((TL.W - x) / (TL.W - t2), 1.8);
  const u = (x - t1) / (t2 - t1);
  return top + (hz - 30 - top) * params.bridgeSag * 4.5 * u * (1 - u);
}

function tlReflectY(x) {
  const hz = TL.H * TL.HORIZON;
  return hz + (hz - tlBridgeY(x)) * 0.55;
}

class TideParticle {
  constructor(sky) {
    this.reset(sky, true);
  }

  reset(sky, first) {
    const hz = TL.H * TL.HORIZON;
    this.sky = sky;
    if (sky) {
      const a = random(PI, TWO_PI);
      const r = random(20, first ? TL.H * 0.55 : 80);
      this.x = TL.W / 2 + cos(a) * r;
      this.y = hz - 30 + sin(a) * r * 0.9;
    } else {
      this.x = random(-40, TL.W + 40);
      this.y = hz + pow(random(), 1.35) * (TL.H - hz);
    }
    this.life = random(60, 220);
    this.age = first ? random(this.life) : 0;
    this.px = this.x;
    this.py = this.y;
  }

  step(pal) {
    const hz = TL.H * TL.HORIZON;
    const z = TL.frame * 0.004 * params.drift;
    this.px = this.x;
    this.py = this.y;
    if (this.sky) {
      // 태양을 중심으로 느리게 회전하며 퍼지는 빛
      const dx = this.x - TL.W / 2, dy = this.y - (hz - 30);
      const ang = atan2(dy, dx) + 0.004 * params.drift + (noise(dx * 0.003, dy * 0.003, z) - 0.5) * 0.02;
      const r = sqrt(dx * dx + dy * dy) + 0.9 * params.drift;
      this.x = TL.W / 2 + cos(ang) * r;
      this.y = hz - 30 + sin(ang) * r;
      const by = tlBridgeY(this.x);
      if (abs(this.y - by) < 18) this.y += (by - this.y) * 0.08;   // 하늘의 현수선 인력
      if (this.y > hz - 4) this.age = this.life;
    } else {
      // 수면: 세로로 압축된 노이즈 장 + 조수 진동
      const depth = (this.y - hz) / (TL.H - hz);
      const s = params.tideScale;
      const tide = sin(TL.frame * 0.02) * 0.18;
      const a = (noise(this.x * s, this.y * s * 3.2, z) - 0.5) * 1.6 + tide;
      const v = (0.6 + depth * 2.6) * params.drift;
      this.x += cos(a) * v * 1.4;
      this.y += sin(a) * v * 0.25;
      // 물에 비친 현수선(반사)의 약한 인력
      const by = tlReflectY(this.x);
      if (abs(this.y - by) < 22) this.y += (by - this.y) * 0.05;
      if (this.y < hz) this.y = hz + 1;
    }
    this.age++;
    if (this.age > this.life || this.x < -60 || this.x > TL.W + 60 || this.y > TL.H + 10) this.reset(this.sky, false);
    this.draw(pal);
  }

  draw(pal) {
    const hz = TL.H * TL.HORIZON;
    const fade = sin((this.age / this.life) * PI);
    let c, w, a;
    if (this.sky) {
      const d = dist(this.x, this.y, TL.W / 2, hz - 30) / (TL.H * 0.55);
      const onBridge = exp(-pow(this.y - tlBridgeY(this.x), 2) / 40);
      c = lerpColor(lerpColor(pal[1], pal[0], constrain(d * 1.3, 0, 1)), pal[2], onBridge);
      a = (90 * (1 - constrain(d, 0, 1)) + 140 * onBridge) * fade;
      w = 1.6 + onBridge;
    } else {
      const depth = (this.y - hz) / (TL.H - hz);
      const col = exp(-pow(this.x - TL.W / 2, 2) / (2 * pow(40 + depth * 330, 2)));
      const nearBridge = exp(-pow(this.y - tlReflectY(this.x), 2) / 60) * 0.7;
      const lit = constrain(col * (0.7 + 0.3 * sin(TL.frame * 0.3 + this.x)) + nearBridge * 0.8, 0, 1);
      if (lit < params.glintThreshold * 0.4 && random() > 0.35) return;
      c = lerpColor(pal[0], lit > params.glintThreshold ? pal[2] : pal[1], lit);
      a = (25 + 200 * lit) * fade;
      w = 1 + depth * 3.2;
    }
    TL.trails.stroke(red(c), green(c), blue(c), a);
    TL.trails.strokeWeight(w);
    TL.trails.line(this.px, this.py, this.x, this.y);
  }
}

function initializeSystem() {
  randomSeed(params.seed);
  noiseSeed(params.seed);
  TL.frame = 0;
  TL.particles = [];
  const n = params.particleCount;
  for (let i = 0; i < n; i++) TL.particles.push(new TideParticle(i < n * 0.32));
  TL.trails = createGraphics(TL.W, TL.H);
  TL.trails.pixelDensity(1);
  buildBackground();
}

function buildBackground() {
  // 1px 단위 그라데이션 (밴딩 없음). 하늘과 바다를 따로 두어 해가 수평선 아래로 가려지게 한다.
  const pal = tlPalette();
  const hz = Math.round(TL.H * TL.HORIZON);
  TL.sky = createGraphics(TL.W, hz);
  TL.sea = createGraphics(TL.W, TL.H - hz);
  for (const g of [TL.sky, TL.sea]) g.pixelDensity(1);
  for (let y = 0; y < hz; y++) {
    const c = lerpColor(color("#0d1033"), lerpColor(pal[0], pal[1], 0.75), pow(y / hz, 2.0));
    TL.sky.stroke(c);
    TL.sky.line(0, y, TL.W, y);
  }
  for (let y = 0; y < TL.H - hz; y++) {
    const c = lerpColor(lerpColor(pal[0], pal[1], 0.35), color("#070a1f"), pow(y / (TL.H - hz), 0.6));
    TL.sea.stroke(c);
    TL.sea.line(0, y, TL.W, y);
  }
}

function stepSystem() {
  const pal = tlPalette();
  const hz = Math.round(TL.H * TL.HORIZON);
  // 흔적 레이어를 조금씩 지움 (destination-out)
  const ctx = TL.trails.drawingContext;
  ctx.save();
  ctx.globalCompositeOperation = "destination-out";
  ctx.fillStyle = `rgba(0,0,0,${params.trailFade / 255})`;
  ctx.fillRect(0, 0, TL.W, TL.H);
  ctx.restore();
  TL.trails.blendMode(ADD);
  for (const p of TL.particles) p.step(pal);
  TL.trails.blendMode(BLEND);

  // 합성: 하늘 → 해 → 바다 → 빛의 흔적
  blendMode(BLEND);
  image(TL.sky, 0, 0);
  const sunY = hz - 6 - min(TL.frame, 200) * 0.3;
  noStroke();
  for (let r = 150; r > 30; r -= 8) {
    fill(255, 190, 130, 7);
    circle(TL.W / 2, sunY, r * 2);
  }
  fill(255, 238, 205);
  circle(TL.W / 2, sunY, 78);
  image(TL.sea, 0, hz);
  blendMode(ADD);
  image(TL.trails, 0, 0);
  blendMode(BLEND);
  TL.frame++;
}
