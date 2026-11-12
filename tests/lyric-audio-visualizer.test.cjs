'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {createAudioVisualizer} = require('../skills/lyric-video-effects/assets/audio-visualizer.js');

function canvas(){
  const calls=[];
  const ctx=new Proxy({}, {get(o,k){ if(!(k in o)) o[k]=(...args)=>calls.push([k,...args]); return o[k]}, set(o,k,v){calls.push(['set',k,v]);o[k]=v;return true}});
  return {width:800,height:400,getContext:()=>ctx,calls};
}
const input=()=>({spectrum:{frames:[[0,0.5],[1,0],[0,1]],sampleRate:10,hopSamples:10,offset:2},wordCues:[{start:0.2},{start:0.4}],region:{x:10,y:20,width:600,height:300},noteDuration:1});

test('seeking a second time produces identical draw commands without accumulated state',()=>{
  const c=canvas(), paint=createAudioVisualizer(c,input()); paint(2.5); const expected=c.calls.splice(0); paint(3.1); c.calls.length=0; paint(2.5); assert.deepEqual(c.calls,expected);
});
test('spectrum offsets and boundaries interpolate, outside range is silent',()=>{
  const paint=createAudioVisualizer(canvas(),input());
  assert.deepEqual(paint(1.9).bands,[0,0]); assert.deepEqual(paint(2).bands,[0,0.5]);
  assert.deepEqual(paint(2.5).bands,[0.5,0.25]); assert.deepEqual(paint(4).bands,[0,1]); assert.deepEqual(paint(4.01).bands,[0,0]);
});
test('each word cue emits exactly one note, affected by offset and lifetime',()=>{
 const paint=createAudioVisualizer(canvas(),input());
 assert.equal(paint(2.1).notes.length,0); assert.equal(paint(2.3).notes.length,1);
 assert.equal(paint(2.5).notes.length,2); assert.equal(paint(3.2).notes.length,1); assert.equal(paint(3.4).notes.length,0);
});
test('rejects invalid analyzed data and does not accept bad cue order',()=>{
 const a=input(); a.spectrum.frames[0][0]=NaN; assert.throws(()=>createAudioVisualizer(canvas(),a),/spectrum/i);
 const b=input(); b.wordCues=[{start:2},{start:1}]; assert.throws(()=>createAudioVisualizer(canvas(),b),/cue/i);
 const d=input(); d.spectrum.hopSamples=0; assert.throws(()=>createAudioVisualizer(canvas(),d),/spectrum/i);
 const e=input(); e.region.width=0; assert.throws(()=>createAudioVisualizer(canvas(),e),/region/i);
});
test('rejects missing frames and missing frequency values before drawing',()=>{
 const a=input(); a.spectrum.frames=[[0,,1],[1,1,1]];
 assert.throws(()=>createAudioVisualizer(canvas(),a),/spectrum/i);
 const b=input(); b.spectrum.frames=new Array(3); b.spectrum.frames[0]=[0,0.5];
 assert.throws(()=>createAudioVisualizer(canvas(),b),/spectrum/i);
 const c=input(); c.wordCues=[,{start:0.2}];
 assert.throws(()=>createAudioVisualizer(canvas(),c),/cue/i);
});
test('takes an immutable snapshot of inputs and validates time',()=>{
 const a=input(), paint=createAudioVisualizer(canvas(),a); a.spectrum.frames[0][0]=1;a.wordCues[0].start=8;
 assert.equal(paint(2).bands[0],0);assert.equal(paint(2.3).notes.length,1);assert.throws(()=>paint(NaN),/time/i);
});

test('custom ring size and position fit within the clipping region',()=>{
 const opts=input(); Object.assign(opts,{ringRadius:35,maxBarLength:50,centerX:200,centerY:150});
 const result=createAudioVisualizer(canvas(),opts)(2.5);
 assert.deepEqual(result.ring,{centerX:200,centerY:150,radius:35,maxBarLength:50});
 const invalid=input();Object.assign(invalid,{ringRadius:35,maxBarLength:50,centerX:20,centerY:150});
 assert.throws(()=>createAudioVisualizer(canvas(),invalid),/fit region/i);
 const negative=input();negative.maxBarLength=-1;assert.throws(()=>createAudioVisualizer(canvas(),negative),/dimensions/i);
 const huge=input();huge.ringRadius=200;assert.throws(()=>createAudioVisualizer(canvas(),huge),/fit region/i);
});

test('rejects a ring position that leaves no visible space for flying notes',()=>{
 const a=input();Object.assign(a,{ringRadius:35,maxBarLength:1,centerX:570,centerY:150});
 assert.throws(()=>createAudioVisualizer(canvas(),a),/note path/i);
 const b=input();Object.assign(b,{ringRadius:35,maxBarLength:1,centerX:570,centerY:150,wordCues:[]});
 assert.doesNotThrow(()=>createAudioVisualizer(canvas(),b));
});
