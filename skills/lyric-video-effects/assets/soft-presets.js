/* Original finite GSAP lyric entrances. The caller owns timeline and cue timing. */
(function (global) {
  'use strict';
  function schedule(timeline, element, options) {
    const {preset, start, duration} = options;
    if (!timeline || !element || !Number.isFinite(start) || start < 0 || !Number.isFinite(duration) || duration <= 0)
      throw new Error('Invalid lyric element or timing');
    const from = {
      'soft-rise': {opacity: 0, y: 18},
      'focus-in': {opacity: 0, filter: 'blur(4px)', scale: .98}
    }[preset];
    if (!from) throw new Error('Unknown lyric preset');
    const to = preset === 'soft-rise' ? {opacity: 1, y: 0} : {opacity: 1, filter: 'blur(0px)', scale: 1};
    timeline.fromTo(element, from, {...to, duration, ease: 'power2.out'}, start);
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {schedule};
  else global.LyricNewPresets = {schedule};
})(typeof window !== 'undefined' ? window : globalThis);
