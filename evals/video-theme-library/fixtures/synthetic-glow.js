// Synthetic, self-contained test component. No dependencies or personal data.
export function glowOpacity(time, strength = 0.5) {
  return Math.max(0, Math.min(1, strength * (0.5 + 0.5 * Math.sin(time))));
}
