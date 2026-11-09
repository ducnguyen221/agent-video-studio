/* Original periodic dust overlay; caller masks protected subjects/text separately. */
(function (global) {
  'use strict';
  function createDustPainter(canvas) {
    if (!canvas || typeof canvas.getContext !== 'function') throw new Error('Canvas required');
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('2D context required');
    return function paint(time, strength = 1) {
      if (!Number.isFinite(time) || !Number.isFinite(strength) || strength < 0 || strength > 1) throw new Error('Invalid dust parameters');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (!strength) return;
      ctx.save();
      for (let i = 0; i < 24; i++) {
        const phase = 2 * Math.PI * (time / 8 + i / 24);
        const x = canvas.width * ((i * 37 % 101) / 101 + .012 * Math.sin(phase));
        const y = canvas.height * ((i * 53 % 103) / 103 + .02 * Math.cos(phase));
        ctx.globalAlpha = strength * (.08 + .12 * (.5 + .5 * Math.sin(phase)));
        ctx.fillStyle = '#fff4da'; ctx.beginPath(); ctx.arc(x, y, 1 + i % 3, 0, 2 * Math.PI); ctx.fill();
      }
      ctx.restore();
    };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {createDustPainter};
  else global.AmbientDust = {createDustPainter};
})(typeof window !== 'undefined' ? window : globalThis);
