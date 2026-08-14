// A completion chime for turns long enough that the user has wandered off.
// Synthesized with Web Audio so the app ships no audio asset and stays offline.

const SOUND_KEY = "nurb-completion-sound";
const LONG_TASK_MS = 8000;

export function shouldPlayCompletionChime(completed: boolean, elapsedMs: number): boolean {
  return completed && elapsedMs > LONG_TASK_MS;
}

export function soundEnabled(): boolean {
  return localStorage.getItem(SOUND_KEY) !== "off";
}

export function setSoundEnabled(on: boolean) {
  if (on) localStorage.removeItem(SOUND_KEY);
  else localStorage.setItem(SOUND_KEY, "off");
}

let ctx: AudioContext | null = null;

export function playChime() {
  if (!soundEnabled()) return;
  try {
    ctx ??= new AudioContext();
    // WKWebView leaves a context created outside a user gesture suspended.
    if (ctx.state === "suspended") void ctx.resume();
    const now = ctx.currentTime;
    // A bouncy C-major arpeggio, video-game "ta-da!": triangle waves read as
    // toy-like rather than doorbell, and the last note gets to ring out.
    for (const [freq, at, hold] of [
      [784, 0, 0.18],
      [1046.5, 0.08, 0.18],
      [1318.5, 0.16, 0.18],
      [1568, 0.24, 0.6],
    ] as const) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "triangle";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0, now + at);
      gain.gain.linearRampToValueAtTime(0.14, now + at + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + at + hold);
      osc.connect(gain).connect(ctx.destination);
      osc.start(now + at);
      osc.stop(now + at + hold + 0.1);
    }
  } catch {
    // No audio device is never worth an error in the chat.
  }
}
