/* Original synthetic lens flare. The caller supplies composition time. */
(function(global){
  'use strict';
  function createLensFlarePainter(canvas, options={}) {
    if(!canvas || typeof canvas.getContext!=='function') throw new Error('Lens flare requires a canvas');
    const ctx=canvas.getContext('2d');
    if(!ctx) throw new Error('Lens flare requires a 2D context');
    const period=options.period ?? 8, strength=options.strength ?? 0.5;
    if(!Number.isFinite(period)||period<=0||!Number.isFinite(strength)||strength<0||strength>1) throw new Error('Invalid lens flare options');
    return function paint(seconds){
      if(!Number.isFinite(seconds)) throw new Error('Lens flare time must be finite');
      const phase=((seconds%period)+period)%period/period, pulse=0.85+0.15*Math.cos(2*Math.PI*phase);
      ctx.clearRect(0,0,canvas.width,canvas.height); ctx.save(); ctx.globalCompositeOperation='screen';
      for (const [x,y,r,a] of [[.87,.1,.13,.7],[.63,.34,.065,.22],[.4,.57,.045,.16]]) {
        const cx=x*canvas.width,cy=y*canvas.height,radius=r*Math.min(canvas.width,canvas.height);
        const g=ctx.createRadialGradient(cx,cy,0,cx,cy,radius);
        g.addColorStop(0,`rgba(255,224,165,${a*strength*pulse})`);g.addColorStop(1,'rgba(255,224,165,0)');
        ctx.fillStyle=g;ctx.fillRect(cx-radius,cy-radius,2*radius,2*radius);
      }
      ctx.restore();
    };
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={createLensFlarePainter};
  else global.PhotoLensFlare={createLensFlarePainter};
})(typeof window!=='undefined'?window:globalThis);
