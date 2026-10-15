# Asteroids in the browser

Needs Node 18 or newer, for the tests. No npm packages: there is nothing to
install.

Build a browser Asteroids game in plain JavaScript, HTML and CSS.

## Game

- The ship turns with Left/Right (or A/D), thrusts with Up (or W) and slows
  down by friction, and shoots with Space. At most 5 bullets fly at once,
  and each one disappears after a second or so.
- The ship, bullets and asteroids leave one edge of the screen and come
  back on the opposite edge.
- Asteroids drift at different speeds. A shot large asteroid splits into
  two medium ones, a medium one into two small ones, and a small one is
  destroyed.
- A bullet that hits an asteroid is removed and scores 20 points for a
  large asteroid, 50 for a medium one and 100 for a small one.
- An asteroid hitting the ship costs a life. The player has 3 lives. At 0
  the game is over, and Enter starts a new game.
- When every asteroid is gone, a new wave starts with one more asteroid.
- P pauses and resumes. Score, lives and wave are always on screen.
- Draw on a canvas that fills the window and follows resizes. Movement uses
  the time between frames, so the speed doesn't depend on the frame rate.

## Files

- `game.js`: every rule above (movement, wrapping, bullets, splitting,
  collisions, scoring, lives, waves) as plain functions or classes, with no
  canvas, DOM or keyboard code. It must load both as a plain `<script>` in
  the browser (no `import`/`export`) and with `require` in Node, so it ends
  with `if (typeof module !== "undefined") module.exports = { ... };`.
  It includes at least these functions, used by the game and the tests:

  | Function | Examples |
  | --- | --- |
  | `wrap(x, y, width, height)` returns `{ x, y }` back on screen | `wrap(-5, 10, 800, 600)` → `{ x: 795, y: 10 }`; `wrap(805, 610, 800, 600)` → `{ x: 5, y: 10 }` |
  | `splitAsteroid(asteroid)` returns the pieces of a shot asteroid (an object with at least `x`, `y` and `size`) | a `"large"` one → two `"medium"`; a `"medium"` one → two `"small"`; a `"small"` one → `[]` |
  | `pointsFor(size)` | `"large"` → 20, `"medium"` → 50, `"small"` → 100 |
  | `circlesCollide(a, b)` for two `{ x, y, radius }` | `({ x: 0, y: 0, radius: 10 }, { x: 15, y: 0, radius: 6 })` → `true`; `({ x: 0, y: 0, radius: 10 }, { x: 20, y: 0, radius: 5 })` → `false` |
- `main.js`: drawing, keyboard input and the game loop, using `game.js`.
- `index.html`: the canvas plus `<script src="game.js">` and
  `<script src="main.js">`. Opening the file in a browser starts the game,
  with no server.
- `game.test.js`: tests with Node's built-in test runner (`node:test` and
  `node:assert`) with every example in the table above, copied as written
  (they are worked out already, don't change them), plus a test that the
  game is over when the last life is lost. Compare numbers that aren't
  whole with a tolerance (`Math.abs(a - b) < 1e-9`), never `strictEqual`.
- `package.json`: no dependencies, and `"scripts": { "test": "node --test" }`.
- `README.md`: how to open the game and how to run the tests.

## Done when

- `npm test` passes.
- Opening `index.html` shows the game.
