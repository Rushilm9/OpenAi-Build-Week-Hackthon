import test from "node:test";
import assert from "node:assert/strict";
import createDOMPurify from "dompurify";
import { JSDOM } from "jsdom";

const window = new JSDOM("").window;
const DOMPurify = createDOMPurify(window);

test("preserves supported formatting and removes executable HTML", () => {
  const dirty = [
    '<ul><li onclick="globalThis.__xss = true"><strong>BUY</strong></li></ul>',
    '<img src="x" onerror="globalThis.__xss = true">',
    '<script>globalThis.__xss = true</script>',
  ].join("");

  const clean = DOMPurify.sanitize(dirty);

  assert.match(clean, /<ul><li><strong>BUY<\/strong><\/li><\/ul>/);
  assert.doesNotMatch(clean, /<script/i);
  assert.doesNotMatch(clean, /on(?:click|error)\s*=/i);
});
