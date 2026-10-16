const test = require('node:test');
const assert = require('node:assert/strict');
const { slugify } = require('../slugify.js');

test('basic title', () => {
  assert.equal(slugify('Hello, World!'), 'hello-world');
});

test('accents are removed', () => {
  assert.equal(slugify('  Crème brûlée  '), 'creme-brulee');
  assert.equal(slugify('Über Café'), 'uber-cafe');
});

test('runs of other characters become one hyphen', () => {
  assert.equal(slugify('a--b__c  d'), 'a-b-c-d');
  assert.equal(slugify("C'est l'été"), 'c-est-l-ete');
  assert.equal(slugify('--Hello--'), 'hello');
});

test('digits are kept', () => {
  assert.equal(slugify('Top 10 Tips for 2026'), 'top-10-tips-for-2026');
});

test('nothing usable gives an empty string', () => {
  assert.equal(slugify('***'), '');
  assert.equal(slugify(''), '');
});

test('shortening does not cut a word', () => {
  assert.equal(slugify('the quick brown fox', 12), 'the-quick');
  assert.equal(slugify('the quick brown fox', 9), 'the-quick');
  assert.equal(slugify('the quick brown fox', 10), 'the-quick');
  assert.equal(slugify('the quick brown', 15), 'the-quick-brown');
});

test('a first word longer than maxLength is cut', () => {
  assert.equal(slugify('supercalifragilistic word', 5), 'super');
});

test('default maxLength is 50', () => {
  const title = 'word '.repeat(20);
  const slug = slugify(title);
  assert.ok(slug.length <= 50);
  assert.equal(slug, Array(10).fill('word').join('-'));
});

test('bad arguments', () => {
  assert.throws(() => slugify(42), TypeError);
  assert.throws(() => slugify('a', 0), RangeError);
  assert.throws(() => slugify('a', 2.5), RangeError);
});
