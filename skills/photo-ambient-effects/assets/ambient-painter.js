/* Original overlay; seeded periodic twinkle approach adapted from HyperFrames registry starfield. */
(function(global){
'use strict';
function createAmbientPainter(canvas,options={}){
  if(!canvas||typeof canvas.getContext!=='function')throw new Error('Ambient effects need an existing canvas.');
  const ctx=canvas.getContext('2d');
  if(!ctx)throw new Error('Ambient effects need a 2D context.');
  const W=1920,H=1080,TAU=Math.PI*2;
  const rnd=n=>{const v=Math.sin(n*127.1+311.7)*43758.5453;return v-Math.floor(v);};
  const stars=Array.from({length:48},(_,i)=>({x:rnd(i+40)*W,y:35+rnd(i+78)*220,r:1.1+rnd(i+130)*2.4,phase:rnd(i+150)*TAU,cycles:2+Math.floor(rnd(i+200)*3)}));
  const flies=Array.from({length:34},(_,i)=>({x:i%2?1660+rnd(i+810)*210:45+rnd(i+410)*225,y:160+rnd(i+520)*610,r:2.2+rnd(i+540)*2.8,phase:rnd(i+600)*TAU}));
  function glow(x,y,r,color,alpha){const g=ctx.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,`rgba(${color},${alpha})`);g.addColorStop(.18,`rgba(${color},${alpha*.45})`);g.addColorStop(1,`rgba(${color},0)`);ctx.fillStyle=g;ctx.fillRect(x-r,y-r,r*2,r*2);}
  function cross(x,y,r,a){ctx.strokeStyle=`rgba(255,235,183,${a})`;ctx.lineWidth=1.4;ctx.beginPath();ctx.moveTo(x-r,y);ctx.lineTo(x+r,y);ctx.moveTo(x,y-r);ctx.lineTo(x,y+r);ctx.stroke();}
  return function paint(seconds,strength=1){
    if(!Number.isFinite(seconds)||!Number.isFinite(strength)||strength<0)throw new Error('Invalid ambient time or strength.');
    const phase=((seconds%8)+8)%8/8,angle=phase*TAU;
    ctx.clearRect(0,0,canvas.width,canvas.height);if(strength===0)return;ctx.save();ctx.scale(canvas.width/W,canvas.height/H);ctx.globalCompositeOperation='screen';ctx.globalAlpha=strength;
    if(options.glows!==false)glow(15,300,440,'255,185,96',.18+.10*Math.sin(angle));
    if(options.glows!==false)glow(1900,330,480,'255,164,135',.18+.09*Math.sin(angle+2.4));
    if(options.stars!==false)for(const s of stars){const a=.24+.70*Math.pow(.5+.5*Math.sin(angle*s.cycles+s.phase),3);const x=s.x+9*Math.sin(angle+s.phase);glow(x,s.y,s.r*5.5,'255,231,175',a*.8);ctx.fillStyle=`rgba(255,246,213,${a})`;ctx.beginPath();ctx.arc(x,s.y,s.r,0,TAU);ctx.fill();if(s.r>2.7)cross(x,s.y,s.r*2.4,a*.7);}
    if(options.fireflies!==false)for(const f of flies){const x=f.x+52*Math.sin(angle+f.phase),y=f.y+85*Math.cos(angle+f.phase);const a=.30+.65*(.5+.5*Math.sin(angle*3+f.phase));glow(x,y,24,'255,212,121',a*.85);ctx.fillStyle=`rgba(255,243,194,${a})`;ctx.beginPath();ctx.arc(x,y,f.r,0,TAU);ctx.fill();}
    const meteors=[{at:.45,x:110,y:65,dx:540,dy:165},{at:2.6,x:1210,y:34,dx:570,dy:155},{at:4.8,x:260,y:72,dx:480,dy:144},{at:6.6,x:1320,y:60,dx:440,dy:150}];
    if(options.meteors!==false)for(const m of meteors){const u=(phase*8-m.at)/.95;if(u<0||u>1)continue;const a=Math.pow(Math.sin(u*Math.PI),.6),x=m.x+m.dx*u,y=m.y+m.dy*u;const tx=x-m.dx*.31,ty=y-m.dy*.31;const grad=ctx.createLinearGradient(tx,ty,x,y);grad.addColorStop(0,'rgba(255,223,154,0)');grad.addColorStop(.7,`rgba(255,228,169,${a*.65})`);grad.addColorStop(1,`rgba(255,251,222,${a})`);ctx.strokeStyle=grad;ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(tx,ty);ctx.lineTo(x,y);ctx.stroke();glow(x,y,20,'255,232,168',a);cross(x,y,6,a);}
    if(options.sea!==false)for(let side=0;side<2;side++){
      const left=side?1240:25,right=side?1895:655;
      for(let j=0;j<3;j++){ctx.beginPath();for(let x=left;x<=right;x+=10){const y=846+j*56+6*Math.sin(x*.018-angle*(j%2?2:1)+j);if(x===left)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.strokeStyle=`rgba(255,224,168,${.22+.13*Math.sin(angle+j)**2})`;ctx.lineWidth=1.4;ctx.stroke();}
      for(let j=0;j<30;j++){const x=left+30+rnd(j+side*100+900)*(right-left-60),y=820+rnd(j+1100)*195+3*Math.sin(angle+j);const a=.08+.44*Math.pow(.5+.5*Math.sin(angle*2+j*1.7),5);ctx.strokeStyle=`rgba(255,235,184,${a})`;ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+5+rnd(j+1400)*18,y);ctx.stroke();}
    }
    ctx.restore();
  };

}
if(typeof module!=='undefined'&&module.exports)module.exports={createAmbientPainter};
else global.PhotoAmbient={createAmbientPainter};
})(typeof window!=='undefined'?window:globalThis);
