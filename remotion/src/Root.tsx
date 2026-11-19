import { Composition } from "remotion";
import "./fonts";
import { MotionBusan } from "./MotionBusan";
import { MotionAnniversary } from "./MotionAnniversary";
import { MotionCharacter } from "./MotionCharacter";
import { SAMPLE } from "./types";

// 9:16, 30fps, 5.5초
const common = { width: 1080, height: 1920, fps: 30, durationInFrames: 165, defaultProps: SAMPLE } as const;

export const Root = () => (
  <>
    <Composition id="MotionBusan" component={MotionBusan} {...common} />
    <Composition id="MotionAnniversary" component={MotionAnniversary} {...common} />
    <Composition id="MotionCharacter" component={MotionCharacter} {...common} />
  </>
);
