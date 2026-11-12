/* Deterministic audio visualization from previously analyzed samples and word cue times.
 * No media decoding, audio recording, ASR, or live audio analysis occurs here.
 * Use a dedicated canvas: every paint clears that canvas. Regions protect layout only;
 * the caller must mask faces/text when the region intersects them. */
(function (global) {
  'use strict';
  function finite(value) { return Number.isFinite(value); }
  function createAudioVisualizer(canvas, options) {
    if (!canvas || typeof canvas.getContext !== 'function' || !finite(canvas.width) || !finite(canvas.height) || canvas.width <= 0 || canvas.height <= 0)
      throw new Error('Invalid canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas needs a 2D context');
    if (!options || !options.spectrum) throw new Error('Invalid spectrum');
    const {frames, sampleRate, hopSamples, offset = 0} = options.spectrum;
    if (!Array.isArray(frames) || !frames.length || !Array.isArray(frames[0]) || !frames[0].length ||
        !finite(sampleRate) || sampleRate <= 0 || !Number.isInteger(hopSamples) || hopSamples <= 0 || !finite(offset))
      throw new Error('Invalid spectrum metadata');
    const bandsCount = frames[0].length;
    const data = Array.from(frames, frame => {
      if (!Array.isArray(frame) || frame.length !== bandsCount || Array.from(frame).some(value => !finite(value) || value < 0 || value > 1))
        throw new Error('Invalid spectrum frame');
      return frame.slice();
    });
    const region = options.region;
    if (!region || !['x','y','width','height'].every(k => finite(region[k])) || region.x < 0 || region.y < 0 || region.width <= 0 || region.height <= 0 || region.x + region.width > canvas.width || region.y + region.height > canvas.height)
      throw new Error('Invalid region');
    const rect = {...region};
    if (!Array.isArray(options.wordCues)) throw new Error('Invalid word cues');
    let previous = -Infinity;
    const cues = Array.from(options.wordCues, cue => {
      if (!cue || !finite(cue.start) || cue.start < 0 || cue.start < previous) throw new Error('Invalid word cue time or order');
      previous = cue.start;
      return cue.start;
    });
    const noteDuration = options.noteDuration === undefined ? 2 : options.noteDuration;
    const barCount = options.barCount === undefined ? 64 : options.barCount;
    const hueStart = options.hueStart === undefined ? 35 : options.hueStart;
    const hueRate = options.hueRate === undefined ? 16 : options.hueRate;
    if (!finite(noteDuration) || noteDuration <= 0 || !Number.isInteger(barCount) || barCount < 4 || barCount > 512 || !finite(hueStart) || !finite(hueRate))
      throw new Error('Invalid visualizer options');
    const glyphs = ['♪', '♫', '♩'];
    const radius = options.ringRadius === undefined ? Math.min(rect.width * 0.095, rect.height * 0.24) : options.ringRadius;
    const maxBar = options.maxBarLength === undefined ? radius * 0.9 : options.maxBarLength;
    if (!finite(radius) || radius <= 0 || !finite(maxBar) || maxBar <= 0) throw new Error('Invalid ring dimensions');
    // Account for the radial gap and half of the bar stroke in the bounds.
    const extent = radius + 3 + maxBar + Math.max(1, radius * 0.04) / 2;
    if (extent * 2 > rect.width || extent * 2 > rect.height) throw new Error('Ring does not fit region');
    const cx = options.centerX === undefined ? rect.x + Math.max(extent, Math.min(rect.width * 0.24, rect.width - extent)) : options.centerX;
    const cy = options.centerY === undefined ? rect.y + rect.height * 0.5 : options.centerY;
    if (!finite(cx) || !finite(cy) || cx - extent < rect.x || cx + extent > rect.x + rect.width || cy - extent < rect.y || cy + extent > rect.y + rect.height)
      throw new Error('Ring does not fit region');
    const fontSize = Math.max(12, radius * 0.45);
    const noteStartX = cx + radius + 5;
    const noteEndX = rect.x + rect.width - fontSize;
    if (cues.length && noteEndX - noteStartX < fontSize) throw new Error('Note path does not fit region');
    function paint(time) {
      if (!finite(time)) throw new Error('Invalid time');
      const audioTime = time - offset;
      const sample = audioTime * sampleRate / hopSamples;
      let values = new Array(bandsCount).fill(0);
      if (sample >= 0 && sample <= data.length - 1) {
        const i = Math.floor(sample), j = Math.min(i + 1, data.length - 1), fraction = sample - i;
        values = data[i].map((value, band) => value + (data[j][band] - value) * fraction);
      }
      const hue = ((hueStart + hueRate * time) % 360 + 360) % 360;
      const notes = [];
      for (let i = 0; i < cues.length; i++) {
        const age = audioTime - cues[i];
        if (age < -1e-9 || age >= noteDuration - 1e-9) continue;
        const phase = cues[i] * 2.7 + i * 2.4;
        const progress = Math.max(0, age) / noteDuration;
        const x = noteStartX + progress * (noteEndX - noteStartX);
        const y = cy + ((i % 7) - 3) * radius * 0.18 + Math.sin(age * 4.2 + phase) * radius * 0.34 + Math.sin(age * 1.9 + phase * 0.6) * radius * 0.25;
        notes.push({cueIndex:i, x, y, alpha:Math.pow(1 - progress, 1.15), glyph:glyphs[i % glyphs.length]});
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save(); ctx.beginPath(); ctx.rect(rect.x, rect.y, rect.width, rect.height); ctx.clip();
      ctx.fillStyle = 'rgba(5,12,22,.43)'; ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = `hsla(${hue},85%,73%,.9)`; ctx.lineWidth = Math.max(1, radius * 0.04);
      ctx.shadowColor = `hsl(${hue},90%,65%)`; ctx.shadowBlur = radius * 0.2;
      ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.stroke(); ctx.shadowBlur = 0;
      for (let i = 0; i < barCount; i++) {
        const band = Math.floor((i % Math.ceil(barCount / 2)) * bandsCount / Math.ceil(barCount / 2));
        const angle = i * Math.PI * 2 / barCount - Math.PI / 2;
        const length = maxBar * (0.16 + 0.84 * values[band]);
        const start = radius + 3, end = start + length;
        ctx.strokeStyle = `hsla(${(hue + 32 * Math.sin(angle) + 360) % 360},88%,70%,.95)`;
        ctx.lineWidth = Math.max(1, radius * 0.04); ctx.beginPath();
        ctx.moveTo(cx + Math.cos(angle) * start, cy + Math.sin(angle) * start);
        ctx.lineTo(cx + Math.cos(angle) * end, cy + Math.sin(angle) * end); ctx.stroke();
      }
      for (const note of notes) {
        const noteHue = (hue + note.cueIndex * 22) % 360;
        ctx.fillStyle = `hsla(${noteHue},88%,75%,${note.alpha})`;
        ctx.font = `${fontSize}px Segoe UI Symbol, sans-serif`;
        ctx.shadowColor = `hsla(${noteHue},90%,65%,${note.alpha})`; ctx.shadowBlur = radius * 0.14;
        ctx.fillText(note.glyph, note.x, note.y);
      }
      ctx.restore();
      return {bands:values, notes, ring:{centerX:cx, centerY:cy, radius, maxBarLength:maxBar}};
    }
    return paint;
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {createAudioVisualizer};
  else global.LyricAudioVisualizer = {createAudioVisualizer};
})(typeof window !== 'undefined' ? window : globalThis);
