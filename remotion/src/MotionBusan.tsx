import { AbsoluteFill, Easing, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { FONT } from "./fonts";
import type { Today } from "./types";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const HOR = 1180;

const Sky = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const sunY = interpolate(frame, [0, durationInFrames], [1250, 1020], { ...clamp, easing: Easing.bezier(0.33, 0, 0.2, 1) });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(#141c4a 0%, #3b3a86 30%, #c4607a 55%, #ffb27a 62%, #ffd7a0 63%)" }} />
      <div style={{ position: "absolute", left: 540 - 520, top: sunY - 520, width: 1040, height: 1040, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(255,214,150,0.75) 0%, rgba(255,160,110,0.25) 40%, rgba(255,140,100,0) 70%)" }} />
      <div style={{ position: "absolute", left: 540 - 95, top: sunY - 95, width: 190, height: 190, borderRadius: "50%",
        background: "#fff4d6", boxShadow: "0 0 80px 30px rgba(255,220,160,0.8)" }} />
    </AbsoluteFill>
  );
};

// 건물이 아래에서 차례로 솟아오르는 스카이라인
const Skyline = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const blds = [
    [20, 260], [70, 380], [118, 520], [170, 470], [222, 430], [270, 300], [330, 210], [390, 160],
    [760, 180], [820, 240], [880, 330], [940, 280], [1000, 360],
  ];
  return (
    <AbsoluteFill>
      {blds.map(([x, h], i) => (
        <div key={i} style={{
          position: "absolute", left: x, width: 46, height: h, top: HOR - h, background: "#4a3e7a",
          borderRadius: "10px 10px 0 0", transformOrigin: "bottom",
          scale: `1 ${interpolate(frame, [0.15 * fps + i * 2, 0.9 * fps + i * 2], [0, 1], { ...clamp, easing: Easing.spring({ damping: 14 }) })}`,
        }} />
      ))}
    </AbsoluteFill>
  );
};

// 광안대교: 선이 그려지듯 나타남
const Bridge = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const draw = interpolate(frame, [0.4 * fps, 1.8 * fps], [1, 0], { ...clamp, easing: Easing.bezier(0.65, 0, 0.35, 1) });
  const deck = 1110, top = 860, t1 = 300, t2 = 780;
  const cable = `M -40 ${deck - 10} Q ${(t1 - 40) / 2} ${deck - 40} ${t1} ${top} Q ${(t1 + t2) / 2} ${deck + 120} ${t2} ${top} Q ${(t2 + 1120) / 2} ${deck - 40} 1120 ${deck - 10}`;
  const hangers = Array.from({ length: 40 }, (_, k) => 30 + k * 26);
  const cableY = (x: number) => {
    if (x < t1) return deck - 10 - (deck - 10 - top) * (x / t1) ** 1.8;
    if (x > t2) return deck - 10 - (deck - 10 - top) * ((1080 - x) / (1080 - t2)) ** 1.8;
    const u = (x - t1) / (t2 - t1);
    return top + (deck - 30 - top) * 4 * u * (1 - u);
  };
  const hangerOpacity = interpolate(frame, [1.4 * fps, 2 * fps], [0, 1], clamp);
  return (
    <svg width={1080} height={1920} style={{ position: "absolute" }}>
      {[t1, t2].map((x) => (
        <g key={x} opacity={interpolate(frame, [0.3 * fps, 0.8 * fps], [0, 1], clamp)}>
          <rect x={x - 26} y={top} width={10} height={HOR - top + 30} fill="#1d1838" />
          <rect x={x + 16} y={top} width={10} height={HOR - top + 30} fill="#1d1838" />
          <rect x={x - 26} y={top + 20} width={52} height={10} fill="#1d1838" />
          <rect x={x - 26} y={top + 130} width={52} height={10} fill="#1d1838" />
        </g>
      ))}
      <path d={cable} fill="none" stroke="#1d1838" strokeWidth={6} pathLength={1} strokeDasharray={1} strokeDashoffset={draw} />
      {hangers.map((x) => (
        <line key={x} x1={x} x2={x} y1={cableY(x)} y2={deck - 8} stroke="#1d1838" strokeWidth={2} opacity={hangerOpacity} />
      ))}
      <rect x={0} y={deck - 8} width={1080 * (1 - draw)} height={22} fill="#1d1838" />
      {Array.from({ length: 30 }, (_, k) => (
        <circle key={k} cx={18 + k * 36} cy={deck + 2} r={3} fill="#ffe2a8"
          opacity={interpolate(frame, [1.6 * fps + k, 1.9 * fps + k], [0, 1], clamp)} />
      ))}
    </svg>
  );
};

