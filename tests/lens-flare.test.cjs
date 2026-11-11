const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createLensFlarePainter} = require('../skills/photo-ambient-effects/assets/lens-flare.js');

test('flare is deterministic across backward seek and loops', () => {
  let stops=[];
  const ctx={clearRect(){stops=[]},save(){},restore(){},fillRect(){},
    createRadialGradient(){return {addColorStop(pos,value){stops.push([pos,value])}}}};
  const paint=createLensFlarePainter({width:1920,height:1080,getContext(){return ctx}});
  paint(0.5);const first=JSON.stringify(stops);paint(1.5);assert.notEqual(JSON.stringify(stops),first);
  paint(0.5);assert.equal(JSON.stringify(stops),first);paint(8.5);assert.equal(JSON.stringify(stops),first);
  assert.throws(()=>paint(NaN),/finite/);
  assert.throws(()=>createLensFlarePainter({getContext(){return ctx}}, {period:0}),/options/);
});
