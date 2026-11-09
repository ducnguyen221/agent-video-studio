/* Caller supplies previously analyzed samples in seconds and composition time. */
(function (global) {
  'use strict';
  function strengthAt(samples, time, max = 1) {
    if (!Array.isArray(samples) || !samples.length || !Number.isFinite(time) || !Number.isFinite(max) || max < 0 || max > 1)
      throw new Error('Invalid envelope or strength limit');
    let previous = -Infinity;
    for (const sample of samples) {
      if (!Number.isFinite(sample.time) || sample.time < 0 || sample.time <= previous || !Number.isFinite(sample.value) || sample.value < 0 || sample.value > 1)
        throw new Error('Envelope samples must be ordered and in range');
      previous = sample.time;
    }
    if (time <= samples[0].time) return samples[0].value * max;
    const last = samples[samples.length - 1];
    if (time >= last.time) return last.value * max;
    const i = samples.findIndex(sample => sample.time >= time);
    const a = samples[i - 1], b = samples[i];
    return (a.value + (b.value - a.value) * (time - a.time) / (b.time - a.time)) * max;
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {strengthAt};
  else global.AmbientEnvelope = {strengthAt};
})(typeof window !== 'undefined' ? window : globalThis);
