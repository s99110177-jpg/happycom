// public/today.json 을 props 로 넘겨 세 컴포지션을 렌더한다.
// 사용: node render.mjs [출력폴더]   (먼저 python -m morning_video.export_remotion)
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync } from "node:fs";

const data = JSON.parse(readFileSync("public/today.json", "utf8"));
const out = process.argv[2] ?? `../output/${data.date}`;
mkdirSync(out, { recursive: true });
const stamp = data.date.replaceAll("-", "");
const browser = ["/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell"]
  .concat(process.env.REMOTION_BROWSER ? [process.env.REMOTION_BROWSER] : [])
  .find((p) => existsSync(p));
const jobs = [["MotionBusan", "1_busan_m"], ["MotionAnniversary", "2_anniversary_m"], ["MotionCharacter", "3_character_m"]];
for (const [id, name] of jobs) {
  const args = ["remotion", "render", "src/index.ts", id, `${out}/${stamp}_${name}.mp4`, "--props=public/today.json",
    "--codec=h264", "--pixel-format=yuv420p", "--log=error"];
  if (browser) args.push(`--browser-executable=${browser}`);
  console.log("▶", id);
  execFileSync("npx", args, { stdio: "inherit" });
}
