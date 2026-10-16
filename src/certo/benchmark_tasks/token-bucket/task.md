# Token bucket rate limiter

Write a Node.js module with no dependencies. `package.json` is already
here; keep it CommonJS and keep `npm test` running `node --test`.

## `tokenBucket.js`

Export a class `TokenBucket` with `module.exports = { TokenBucket }`.

`new TokenBucket({ capacity, refillPerSecond, now })`

- `capacity`: an integer of at least 1, the most tokens the bucket holds.
- `refillPerSecond`: a number greater than 0. Tokens are added
  continuously at this rate, and may be fractional internally.
- `now`: optional function returning the current time in milliseconds;
  defaults to `Date.now`. Tests pass a fake clock.
- The bucket starts full.
- Throw a `RangeError` for an invalid `capacity` or `refillPerSecond`.

Methods:

- `available()`: the number of whole tokens available now
  (`Math.floor` of the current amount, after refilling).
- `tryTake(n = 1)`: if at least `n` tokens are available now, take them and
  return `true`; otherwise take nothing and return `false`. `n` must be an
  integer between 1 and `capacity`; otherwise throw a `RangeError`.

Refilling: before answering, add `refillPerSecond × seconds passed since
the last refill`, never going above `capacity`. If the clock goes
backwards, treat it as no time passing (never remove tokens).

Also write tests in `tokenBucket.test.js`, using `node:test` and
`node:assert`.