const Waves = () => {
  const frame = useCurrentFrame();
  const layers = [
    { y: HOR, amp: 8, len: 160, speed: 1.2, color: "#f0a38c" },
    { y: HOR + 120, amp: 14, len: 240, speed: -1.6, color: "#7a5a9a" },
    { y: HOR + 330, amp: 20, len: 320, speed: 2.0, color: "#3d3a7c" },
    { y: HOR + 560, amp: 26, len: 420, speed: -2.4, color: "#1f2456" },
  ];
  return (
    <svg width={1080} height={1920} style={{ position: "absolute" }}>
      {layers.map((l, i) => {
        const pts: string[] = [];
        for (let x = 0; x <= 1080; x += 20) {
          pts.push(`${x},${l.y + l.amp * Math.sin((x / l.len) * Math.PI * 2 + (frame / 30) * l.speed)}`);
        }
        return <polygon key={i} points={`0,1920 ${pts.join(" ")} 1080,1920`} fill={l.color} />;
      })}
      {/* 윤슬 */}
      {Array.from({ length: 26 }, (_, k) => {
        const y = HOR + 30 + ((k * 53) % 600);
        const w = 20 + (k % 5) * 14;
        const x = 540 + Math.sin(k * 7.3) * (60 + (y - HOR) * 0.35);
        const a = 0.5 + 0.5 * Math.sin(frame / 5 + k);
        return <rect key={k} x={x - w / 2} y={y} width={w} height={4} rx={2} fill="#ffe8c4" opacity={a} />;
      })}
    </svg>
  );
};

// 글자 단위 스프링 등장
const Words = ({ text, start, size, color, font, gap = 1.35 }: { text: string; start: number; size: number; color: string; font: string; gap?: number }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  let idx = 0;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: size * (gap - 1) }}>
      {text.split("\n").map((line, li) => (
        <div key={li} style={{ display: "flex", gap: size * 0.28 }}>
          {line.split(" ").map((w, wi) => {
            const k = idx++;
            const s = start * fps + k * 4;
            return (
              <span key={wi} style={{
                fontFamily: font, fontSize: size, color, lineHeight: 1, textShadow: "0 6px 24px rgba(10,10,40,0.55)",
                opacity: interpolate(frame, [s, s + 8], [0, 1], clamp),
                translate: interpolate(frame, [s, s + 18], ["0px 40px", "0px 0px"], { ...clamp, easing: Easing.spring({ damping: 12 }) }),
                rotate: interpolate(frame, [s, s + 18], ["-8deg", "0deg"], { ...clamp, easing: Easing.spring({ damping: 12 }) }),
              }}>{w}</span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

const DateBlock = ({ d }: { d: Today }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 120, width: 1080, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ fontFamily: FONT.bold, fontSize: 34, letterSpacing: 14, color: "#ffd9b0",
        opacity: interpolate(frame, [0, 10], [0, 1], clamp) }}>GOOD MORNING · BUSAN</div>
      <div style={{ display: "flex", alignItems: "center", gap: 30, marginTop: 10 }}>
        <div style={{ overflow: "hidden", height: 250 }}>
          <div style={{ fontFamily: FONT.bold, fontSize: 250, color: "#fff", lineHeight: 1,
            translate: interpolate(frame, [0.1 * fps, 0.7 * fps], ["0px 260px", "0px 0px"], { ...clamp, easing: Easing.spring({ damping: 15 }) }) }}>
            {String(d.day).padStart(2, "0")}
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {[`${d.year}년 ${d.month}월`, d.weekday].map((s, i) => (
            <div key={i} style={{
              fontFamily: FONT.round, fontSize: i ? 60 : 44, color: i ? "#2a2357" : "#fff",
              background: i ? "#ffd27a" : "rgba(255,255,255,0.16)", padding: "10px 26px", borderRadius: 40,
              scale: interpolate(frame, [(0.45 + i * 0.15) * fps, (0.85 + i * 0.15) * fps], [0, 1], { ...clamp, easing: Easing.spring({ damping: 10 }), output: "perceptual-scale" }),
            }}>{s}</div>
          ))}
        </div>
      </div>
    </div>
  );
};

export const MotionBusan = (d: Today) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: "#141c4a" }}>
      <Sky />
      <Skyline />
      <Waves />
      <Bridge />
      <DateBlock d={d} />
      <div style={{ position: "absolute", top: 520, width: 1080 }}>
        <Words text={d.message} start={1.2} size={74} color="#ffffff" font={FONT.serif} />
      </div>
      <div style={{ position: "absolute", bottom: 90, width: 1080, textAlign: "center", fontFamily: FONT.round, fontSize: 38,
        color: "#ffe2c0", opacity: interpolate(frame, [2.2 * fps, 2.8 * fps], [0, 1], clamp) }}>부산 · 광안대교의 아침</div>
      <AbsoluteFill style={{ background: "#fff", opacity: interpolate(frame, [durationInFrames - 10, durationInFrames], [0, 0.5], clamp) }} />
      <Sequence><Audio src={staticFile("busan.wav")} /></Sequence>
    </AbsoluteFill>
  );
};
