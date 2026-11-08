/* Original deterministic sun-shaft overlay. Canvas coordinates are scaled from
 * a 1920x1080 design space; the caller owns the composition clock. */
(function(global){
  'use strict';
  function createSunRayPainter(canvas,options={}){
    if(!canvas||typeof canvas.getContext!=='function')throw new Error('Sun rays need an existing canvas. Initialize after the DOM.');
    const ctx=canvas.getContext('2d');
    if(!ctx)throw new Error('Sun rays require a 2D canvas context.');
    const origin=options.origin||[1840,-75],direction=options.direction??2.13,period=options.period??8;
    const color=options.color||[255,233,174],strength=options.strength??1;
    if(!(period>0)||!Number.isFinite(strength))throw new Error('Invalid sun-ray period or strength.');
    return function paint(seconds,power=1){
      if(!Number.isFinite(seconds)||!Number.isFinite(power))throw new Error('Sun-ray time and power must be finite.');
      const phase=((seconds%period)+period)%period/period,turn=phase*Math.PI*2;
      ctx.clearRect(0,0,canvas.width,canvas.height);
      if(power<=0)return;
      ctx.save();ctx.scale(canvas.width/1920,canvas.height/1080);ctx.globalCompositeOperation='screen';
      const [ox,oy]=origin,alpha=Math.min(1,Math.max(0,power*strength));
      for(let i=-2;i<=2;i++){
        const angle=direction+i*.115+.027*Math.sin(turn+i*.7),length=1680;
        const dx=Math.cos(angle),dy=Math.sin(angle),nx=-dy,ny=dx;
        const light=.78+.22*Math.sin(turn+i*1.2);
        for(let layer=3;layer>=0;layer--){
          const half=.018+layer*.010,farWidth=Math.tan(half)*length;
          const endX=ox+dx*length,endY=oy+dy*length;
          const grad=ctx.createLinearGradient(ox,oy,endX,endY);
          const a=alpha*light*[.17,.09,.045,.022][layer];
          grad.addColorStop(0,`rgba(${color.join(',')},${a*.35})`);
          grad.addColorStop(.18,`rgba(${color.join(',')},${a})`);
          grad.addColorStop(.72,`rgba(${color.join(',')},${a*.55})`);
          grad.addColorStop(1,`rgba(${color.join(',')},0)`);
          ctx.fillStyle=grad;ctx.beginPath();ctx.moveTo(ox-nx*7,oy-ny*7);ctx.lineTo(endX-nx*farWidth,endY-ny*farWidth);ctx.lineTo(endX+nx*farWidth,endY+ny*farWidth);ctx.lineTo(ox+nx*7,oy+ny*7);ctx.closePath();ctx.fill();
        }
      }
      const halo=ctx.createRadialGradient(ox,oy,0,ox,oy,290);halo.addColorStop(0,`rgba(${color.join(',')},${.32*alpha})`);halo.addColorStop(1,`rgba(${color.join(',')},0)`);ctx.fillStyle=halo;ctx.fillRect(ox-290,oy-290,580,580);
      ctx.restore();
    };
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={createSunRayPainter};
  else global.PhotoSunRays={createSunRayPainter};
})(typeof window!=='undefined'?window:globalThis);
