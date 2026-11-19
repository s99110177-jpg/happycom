import { AbsoluteFill, Easing, interpolate, random, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { FONT } from "./fonts";
import type { Today } from "./types";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// 색 패널 3장이 차례로 쓸고 지나가며 배경을 채움
const Panels = ({ colors, solemn }: { colors: string[]; solemn: boolean }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const list = solemn ? ["#2b3044", "#1b1f30", "#10131f"] : [colors[2], colors[0], colors[1]];
  return (
    <AbsoluteFill>
      {list.map((c, i) => (
        <AbsoluteFill key={i} style={{
          background: i === 2 ? `linear-gradient(160deg, ${list[1]} 0%, ${c} 100%)` : c,
          translate: interpolate(frame, [i * 0.12 * fps, (i * 0.12 + 0.45) * fps], ["0px 1920px", "0px 0px"],
            { ...clamp, easing: Easing.bezier(0.7, 0, 0.2, 1) }),
        }} />
      ))}
    </AbsoluteFill>
  );
};

const Rays = ({ solemn }: { solemn: boolean }) => {
  const frame = useCurrentFrame();
  const n = 18;
  return (
    <svg width={1400} height={1400} viewBox="-700 -700 1400 1400"
      style={{ position: "absolute", left: -160, top: 60, rotate: `${frame * (solemn ? 0.1 : 0.4)}deg`, opacity: solemn ? 0.08 : 0.18 }}>
      {Array.from({ length: n }, (_, k) => {
        const a0 = (k / n) * Math.PI * 2, a1 = a0 + Math.PI / n;
        return <polygon key={k} points={`0,0 ${700 * Math.cos(a0)},${700 * Math.sin(a0)} ${700 * Math.cos(a1)},${700 * Math.sin(a1)}`} fill="#fff" />;
      })}
    </svg>
  );
};

// 제목: 글자가 하나씩 떨어지며 튕김
const KineticTitle = ({ text, start, solemn }: { text: string; start: number; solemn: boolean }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const chars = [...text];
  const size = Math.min(150, Math.floor(920 / Math.max(6, chars.length * 0.95)));
  return (
    <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", width: 960, rowGap: 10 }}>
      {chars.map((c, i) => {
        const s = start * fps + i * 2;
        return (
          <span key={i} style={{
            fontFamily: FONT.round, fontSize: size, color: "#fff", lineHeight: 1.1, whiteSpace: "pre",
            textShadow: "0 8px 0 rgba(0,0,0,0.18)",
            opacity: interpolate(frame, [s, s + 6], [0, 1], clamp),
            translate: interpolate(frame, [s, s + 20], [solemn ? "0px 30px" : "0px -260px", "0px 0px"],
              { ...clamp, easing: solemn ? Easing.bezier(0.2, 0.8, 0.2, 1) : Easing.spring({ damping: 9 }) }),
            rotate: interpolate(frame, [s, s + 20], [solemn ? "0deg" : `${(random(i) - 0.5) * 50}deg`, "0deg"],
              { ...clamp, easing: Easing.spring({ damping: 9 }) }),
          }}>{c}</span>
        );
      })}
    </div>
  );
};

const Confetti = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const colors = ["#ffffff", "#ffe066", "#ff7aa2", "#7ad7ff", "#9bf6a3"];
  return (
    <AbsoluteFill>
      {Array.from({ length: 70 }, (_, i) => {
        const t = frame / fps - 1.0 - random(`d${i}`) * 1.2;
        if (t < 0) return null;
        const x = random(`x${i}`) * 1080 + Math.sin(t * 3 + i) * 40;
        const y = -40 + t * (300 + random(`v${i}`) * 300) + 120 * t * t;
        return <div key={i} style={{ position: "absolute", left: x, top: y, width: 18, height: 10, background: colors[i % 5],
          rotate: `${t * 400 * (random(`r${i}`) - 0.5)}deg`, scale: `${Math.abs(Math.cos(t * 5 + i))} 1` }} />;
      })}
    </AbsoluteFill>
  );
};

