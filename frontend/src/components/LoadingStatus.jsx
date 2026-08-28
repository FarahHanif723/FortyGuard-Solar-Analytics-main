import { useEffect, useState } from "react";

const MESSAGES = [
  "Geocoding your locations…",
  "Pulling live temperature & irradiance data…",
  "Calculating heat-adjusted output…",
  "Generating AI recommendation…",
];

export default function LoadingStatus() {
  const [msgIndex, setMsgIndex] = useState(0);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const msgTimer = setInterval(() => {
      setMsgIndex((i) => (i + 1) % MESSAGES.length);
    }, 4000);
    const clock = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => {
      clearInterval(msgTimer);
      clearInterval(clock);
    };
  }, []);

  return (
    <div className="loading-status">
      <div className="loading-spinner"></div>
      <div>
        <div className="loading-msg">{MESSAGES[msgIndex]}</div>
        <div className="loading-sub">
          {seconds}s elapsed — this can take up to 30s per site, it's normal.
        </div>
      </div>
    </div>
  );
}