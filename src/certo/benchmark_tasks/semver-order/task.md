# Version ordering

Write a Node.js module with no dependencies. `package.json` is already
here; keep it CommonJS and keep `npm test` running `node --test`.

## `versions.js`

Export `compareVersions(a, b)` and `sortVersions(list)` with
`module.exports = { compareVersions, sortVersions }`.

A version looks like `MAJOR.MINOR.PATCH`, optionally followed by
`-PRERELEASE` and then optionally `+BUILD`, with an optional leading `v`:
`1.4.2`, `v2.0.0-rc.1`, `1.0.0-beta+exp.sha.5114f85`.

- MAJOR, MINOR and PATCH are non-negative integers with no leading zeros
  (`0` is fine, `01` is not).
- PRERELEASE and BUILD are dot-separated identifiers made of `0-9`,
  `A-Z`, `a-z` and `-`. No identifier may be empty. A numeric prerelease
  identifier must not have leading zeros.
- Anything else is invalid: throw an `Error`.

`compareVersions(a, b)` returns `-1`, `0` or `1`:

1. Compare MAJOR, then MINOR, then PATCH, as numbers (so `1.10.0` is
   after `1.9.0`).
2. If those are equal, a version **with** a prerelease comes **before**
   the same version without one: `1.0.0-alpha` < `1.0.0`.
3. Two prereleases are compared identifier by identifier, left to right:
   two numeric identifiers as numbers; two others as strings in ASCII
   order; a numeric identifier comes before a non-numeric one. If all
   compared identifiers are equal, the one with fewer identifiers comes
   first.
4. BUILD and the leading `v` are ignored: `1.0.0+a` equals `v1.0.0+b`.

`sortVersions(list)` returns a new array sorted from lowest to highest,
without changing `list`.

Also write tests in `versions.test.js`, using `node:test` and
`node:assert`.
