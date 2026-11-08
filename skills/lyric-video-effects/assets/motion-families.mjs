/* Original extended lyric recipes. F01..F20 are opt-in; never mix into an ABC-only brief.
 * Browser + GSAP timeline required. DOM contract: #lyric-{index}, .card, .phrase-text,
 * .icon-holder, .lyric-underline, .ink-band; #word-{index}-{j}, #glyph-{index}-{j}, .letter.
 * Input p: index,motion,display_start,start,sung_end,enter_duration,exit_duration,
 * words[{text,start,end,key}],accent,icon_id,emphasize. Caller owns clip visibility.
 * Masked families need the same ink padding / settled mask removal as script B. */
export function animateFamilyPhrase(tl,p,{allowExtended=false,palette={ivory:'#fff7e8',coral:'#ffadab',mint:'#bcebd7'}}={}){
  if(allowExtended!==true)throw new Error('ABC is the default. Extended families require explicit user approval.');
  if(!/^F(0[1-9]|1[0-9]|20)$/.test(p.motion))throw new Error('Unknown lyric motion family.');
  if(!p.words?.length||![p.display_start,p.start,p.sung_end,p.enter_duration,p.exit_duration].every(Number.isFinite)||p.display_start<0||p.start<p.display_start||p.sung_end<p.start||p.enter_duration<=0||p.exit_duration<0)throw new Error('Invalid lyric cue.');
  p.words.forEach((w,j)=>{if(!Number.isFinite(w.start)||!Number.isFinite(w.end)||w.start<p.start||w.end<=w.start||w.end>p.sung_end||(j>0&&w.start<p.words[j-1].end))throw new Error('Invalid word timing.');});
  const ivory=palette.ivory;
    const q=`#lyric-${p.index}`, card=q+' .card', text=q+' .phrase-text', icon=q+' .icon-holder';
    const ws=p.words.map((w,j)=>`#word-${p.index}-${j}`);
    const glyphs=p.words.map((w,j)=>`#glyph-${p.index}-${j}`);
    const a=p.display_start, s=p.start, last=p.sung_end;
    const en=p.enter_duration, dir=p.index%2?1:-1;
    const reveal=(target,from,to,time=a,duration=en)=>{tl.fromTo(target,from,{...to,duration,ease:'power3.out'},time);if(to.clipPath)tl.set(target,{clipPath:'none'},time+duration+.001);};
    // The framework owns .clip visibility; only child elements are animated.
    reveal(card,{opacity:0},{opacity:1},a,Math.min(.12,en));
    reveal(icon,{scale:.94},{scale:1},a,Math.min(.25,en));
    reveal(q+' .lyric-underline',{scaleX:0,opacity:0},{scaleX:1,opacity:0},a,.05);
    reveal(q+' .ink-band',{scaleX:0,opacity:0},{scaleX:1,opacity:0},a,.05);
    const wordRise=(distance=25)=>ws.forEach((w,j)=>reveal(w,{y:distance,opacity:0},{y:0,opacity:1},Math.max(a,p.words[j].start-.075),Math.min(.18,en)));
    switch(p.motion){
      case 'F01':
        reveal(text,{clipPath:'inset(0% 0% 100% 0%)'},{clipPath:'inset(0% 0% 0% 0%)'},a,en);
        wordRise(22);break;
      case 'F02':
        ws.forEach((w,j)=>reveal(w,{x:(j-(ws.length-1)/2)*13,opacity:0},{x:0,opacity:1},a+Math.min(.08,j*.012),en));
        break;
      case 'F03':
        reveal(text,{x:dir*48,clipPath:`inset(0% ${dir>0?100:0}% 0% ${dir>0?0:100}%)`},{x:0,clipPath:'inset(0% 0% 0% 0%)'},a,en);break;
      case 'F04':
        reveal(text,{filter:'blur(5px)',scale:.97},{filter:'blur(0px)',scale:1},a,en);break;
      case 'F05':
        tl.fromTo(text,{scale:.88},{scale:1,duration:Math.min(.34,en*1.25),ease:'back.out(1.25)'},a);break;
      case 'F06':
        ws.forEach((w,j)=>reveal(w,{x:j%2?-26:26,rotation:j%2?-2:2,opacity:0},{x:0,rotation:0,opacity:1},a+j*.012,en));
        break;
      case 'F07':
        reveal(text,{clipPath:'inset(0% 100% 0% 0%)'},{clipPath:'inset(0% 0% 0% 0%)'},a,en);
        reveal(q+' .ink-band',{scaleX:0,opacity:.8},{scaleX:1,opacity:.8},a,en);
        break;
      case 'F08':
        reveal(text,{x:-50,y:10},{x:0,y:0},a,en);
        reveal(icon,{x:-20,rotation:-5},{x:0,rotation:0},a,en);break;
      case 'F09':
        ws.forEach((w,j)=>reveal(w,{opacity:0,clipPath:'inset(0% 100% 0% 0%)'},{opacity:1,clipPath:'inset(0% 0% 0% 0%)'},Math.max(a,p.words[j].start-.04),Math.min(.12,en)));
        break;
      case 'F10':
        ws.forEach((w,j)=>reveal(w,{y:-9-20*Math.sin((j+1)/(ws.length+1)*Math.PI),rotation:(j-(ws.length-1)/2)*.8,opacity:0},{y:0,rotation:0,opacity:1},a+j*.015,en));
        break;
      case 'F11':
        reveal(text,{clipPath:'circle(0% at 50% 50%)',scale:.93},{clipPath:'circle(100% at 50% 50%)',scale:1},a,en);break;
      case 'F12':
        ws.forEach((w,j)=>reveal(w,{rotationX:-55,transformPerspective:800,opacity:0},{rotationX:0,opacity:1},a+j*.015,en));
        break;
      case 'F13':
        ws.forEach((w,j)=>reveal(w,{x:j<ws.length/2?-40:40,opacity:0},{x:0,opacity:1},a,en));break;
      case 'F14':
        ws.forEach((w,j)=>reveal(w,{y:j<ws.length/2?-24:24,opacity:0},{y:0,opacity:1},a+j*.012,en));
        reveal(q+' .lyric-underline',{scaleX:0,opacity:.7},{scaleX:1,opacity:.7},a,en);break;
      case 'F15':
        reveal(text,{y:-24},{y:0},a,en);
        reveal(icon,{y:-14},{y:0},a,en*1.1);break;
      case 'F16':
        reveal(q+' .lyric-underline',{scaleX:0,opacity:.85},{scaleX:1,opacity:.85},a,en*1.2);
        reveal(text,{clipPath:'inset(0% 100% 0% 0%)'},{clipPath:'inset(0% 0% 0% 0%)'},a,en);break;
      case 'F17':
        reveal(text,{scale:.82,y:14},{scale:1,y:0},a,en);
        if(p.emphasize&&last-a-en>0)reveal(text,{scale:1},{scale:1.055},a+en,Math.min(.5,last-a-en));
        break;
      case 'F18':
        reveal(text,{textShadow:`-3px 0 ${palette.coral},3px 0 ${palette.mint},0 3px 10px #111724`,x:dir*10},{textShadow:'0px 0px transparent,0px 0px transparent,0 3px 10px #111724',x:0},a,en);break;
      case 'F19':
        ws.forEach(w=>{const letters=document.querySelectorAll(w+' .letter');letters.forEach((el,j)=>reveal(el,{x:(j-(letters.length-1)/2)*-1.6,opacity:.2},{x:0,opacity:1},a,en*1.1));});break;
      case 'F20':
        ws.forEach((w,j)=>reveal(w,{y:8,opacity:0},{y:0,opacity:1},a+j*.018,Math.min(.26,en)));
        reveal(q+' .lyric-underline',{scaleX:0,opacity:.7},{scaleX:1,opacity:.7},a,en*1.2);break;
      default:throw new Error('Unimplemented motion '+p.motion);
    }
    const ink=q+' .icon-ink [pathLength]';
    tl.fromTo(ink,{strokeDasharray:'1 1',strokeDashoffset:1},{strokeDashoffset:0,duration:Math.min(.28,(last-a)*.35),stagger:.006,ease:'power1.out'},a);
    const pulseAt=s+Math.min(.5,(last-s)*.35);
    if(/heart|sun|smile|embrace|growing|confetti/.test(p.icon_id)){
      tl.fromTo(icon,{scale:1},{scale:1.045,duration:.16,ease:'sine.out'},pulseAt);
      tl.to(icon,{scale:1,duration:.3,ease:'sine.inOut'},pulseAt+.16);
    }
    p.words.forEach((w,j)=>{
      const key=Boolean(w.key);
      tl.fromTo(glyphs[j],{color:ivory},{color:p.accent,duration:.045,ease:'none'},w.start);
      if(w.end+.07<last)tl.to(glyphs[j],{color:key?p.accent:ivory,duration:.13,ease:'none'},w.end+.025);
      if(key&&w.end-w.start>.25){
        tl.fromTo(glyphs[j],{scale:1},{scale:1.035,duration:.14,ease:'power2.out'},w.start);
        tl.to(glyphs[j],{scale:1,duration:.18,ease:'sine.inOut'},Math.min(last-.18,w.start+.2));
      }
    });
    // An adjacent sung phrase can leave no exit gap. Keep the last word intact;
    // the next clip then replaces it rather than cutting its vowel early.
    const ex=p.exit_duration;
    if(ex<=.025){
      // In connected singing, retire already-sung words during the final held
      // word. That final word stays intact until the next vocal phrase.
      ws.slice(0,-1).forEach((target,j)=>{
        const st=Math.max(last-.22,p.words[j].end+.06),duration=Math.min(.18,last-st);
        if(duration<.065)return;
        const family=Number(p.motion.slice(1))%5;
        const pose=family===0?{y:-12,opacity:0}:family===1?{x:dir*15,opacity:0}:family===2?{scale:.92,opacity:0}:family===3?{rotation:dir*3,y:-6,opacity:0}:{clipPath:'inset(0% 0% 100% 0%)',opacity:0};
        tl.to(target,{...pose,duration,ease:'power2.in'},st);
      });
    }
    if(ex>.025){
      const st=last;
      const opts={duration:ex,ease:'power2.in'};
      switch(p.motion){
        case 'F01':tl.to(text,{y:-16,clipPath:'inset(0% 0% 100% 0%)',...opts},st);break;
        case 'F02':ws.forEach((w,j)=>tl.to(w,{x:(j-(ws.length-1)/2)*8,opacity:0,...opts},st));break;
        case 'F03':tl.to(text,{x:-dir*25,clipPath:'inset(0% 100% 0% 0%)',...opts},st);break;
        case 'F04':tl.to(text,{filter:'blur(3px)',opacity:0,...opts},st);break;
        case 'F05':tl.to(text,{scale:.96,opacity:0,...opts},st);break;
        case 'F06':ws.forEach((w,j)=>tl.to(w,{x:j%2?18:-18,y:-8,opacity:0,...opts},st));break;
        case 'F07':tl.to(text,{clipPath:'inset(0% 0% 0% 100%)',...opts},st);break;
        case 'F08':tl.to(text,{x:30,opacity:0,...opts},st);break;
        case 'F09':tl.to(ws,{opacity:0,duration:ex*.65,stagger:-ex*.35/Math.max(1,ws.length-1)},st);break;
        case 'F10':tl.to(ws,{y:-12,opacity:0,duration:ex*.65,stagger:ex*.35/Math.max(1,ws.length-1)},st);break;
        case 'F11':tl.to(text,{clipPath:'circle(0% at 50% 50%)',...opts},st);break;
        case 'F12':tl.to(ws,{rotationX:30,opacity:0,...opts},st);break;
        case 'F13':tl.to(text,{scale:.96,opacity:0,...opts},st);break;
        case 'F14':tl.to(ws,{y:-20,opacity:0,duration:ex*.7,stagger:ex*.3/Math.max(1,ws.length-1)},st);break;
        case 'F15':tl.to(text,{clipPath:'inset(0% 50% 0% 50%)',...opts},st);break;
        case 'F16':tl.to(q+' .lyric-underline',{scaleX:0,...opts},st);tl.to(text,{opacity:0,...opts},st);break;
        case 'F17':tl.to(text,{scale:.92,y:-10,opacity:0,...opts},st);break;
        case 'F18':tl.to(text,{textShadow:`-2px 0 ${p.accent},2px 0 ${palette.coral}`,opacity:0,...opts},st);break;
        case 'F19':ws.forEach(w=>{const letters=document.querySelectorAll(w+' .letter');letters.forEach((el,j)=>tl.to(el,{x:(j-(letters.length-1)/2)*1.6,opacity:0,...opts},st));});break;
        case 'F20':tl.to(ws,{opacity:0,duration:ex*.6,stagger:ex*.4/Math.max(1,ws.length-1)},st);break;
      }
      tl.to(icon,{opacity:0,duration:ex*.8,ease:'sine.in'},st+ex*.2);
    }

}
