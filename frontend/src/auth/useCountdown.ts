import { useEffect, useState } from 'react';

export function useCountdown(targetTime: number | null) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    if (targetTime === null) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [targetTime]);

  return targetTime === null ? 0 : Math.max(0, Math.ceil((targetTime - now) / 1000));
}
