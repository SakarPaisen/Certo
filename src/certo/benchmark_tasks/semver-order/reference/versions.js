const PATTERN = /^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$/;

function parse(text) {
  const match = typeof text === 'string' ? PATTERN.exec(text) : null;
  if (!match) throw new Error(`invalid version: ${text}`);
  const pre = match[4] ? match[4].split('.') : [];
  for (const id of pre) {
    if (/^\d+$/.test(id) && id.length > 1 && id[0] === '0') {
      throw new Error(`invalid version: ${text}`);
    }
  }
  return { nums: [match[1], match[2], match[3]].map(Number), pre };
}

function cmp(x, y) {
  return x < y ? -1 : x > y ? 1 : 0;
}

function compareIds(a, b) {
  const an = /^\d+$/.test(a);
  const bn = /^\d+$/.test(b);
  if (an && bn) return cmp(Number(a), Number(b));
  if (an) return -1;
  if (bn) return 1;
  return cmp(a, b);
}

function compareVersions(a, b) {
  const x = parse(a);
  const y = parse(b);
  for (let i = 0; i < 3; i++) {
    const c = cmp(x.nums[i], y.nums[i]);
    if (c) return c;
  }
  if (!x.pre.length && !y.pre.length) return 0;
  if (!x.pre.length) return 1;
  if (!y.pre.length) return -1;
  for (let i = 0; i < Math.min(x.pre.length, y.pre.length); i++) {
    const c = compareIds(x.pre[i], y.pre[i]);
    if (c) return c;
  }
  return cmp(x.pre.length, y.pre.length);
}

function sortVersions(list) {
  return [...list].sort(compareVersions);
}

module.exports = { compareVersions, sortVersions };
