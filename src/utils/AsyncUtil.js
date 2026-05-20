const logger = require('./logger');

class AsyncUtil {
  /**
   * Execute a promise with retry on rate-limit or transient errors.
   */
  static async retry(fn, options = {}) {
    const { maxRetries = 3, baseDelay = 1000, onRetry } = options;
    let lastError;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (err) {
        lastError = err;
        const isRateLimit = err.code === 429 || err.status === 429;
        const isTransient = err.code === 500 || err.code === 502 || err.code === 503;

        if (attempt < maxRetries && (isRateLimit || isTransient)) {
          const delay = isRateLimit
            ? (err.retryAfter || 5) * 1000 + 500
            : baseDelay * attempt;

          if (onRetry) onRetry(attempt, delay, err);
          await AsyncUtil.sleep(delay);
          continue;
        }
        throw err;
      }
    }
    throw lastError;
  }

  /**
   * Insert a delay between sequential API calls to avoid rate limits.
   */
  static async batchSend(items, fn, { concurrency = 1, delay = 500 } = {}) {
    const results = [];
    for (let i = 0; i < items.length; i += concurrency) {
      const batch = items.slice(i, i + concurrency);
      const batchResults = await Promise.allSettled(batch.map(item => fn(item)));
      results.push(...batchResults);
      if (i + concurrency < items.length) {
        await AsyncUtil.sleep(delay);
      }
    }
    return results;
  }

  static sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = AsyncUtil;
