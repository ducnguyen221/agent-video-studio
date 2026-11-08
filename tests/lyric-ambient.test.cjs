// Run: node --test tests/lyric-ambient.test.cjs (no network/browser/media required).
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.join(__dirname, '..', 'skills');
const presets = require(path.join(root, 'lyric-video-effects/assets/lyric-presets.js'));
const {createSunRayPainter} = require(path.join(root, 'photo-ambient-effects/assets/sun-rays.js'));
const {createAmbientPainter} = require(path.join(root, 'photo-ambient-effects/assets/ambient-painter.js'));
function recorder() {
  const ops = [];
  const tl = {fromTo(...v) {ops.push(['fromTo', ...v]);}, to(...v) {ops.push(['to', ...v]);}, set(...v) {ops.push(['set', ...v]);}};
  return {tl, ops};
}
function fakeCanvas() {
  const ops=[];
  const gradient=(...v)=>{ops.push(['gradient',...v]);return {addColorStop(...x){ops.push(['colorStop',...x]);}};};
  const ctx=new Proxy({createRadialGradient:gradient,createLinearGradient:gradient}, {
    get(target,key){return key in target?target[key]:(...v)=>ops.push([key,...v]);},
    set(target,key,v){ops.push(['set',key,typeof v==='object'?'gradient':v]);target[key]=v;return true;}
  });
  return {canvas:{width:1920,height:1080,getContext:()=>ctx},ops};
}
test('script reveal removes settled mask; pulse happens on glyph child',()=>{
  const {tl,ops}=recorder();
  presets.animateWord(tl,{style:'B',word:'mask',glyph:'ink',start:2,duration:.8});
  assert.deepEqual(ops[1].slice(0,3),['set','mask',{clipPath:'none'}]);
  assert.ok(Math.abs(ops[1][3]-2.301)<1e-9);
  assert.equal(ops[2][1],'ink');assert.equal(ops[2][3].scaleX,1.08);
  const pad=presets.inkPadding({fontSize:172,left:31,right:26,ascent:140,descent:40});
  assert.ok(pad.left>31*1.08&&pad.right>26*1.08&&pad.bottom>40*1.035);
  assert.throws(()=>presets.inkPadding({fontSize:0,left:0,right:0,ascent:0,descent:0}));
});
test('ABC only and finite times; C needs graphemes; all four curves settle',()=>{
  const {tl,ops}=recorder();
  for(let variant=0;variant<4;variant++)presets.animateWord(tl,{style:'C',word:'w',glyph:'g',chars:['a','b'],start:1,duration:.6,variant});
  assert.equal(ops.length,8);for(const op of ops){assert.equal(op[3].x,0);assert.equal(op[3].opacity,1);}
  assert.notEqual(ops[0][2].x,ops[2][2].x);
  assert.throws(()=>presets.animateWord(tl,{style:'plain',start:0,duration:1}));
  assert.throws(()=>presets.animateWord(tl,{style:'C',start:0,duration:1}));
  assert.throws(()=>presets.safeScriptReveal(tl,'w',{start:NaN,duration:1}));
  presets.animateWord(tl,{style:'A',word:'w',glyph:'g',start:1,duration:.7});
});
test('last held word is never retired early',()=>{
  const {tl,ops}=recorder();
  assert.equal(presets.retireSungWord(tl,'last',{wordEnd:4,sungEnd:4,isLast:true}),false);
  assert.equal(ops.length,0);
  assert.equal(presets.retireSungWord(tl,'previous',{wordEnd:3,sungEnd:4,isLast:false}),true);
  assert.ok(ops[0][3]>=3.07);
});
test('sun ray clock repeats and changes; zero power clears; invalid inputs fail',()=>{
  const {canvas,ops}=fakeCanvas(),paint=createSunRayPainter(canvas);
  paint(2,1);const a=JSON.stringify(ops);assert.equal(ops.filter(o=>o[0]==='fill').length,20);
  ops.length=0;paint(10,1);assert.equal(JSON.stringify(ops),a);
  ops.length=0;paint(3,1);assert.notEqual(JSON.stringify(ops),a);
  ops.length=0;paint(3,0);assert.deepEqual(ops,[['clearRect',0,0,1920,1080]]);
  assert.throws(()=>paint(NaN));assert.throws(()=>createSunRayPainter(null));
  assert.throws(()=>createSunRayPainter(canvas,{period:0}));
});
test('ambient repeats on seek and independent effect toggles can suppress all ink',()=>{
  const {canvas,ops}=fakeCanvas(),paint=createAmbientPainter(canvas);
  paint(2,.8);const a=JSON.stringify(ops);ops.length=0;paint(10,.8);assert.equal(JSON.stringify(ops),a);
  ops.length=0;paint(4,.8);assert.notEqual(JSON.stringify(ops),a);
  ops.length=0;paint(4,0);assert.equal(ops.length,1);
  const off=createAmbientPainter(canvas,{stars:false,fireflies:false,meteors:false,sea:false,glows:false});
  ops.length=0;off(2);assert.equal(ops.filter(o=>['fill','stroke','fillRect'].includes(o[0])).length,0);
  assert.throws(()=>paint(Infinity));assert.throws(()=>paint(1,-1));assert.throws(()=>createAmbientPainter(null));
});
test('20 opt-in families schedule entrance/exit; invalid family rejected; icons are safe',async()=>{
  const {animateFamilyPhrase}=await import('../skills/lyric-video-effects/assets/motion-families.mjs');
  global.document={querySelectorAll:()=>['letter1','letter2']};
  try {
    for(let n=1;n<=20;n++)for(const exit of [0,.3]){
      const {tl,ops}=recorder();
      const p={index:0,motion:`F${String(n).padStart(2,'0')}`,display_start:1,start:1.1,sung_end:3,
        enter_duration:.25,exit_duration:exit,words:[{text:'Bright',start:1.1,end:1.6,key:true},{text:'days',start:1.7,end:3}],accent:'#ffd877',icon_id:'sun',emphasize:true};
      const locked=recorder();assert.throws(()=>animateFamilyPhrase(locked.tl,p));assert.equal(locked.ops.length,0);
      animateFamilyPhrase(tl,p,{allowExtended:true});assert.ok(ops.length>5);
      for(const op of ops)assert.ok(Number.isFinite(op.at(-1))&&op.at(-1)>=0);
    }
    assert.throws(()=>animateFamilyPhrase(recorder().tl,{motion:'F99'},{allowExtended:true}));
    const short={index:0,motion:'F17',display_start:1,start:1,sung_end:1.18,enter_duration:.25,exit_duration:0,
      words:[{text:'Joy',start:1,end:1.18}],accent:'#ffd877',icon_id:'sun',emphasize:true};
    const capture=recorder();animateFamilyPhrase(capture.tl,short,{allowExtended:true});
    for(const op of capture.ops){const params=op[0]==='fromTo'?op[3]:op[2];if('duration' in params)assert.ok(params.duration>0);}
    const bad=recorder();assert.throws(()=>animateFamilyPhrase(bad.tl,{...short,words:[{text:'Joy',end:1.18}]},{allowExtended:true}));assert.equal(bad.ops.length,0);
    assert.throws(()=>animateFamilyPhrase(bad.tl,{...short,words:[{text:'Joy',start:1,end:2}]},{allowExtended:true}));
  } finally {delete global.document;}
  const {ICON_IDS,iconSVG,iconShapes}=await import('../skills/lyric-video-effects/assets/line-icons.mjs');
  assert.equal(ICON_IDS.length,55);for(const id of ICON_IDS)assert.ok(iconShapes(id).includes('pathLength'));
  assert.ok(iconSVG(ICON_IDS[0],'"<bad>').includes('&quot;&lt;bad&gt;'));
  assert.throws(()=>iconShapes('not-present'));
});
