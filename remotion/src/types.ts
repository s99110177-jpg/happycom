export type Today = {
  date: string; year: number; month: number; day: number;
  weekday: string; weekdayShort: string; weekdayEn: string; koreanDate: string;
  message: string; characterMessage: string; tag: string;
  anniversary: {
    name: string; desc: string; emoji: string; solemn: boolean; upcoming: boolean;
    dday: number | null; others: string[]; colors: [string, string, string];
  };
  week: { top: string; bottom: string; accent: string };
  wings: number[];
};

// 미리보기용 기본값 (실제 렌더는 public/today.json 을 --props 로 넘긴다)
export const SAMPLE: Today = {
  date: "2026-11-20", year: 2026, month: 11, day: 20, weekday: "금요일", weekdayShort: "금",
  weekdayEn: "FRIDAY", koreanDate: "2026년 11월 20일 금요일",
  message: "괜찮아요,\n오늘도 잘 될 거예요", characterMessage: "행복 가득\n배달 왔어요!", tag: "신나는 금요일!",
  anniversary: {
    name: "세계 어린이의 날", desc: "어린이의 권리를\n생각하는 날", emoji: "🧒", solemn: false, upcoming: false,
    dday: null, others: [], colors: ["#fbe278", "#fa9f3c", "#ffffe6"],
  },
  week: { top: "#ffecc8", bottom: "#fffae6", accent: "#f05a8c" },
  wings: [-60, -50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
};