export const MotionAnniversary = (d: Today) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const a = d.anniversary;
  const pop = (s: number) => ({ ...clamp, easing: Easing.spring({ damping: a.solemn ? 200 : 10 }) });
  return (
    <AbsoluteFill style={{ background: "#111" }}>
      <Panels colors={a.colors} solemn={a.solemn} />
      <Rays solemn={a.solemn} />
      {/* 날짜 */}
      <div style={{ position: "absolute", top: 150, width: 1080, display: "flex", justifyContent: "center" }}>
        <div style={{ fontFamily: FONT.round, fontSize: 48, color: a.solemn ? "#e8e8f0" : "#3a2a1a", background: "rgba(255,255,255,0.75)",
          padding: "16px 44px", borderRadius: 60,
          scale: interpolate(frame, [0.5 * fps, 0.9 * fps], [0, 1], { ...pop(0), output: "perceptual-scale" }),
          ...(a.solemn ? { background: "rgba(255,255,255,0.12)" } : {}) }}>
          {d.koreanDate}
        </div>
      </div>
      <div style={{ position: "absolute", top: 300, width: 1080, textAlign: "center", fontFamily: FONT.bold, fontSize: 46, letterSpacing: 10,
        color: "#fff", opacity: interpolate(frame, [0.7 * fps, 1.0 * fps], [0, 1], clamp) }}>
        {a.upcoming ? "다가오는 기념일" : "오늘은"}
      </div>
      {/* 이모지: 스프링 확대 + 흔들림 */}
      <div style={{ position: "absolute", top: 400, width: 1080, display: "flex", justifyContent: "center" }}>
        <div style={{ width: 340, height: 340, borderRadius: "50%", background: a.solemn ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.9)",
          display: "flex", alignItems: "center", justifyContent: "center", fontSize: 210, boxShadow: "0 20px 60px rgba(0,0,0,0.18)",
          scale: interpolate(frame, [0.8 * fps, 1.4 * fps], [0, 1], { ...pop(0), output: "perceptual-scale" }),
          rotate: `${a.solemn ? 0 : Math.sin(frame / 8) * 6}deg` }}>
          {a.emoji}
        </div>
      </div>
      <div style={{ position: "absolute", top: 820, width: 1080, display: "flex", justifyContent: "center" }}>
        <KineticTitle text={a.name} start={1.3} solemn={a.solemn} />
      </div>
      {a.upcoming && a.dday !== null && (
        <div style={{ position: "absolute", top: 1100, width: 1080, textAlign: "center", fontFamily: FONT.bold, fontSize: 140, color: "#fff" }}>
          D-{Math.round(interpolate(frame, [1.8 * fps, 2.6 * fps], [30, a.dday], { ...clamp, easing: Easing.bezier(0.2, 0.8, 0.2, 1) }))}
        </div>
      )}
      <div style={{ position: "absolute", top: a.upcoming ? 1290 : 1130, width: 1080, textAlign: "center", fontFamily: FONT.round, fontSize: 56,
        color: "#fff", lineHeight: 1.45, whiteSpace: "pre-line",
        opacity: interpolate(frame, [2.1 * fps, 2.6 * fps], [0, 1], clamp),
        translate: interpolate(frame, [2.1 * fps, 2.6 * fps], ["0px 30px", "0px 0px"], clamp) }}>
        {a.desc}
      </div>
      {a.others.length > 0 && (
        <div style={{ position: "absolute", top: 1480, width: 1080, display: "flex", flexWrap: "wrap", gap: 16, justifyContent: "center" }}>
          {a.others.map((o, i) => (
            <div key={o} style={{ fontFamily: FONT.round, fontSize: 36, color: "#fff", border: "3px solid rgba(255,255,255,0.8)",
              padding: "8px 26px", borderRadius: 40,
              scale: interpolate(frame, [(2.6 + i * 0.15) * fps, (3.0 + i * 0.15) * fps], [0, 1], { ...pop(0), output: "perceptual-scale" }) }}>
              {o}
            </div>
          ))}
        </div>
      )}
      {!a.solemn && <Confetti />}
      <AbsoluteFill style={{ background: a.solemn ? "#000" : "#fff", opacity: interpolate(frame, [durationInFrames - 10, durationInFrames], [0, 0.45], clamp) }} />
      <Audio src={staticFile("anniversary.wav")} />
    </AbsoluteFill>
  );
};
