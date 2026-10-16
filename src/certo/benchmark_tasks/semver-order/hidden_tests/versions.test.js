const test = require('node:test');
const assert = require('node:assert/strict');
const { compareVersions, sortVersions } = require('../versions.js');

test('numeric parts compare as numbers', () => {
  assert.equal(compareVersions('1.0.0', '2.0.0'), -1);
  assert.equal(compareVersions('1.10.0', '1.9.0'), 1);
  assert.equal(compareVersions('1.2.10', '1.2.9'), 1);
  assert.equal(compareVersions('3.1.4', '3.1.4'), 0);
});

test('a prerelease comes before its release', () => {
  assert.equal(compareVersions('1.0.0-alpha', '1.0.0'), -1);
  assert.equal(compareVersions('1.0.0', '1.0.0-rc.1'), 1);
  assert.equal(compareVersions('1.0.1-alpha', '1.0.0'), 1);
});

test('prerelease ordering', () => {
  const ordered = [
    '2.1.0-0',
    '2.1.0-1',
    '2.1.0-2.a',
    '2.1.0-dev',
    '2.1.0-dev.3',
    '2.1.0-dev.20',
    '2.1.0-dev.beta',
    '2.1.0-dev-x',
    '2.1.0-preview',
    '2.1.0',
  ];
  for (let i = 0; i < ordered.length - 1; i++) {
    assert.equal(compareVersions(ordered[i], ordered[i + 1]), -1, `${ordered[i]} < ${ordered[i + 1]}`);
    assert.equal(compareVersions(ordered[i + 1], ordered[i]), 1, `${ordered[i + 1]} > ${ordered[i]}`);
  }
});

test('build metadata and leading v are ignored', () => {
  assert.equal(compareVersions('1.0.0+a', 'v1.0.0+b'), 0);
  assert.equal(compareVersions('1.0.0-rc.1+build.7', '1.0.0-rc.1'), 0);
});

test('invalid versions throw', () => {
  for (const bad of ['1.2', '1.2.x', '01.2.3', '1.02.3', '1.2.3-', '1.2.3-a..b', '1.2.3-01', '1.2.3+', 'version', '1.2.3.4']) {
    assert.throws(() => compareVersions(bad, '1.0.0'), Error, bad);
  }
});

test('sortVersions returns a new sorted array', () => {
  const input = ['1.10.0', '1.2.0', 'v1.9.0', '1.2.0-beta', '0.9.9'];
  const copy = [...input];
  assert.deepEqual(sortVersions(input), ['0.9.9', '1.2.0-beta', '1.2.0', 'v1.9.0', '1.10.0']);
  assert.deepEqual(input, copy);
});
