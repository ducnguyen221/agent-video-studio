/* Original ABC lyric adaptations. GSAP and the composition clock are caller-owned.
 * No fonts, media or licensed template code are bundled. */
(function (global) {
  'use strict';
  const STYLES = Object.freeze(['A', 'B', 'C']);
  function requireTiming(start, duration) {
    if (!Number.isFinite(start) || start < 0 || !Number.isFinite(duration) || duration <= 0)
      throw new Error('Lyric start must be nonnegative and duration positive.');
  }
  function inkPadding({fontSize, left = 0, right = 0, ascent, descent, scaleX = 1.08, scaleY = 1.035}) {
    if (![fontSize, left, right, ascent, descent, scaleX, scaleY].every(Number.isFinite) ||
        fontSize <= 0 || ascent < 0 || descent < 0 || scaleX < 1 || scaleY < 1)
      throw new Error('Supply finite font metrics and pulse scales >= 1.');
    const safety = fontSize * .08;
    return {left: Math.max(fontSize * .44, Math.abs(left) * scaleX + safety),
      right: Math.max(fontSize * .44, Math.abs(right) * scaleX + safety),
      top: Math.max(fontSize * .25, ascent * (scaleY - 1) + safety),
      bottom: Math.max(fontSize * .36, descent * scaleY + safety)};
  }
  function safeScriptReveal(tl, word, {start, duration}) {
    requireTiming(start, duration);
    tl.fromTo(word, {clipPath: 'inset(0% 100% 0% 0%)', opacity: 0},
      {clipPath: 'inset(0% 0% 0% 0%)', opacity: 1, duration, ease: 'power1.out'}, start);
    // Keep the mask only while writing. A zero inset still clips cursive ink.
    tl.set(word, {clipPath: 'none'}, start + duration + .001);
  }
  function animateWord(tl, {style, word, glyph, chars = [], start, duration, index = 0, variant = 0, amplitude = 1}) {
    requireTiming(start, duration);
    if (!STYLES.includes(style)) throw new Error('Use one of the approved styles A, B, C.');
    if (!Number.isInteger(variant) || variant < 0 || variant > 3 || !Number.isFinite(amplitude))
      throw new Error('Invalid curve variant or amplitude.');
    if (style === 'A') {
      tl.fromTo(word, {y: 18, rotation: index % 2 ? -3 : 3, scale: .94, opacity: 0},
        {y: 0, rotation: 0, scale: 1, opacity: 1, duration: Math.min(.26, duration * .5), ease: 'back.out(1.15)'}, start);
      tl.fromTo(glyph, {rotation: 0}, {rotation: index % 2 ? -.7 : .7, duration: .12, yoyo: true, repeat: 1, ease: 'sine.inOut'}, start + .12);
    } else if (style === 'B') {
      safeScriptReveal(tl, word, {start, duration: Math.min(.3, duration * .65)});
      if (duration > .3) {
        tl.fromTo(glyph, {scaleX: 1, scaleY: 1}, {scaleX: 1.08, scaleY: 1.035, duration: .15, ease: 'sine.out'}, start + .06);
        tl.to(glyph, {scaleX: 1, scaleY: 1, duration: .22, ease: 'sine.inOut'}, start + .21);
      }
    } else {
      if (!chars.length) throw new Error('Style C needs grapheme elements.');
      const stagger = Math.min(.026, duration * .28 / chars.length);
      chars.forEach((el, k) => {
        const poses = [{x: 22 + k * 2, y: 40 + 10 * Math.sin(k), rotation: 18 + k * 2},
          {x: -24 - k * 1.8, y: -30 - 8 * Math.cos(k), rotation: -18 - k * 1.5},
          {x: 30 * Math.sin(k * .6), y: 48 + 10 * Math.cos(k), rotation: 10 * Math.sin(k)},
          {x: 24 * Math.cos(k * .7), y: 35 + 12 * Math.sin(k * .5), rotation: -12 + 4 * k}];
        const p = poses[variant];
        tl.fromTo(el, {x: p.x * amplitude, y: p.y * amplitude, rotation: p.rotation * amplitude, opacity: 0},
          {x: 0, y: 0, rotation: 0, opacity: 1, duration: Math.min(.28, duration * .65), ease: 'power3.out'}, start + k * stagger);
      });
    }
  }
  function retireSungWord(tl, target, {wordEnd, sungEnd, isLast, style = 'C'}) {
    if (![wordEnd, sungEnd].every(Number.isFinite) || wordEnd < 0 || sungEnd < wordEnd)
      throw new Error('Invalid vocal endpoints.');
    if (!STYLES.includes(style)) throw new Error('Unknown lyric style.');
    if (isLast) return false;
    const start = Math.max(wordEnd + .07, sungEnd - .32), duration = Math.min(.24, sungEnd - start);
    if (duration <= .075) return false;
    tl.to(target, {y: style === 'C' ? 30 : -10, rotation: style === 'C' ? -14 : 0,
      opacity: 0, duration, ease: 'power2.in'}, start);
    return true;
  }
  const api = {STYLES, inkPadding, safeScriptReveal, animateWord, retireSungWord};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else global.LyricPresets = api;
})(typeof window !== 'undefined' ? window : globalThis);
