import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// export_remotion.py 가 시스템의 나눔 폰트를 public/fonts 로 복사한다
export const FONT = { round: "HappyRound", bold: "HappyBold", serif: "HappySerif", pen: "HappyPen" } as const;

export const fontsReady = Promise.all([
  loadFont({ family: FONT.round, url: staticFile("fonts/round.ttf") }),
  loadFont({ family: FONT.bold, url: staticFile("fonts/bold.ttf") }),
  loadFont({ family: FONT.serif, url: staticFile("fonts/serif.ttf") }),
  loadFont({ family: FONT.pen, url: staticFile("fonts/pen.ttf") }),
]);
