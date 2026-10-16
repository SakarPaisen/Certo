const test = require('node:test');
const assert = require('node:assert/strict');
const { TokenBucket } = require('../tokenBucket.js');

function clock(start = 1000) {
  const c = { t: start, now: () => c.t, advance: (ms) => { c.t += ms; } };
  return c;
}

test('starts full', () => {
  const c = clock();
  const b = new TokenBucket({ capacity: 5, refillPerSecond: 1, now: c.now });
  assert.equal(b.available(), 5);
});

test('takes until empty, then refuses', () => {
  const c = clock();
  const b = new TokenBucket({ capacity: 3, refillPerSecond: 1, now: c.now });
  assert.equal(b.tryTake(), true);
  assert.equal(b.tryTake(2), true);
  assert.equal(b.tryTake(), false);
  assert.equal(b.available(), 0);
});

test('a refused take takes nothing', () => {
  const c = clock();
  const b = new TokenBucket({ capacity: 4, refillPerSecond: 1, now: c.now });
  assert.equal(b.tryTake(3), true);
  assert.equal(b.tryTake(2), false);
  assert.equal(b.tryTake(1), true);
});

test('refills over time and is capped at capacity', () => {
  const c = clock();
  const b = new TokenBucket({ capacity: 5, refillPerSecond: 2, now: c.now });
  b.tryTake(5);
  c.advance(1000);
  assert.equal(b.available(), 2);
  c.advance(60_000);
  assert.equal(b.available(), 5);
});

test('fractional refill accumulates', () => {
  const c = clock();
  const b = new TokenBucket({ capacity: 2, refillPerSecond: 0.5, now: c.now });
  b.tryTake(2);
  c.advance(1000);
  assert.equal(b.tryTake(), false);
  c.advance(1000);
  assert.equal(b.tryTake(), true);
});

test('refill is measured from the last refill, not double counted', () => {
  const c = clock();
  const b = new TokenBucket({ capacity: 10, refillPerSecond: 1, now: c.now });
  b.tryTake(10);
  c.advance(3000);
  assert.equal(b.available(), 3);
  assert.equal(b.available(), 3);
  c.advance(1000);
  assert.equal(b.available(), 4);
});

test('a clock going backwards removes nothing', () => {
  const c = clock(10_000);
  const b = new TokenBucket({ capacity: 3, refillPerSecond: 1, now: c.now });
  b.tryTake(1);
  c.advance(-5000);
  assert.equal(b.available(), 2);
  assert.equal(b.tryTake(2), true);
  assert.equal(b.available(), 0);
  c.advance(60_000);
  assert.equal(b.available(), 3);
});

test('invalid arguments', () => {
  const c = clock();
  assert.throws(() => new TokenBucket({ capacity: 0, refillPerSecond: 1, now: c.now }), RangeError);
  assert.throws(() => new TokenBucket({ capacity: 2.5, refillPerSecond: 1, now: c.now }), RangeError);
  assert.throws(() => new TokenBucket({ capacity: 2, refillPerSecond: 0, now: c.now }), RangeError);
  const b = new TokenBucket({ capacity: 2, refillPerSecond: 1, now: c.now });
  assert.throws(() => b.tryTake(3), RangeError);
  assert.throws(() => b.tryTake(0), RangeError);
  assert.throws(() => b.tryTake(1.5), RangeError);
});

test('uses Date.now by default', () => {
  const b = new TokenBucket({ capacity: 1, refillPerSecond: 1 });
  assert.equal(b.tryTake(), true);
});
