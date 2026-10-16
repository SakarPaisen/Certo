function slugify(text, maxLength = 50) {
  if (typeof text !== 'string') throw new TypeError('text must be a string');
  if (!Number.isInteger(maxLength) || maxLength < 1) {
    throw new RangeError('maxLength must be an integer of at least 1');
  }
  const slug = text
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  if (slug.length <= maxLength) return slug;
  if (slug[maxLength] === '-') return slug.slice(0, maxLength);
  const cut = slug.slice(0, maxLength);
  const lastHyphen = cut.lastIndexOf('-');
  return lastHyphen > 0 ? cut.slice(0, lastHyphen) : cut;
}

module.exports = { slugify };
