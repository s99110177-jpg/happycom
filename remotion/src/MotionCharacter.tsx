import { AbsoluteFill, Easing, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { FONT } from "./fonts";
import type { Today } from "./types";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const INK = "#30365a";

// 해피 갈매기 스프라이트 (Python 에서 각도별로 미리 그린 PNG)
const Gull = ({ wings }: { wings: number[] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const land = spring({ frame, fps, config: { damping: 9, mass: 0.8 } });           // 위에서 통통 떨어짐
  const wave = t > 0.9 ? 35 + 35 * Math.sin(t * 8) : -60;
  const angle = wings.reduce((a, b) => (Math.abs(b - wave) < Math.abs(a - wave) ? b : a), wings[0]);
  const blink = Math.abs(t - 3.9) < 0.07;
  const talking = t > 1.6 && t < 3.0;
  const tag = blink ? "b" : talking && Math.floor(t * 9) % 2 ? "o" : "n";
  const squash = interpolate(land, [0.85, 1, 1.1], [0.92, 1, 1.06], { extrapolateLeft: "clamp", extrapolateRight: "extend" });
  return (
    <Img src={staticFile(`gull/w${angle}_${tag}.png`)} style={{
      position: "absolute", width: 880, height: 720, left: 100, top: 1100,
      translate: `0px ${interpolate(land, [0, 1], [-1300, 0])}px`,
      scale: `${2 - squash} ${squash}`, transformOrigin: "bottom center",
    }} />
  );
};

// 날짜 카드: 3D 로 뒤집히며 등장
const FlipCard = ({ d }: { d: Today }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 110, width: 1080, display: "flex", justifyContent: "center", perspective: 1600 }}>
      <div style={{
        background: "#fff", borderRadius: 40, padding: "30px 70px", border: `8px solid ${INK}`, boxShadow: `0 16px 0 ${INK}`,
        display: "flex", flexDirection: "column", alignItems: "center",
        transform: `rotateX(${interpolate(frame, [0.1 * fps, 0.8 * fps], [-100, 0], { ...clamp, easing: Easing.spring({ damping: 11 }) })}deg)`,
        transformOrigin: "top center",
      }}>
        <div style={{ fontFamily: FONT.round, fontSize: 44, color: INK }}>{d.year}</div>
        <div style={{ fontFamily: FONT.round, fontSize: 120, color: INK, lineHeight: 1.05 }}>{d.month}월 {d.day}일</div>
        <div style={{ fontFamily: FONT.round, fontSize: 64, color: d.week.accent }}>{d.weekday}</div>
      </div>
    </div>
  );
};

const Bubble = ({ text }: { text: string }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = text.replace(/\n/g, "").length;
  const shown = Math.floor(interpolate(frame, [1.6 * fps, 3.0 * fps], [0, total], clamp));
  let left = shown;
  return (
    <div style={{ position: "absolute", top: 720, width: 1080, display: "flex", justifyContent: "center" }}>
      <div style={{
        position: "relative", background: "#fff", border: `8px solid ${INK}`, borderRadius: 60, padding: "36px 60px", minWidth: 560,
        scale: interpolate(frame, [1.2 * fps, 1.6 * fps], [0, 1], { ...clamp, easing: Easing.spring({ damping: 10 }), output: "perceptual-scale" }),
      }}>
        {text.split("\n").map((line, i) => {
          const part = line.slice(0, Math.max(0, left));
          left -= line.length;
          return (
            <div key={i} style={{ fontFamily: FONT.round, fontSize: 70, color: INK, textAlign: "center", lineHeight: 1.3 }}>
              <span>{part}</span><span style={{ visibility: "hidden" }}>{line.slice(part.length)}</span>
            </div>
          );
        })}
        <div style={{ position: "absolute", bottom: -56, left: "46%", width: 0, height: 0, borderLeft: "30px solid transparent",
          borderRight: "30px solid transparent", borderTop: `56px solid ${INK}` }} />
      </div>
    </div>
  );
};

const Hearts = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      {Array.from({ length: 14 }, (_, i) => {
        const t = frame / fps - 1.0 - random(`h${i}`) * 3;
        if (t < 0 || t > 2) return null;
        return <div key={i} style={{ position: "absolute", left: 120 + random(`x${i}`) * 840, top: 1500 - t * 380, fontSize: 60,
          opacity: interpolate(t, [0, 0.2, 1.6, 2], [0, 1, 1, 0]), translate: `${Math.sin(t * 4 + i) * 30}px 0px` }}>
          {["💛", "✨", "🎵", "☀️"][i % 4]}
        </div>;
      })}
    </AbsoluteFill>
  );
};

export const MotionCharacter = (d: Today) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const stripes = `repeating-linear-gradient(45deg, ${d.week.top} 0 60px, ${d.week.bottom} 60px 120px)`;
  return (
    <AbsoluteFill style={{ background: stripes, backgroundPosition: `${frame * 2}px 0px` }}>
      {/* 바닥 원형 무대 */}
      <div style={{ position: "absolute", left: -200, right: -200, top: 1780, height: 600, borderRadius: "50%", background: "#fff",
        border: `10px solid ${INK}` }} />
      <FlipCard d={d} />
      <div style={{ position: "absolute", top: 560, width: 1080, display: "flex", justifyContent: "center" }}>
        <div style={{ fontFamily: FONT.round, fontSize: 52, color: "#fff", background: d.week.accent, padding: "12px 40px", borderRadius: 50,
          border: `6px solid ${INK}`, rotate: "-3deg",
          scale: interpolate(frame, [0.7 * fps, 1.1 * fps], [0, 1], { ...clamp, easing: Easing.spring({ damping: 9 }), output: "perceptual-scale" }) }}>
          {d.tag}
        </div>
      </div>
      <Hearts />
      <Gull wings={d.wings} />
      <Bubble text={d.characterMessage} />
      <AbsoluteFill style={{ background: "#fff", opacity: interpolate(frame, [durationInFrames - 10, durationInFrames], [0, 0.5], clamp) }} />
      <Audio src={staticFile("character.wav")} />
    </AbsoluteFill>
  );
};
