import assert from 'node:assert/strict';

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// Mocking the behavior of apiFetch's error parsing logic
function parseErrorBody(body, statusText) {
  let detail = statusText;
  try {
    // Standardized error format check
    if (body?.error?.message) {
      detail = body.error.message;
    } else if (body?.detail) {
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    }
  } catch (e) {
    // Ignore parsing errors
  }
  return detail;
}

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log(`  PASS ${name}`);
  } catch (e) {
    failed++;
    console.log(`  FAIL ${name}: ${e.message}`);
  }
}

console.log('== Frontend Auth Error Parsing Tests ==');

test('Parses standardized error format { error: { message: "..." } }', () => {
  const body = {
    success: false,
    error: {
      code: 400,
      message: "The verification code you entered is incorrect.",
      details: null
    }
  };
  const detail = parseErrorBody(body, "Bad Request");
  assert.equal(detail, "The verification code you entered is incorrect.");
});

test('Parses standard FastAPI error format { detail: "..." }', () => {
  const body = {
    detail: "Not Found"
  };
  const detail = parseErrorBody(body, "Not Found");
  assert.equal(detail, "Not Found");
});

test('Falls back to statusText if body is empty', () => {
  const detail = parseErrorBody(null, "Internal Server Error");
  assert.equal(detail, "Internal Server Error");
});

test('Falls back to statusText if body has no message or detail', () => {
  const body = { foo: "bar" };
  const detail = parseErrorBody(body, "Bad Request");
  assert.equal(detail, "Bad Request");
});

console.log(`\nResults: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
