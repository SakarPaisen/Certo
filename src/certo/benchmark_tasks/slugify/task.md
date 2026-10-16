# Slugify

Write a Node.js module with no dependencies. `package.json` is already
here; keep it CommonJS and keep `npm test` running `node --test`.

## `slugify.js`

Export a function `slugify(text, maxLength = 50)` with
`module.exports = { slugify }`. It turns a title into a URL slug:

- Lower case.
- Accents are removed: `é` becomes `e`, `ü` becomes `u` (decompose with
  `normalize("NFD")` and drop the combining marks).
- Every run of characters that are not `a`-`z` or `0`-`9` becomes one
  hyphen. There are no hyphens at the start or the end.
- If the slug is longer than `maxLength`, shorten it **without cutting a
  word**: keep the longest start of the slug that ends at a word boundary
  and is at most `maxLength` long. Only if the first word alone is longer
  than `maxLength`, cut that word at `maxLength`.
- A title with no letters or digits gives `""`.
- Throw a `TypeError` if `text` is not a string, and a `RangeError` if
  `maxLength` is not an integer of at least 1.

Examples: `"Hello, World!"` → `"hello-world"`;
`slugify("the quick brown fox", 12)` → `"the-quick"`.

Also write tests in `slugify.test.js`, using `node:test` and
`node:assert`.
