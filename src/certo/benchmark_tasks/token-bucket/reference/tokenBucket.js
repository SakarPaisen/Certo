class TokenBucket {
  constructor({ capacity, refillPerSecond, now = Date.now } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be an integer of at least 1');
    }
    if (typeof refillPerSecond !== 'number' || !(refillPerSecond > 0) || !Number.isFinite(refillPerSecond)) {
      throw new RangeError('refillPerSecond must be a number greater than 0');
    }
    this.capacity = capacity;
    this.refillPerSecond = refillPerSecond;
    this.now = now;
    this.tokens = capacity;
    this.last = now();
  }

  refill() {
    const current = this.now();
    const elapsed = Math.max(0, current - this.last) / 1000;
    this.tokens = Math.min(this.capacity, this.tokens + elapsed * this.refillPerSecond);
    this.last = Math.max(this.last, current);
  }

  available() {
    this.refill();
    return Math.floor(this.tokens);
  }

  tryTake(n = 1) {
    if (!Number.isInteger(n) || n < 1 || n > this.capacity) {
      throw new RangeError('n must be an integer between 1 and capacity');
    }
    this.refill();
    if (this.tokens >= n) {
      this.tokens -= n;
      return true;
    }
    return false;
  }
}

module.exports = { TokenBucket };
