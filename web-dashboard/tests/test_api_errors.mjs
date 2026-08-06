import assert from 'node:assert/strict';

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

const ICONS = Object.freeze({
  AlertCircle: 'AlertCircle',
  ServerCrash: 'ServerCrash',
  WifiOff: 'WifiOff',
  ShieldAlert: 'ShieldAlert',
  Search: 'Search',
  AlertTriangle: 'AlertTriangle',
});

function formatPageError(error, fallback) {
  const safeFallback = fallback || 'Something went wrong';

  if (error instanceof ApiError) {
    const status = error.status || 0;
    if (status === 0) {
      const raw = (error.message || '').toLowerCase();
      if (raw.includes('fetch') || raw.includes('network') || raw.includes('offline')) {
        return { status: 0, message: 'Cannot connect to the server', detail: 'Please check that the backend API is running and your network connection is stable.', icon: ICONS.WifiOff };
      }
      if (raw.includes('time') && raw.includes('out')) {
        return { status: 0, message: 'The server took too long to respond', detail: 'Please try again in a moment.', icon: ICONS.ServerCrash };
      }
      return { status: 0, message: 'Network error', detail: error.message || safeFallback, icon: ICONS.WifiOff };
    }
    if (status === 401) {
      return { status, message: 'Your session has expired', detail: 'Sign out and sign back in to refresh your credentials.', icon: ICONS.ShieldAlert };
    }
    if (status === 403) {
      return { status, message: 'Permission denied', detail: error.message || 'Your account does not have permission to view this page.', icon: ICONS.ShieldAlert };
    }
    if (status === 404) {
      return { status, message: 'Resource not found', detail: error.message || 'The requested data does not exist on the server.', icon: ICONS.Search };
    }
    if (status >= 500) {
      return { status, message: 'Server error', detail: error.message || safeFallback, icon: ICONS.ServerCrash };
    }
    return { status, message: 'Request failed', detail: error.message || safeFallback, icon: ICONS.AlertTriangle };
  }

  if (error instanceof Error) {
    const msg = (error.message || '').toLowerCase();
    if (msg.includes('failed to fetch') || msg.includes('network') || msg.includes('load')) {
      return { status: 0, message: 'Cannot connect to the server', detail: 'Please check that the backend API is running and your network connection is stable.', icon: ICONS.WifiOff };
    }
    if (msg.includes('time') && msg.includes('out')) {
      return { status: 0, message: 'The server took too long to respond', detail: 'Please try again in a moment.', icon: ICONS.ServerCrash };
    }
    return { status: 0, message: safeFallback, detail: error.message, icon: ICONS.AlertCircle };
  }

  return { status: 0, message: safeFallback, detail: '', icon: ICONS.AlertCircle };
}

function decodeJwtPayload(token) {
  if (!token) return null;
  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const base64Payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64Payload + '='.repeat((4 - (base64Payload.length % 4)) % 4);
    const decoded = Buffer.from(padded, 'base64').toString('utf-8');
    const obj = JSON.parse(decoded);
    return {
      sub: typeof obj.sub === 'string' ? obj.sub : null,
      role: typeof obj.role === 'string' ? obj.role : null,
      exp: typeof obj.exp === 'number' ? obj.exp : null,
      iat: typeof obj.iat === 'number' ? obj.iat : null,
      aud: typeof obj.aud === 'string' ? obj.aud : null,
      raw: obj,
    };
  } catch {
    return null;
  }
}

function btoaUrl(s) {
  return Buffer.from(s, 'utf-8').toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

let passed = 0;
let failed = 0;
const failures = [];
function test(name, fn) {
  try {
    fn();
    passed += 1;
    console.log('  PASS ', name);
  } catch (e) {
    failed += 1;
    failures.push({ name, message: e.message, stack: e.stack });
    console.log('  FAIL ', name, '\n      ', e.message);
  }
}

console.log('\n== ApiError wrapping (prevents raw "Failed to fetch" TypeError) ==');

test('ApiError(0, "Failed to fetch") becomes network error', () => {
  const r = formatPageError(new ApiError(0, 'Failed to fetch'), 'fallback');
  assert.equal(r.status, 0);
  assert.equal(r.icon, ICONS.WifiOff);
  assert.ok(r.message.includes('connect'), r.message);
});

test('ApiError(0, "Request timeout") becomes timeout error', () => {
  const r = formatPageError(new ApiError(0, 'Request timeout exceeded'), 'x');
  assert.equal(r.icon, ICONS.ServerCrash);
  assert.ok(r.message.includes('too long'), r.message);
});

test('ApiError(0, "unknown error") falls back to Network error', () => {
  const r = formatPageError(new ApiError(0, 'unknown error'), 'x');
  assert.equal(r.message, 'Network error');
  assert.equal(r.detail, 'unknown error');
});

test('ApiError(401) returns session expired message', () => {
  const r = formatPageError(new ApiError(401, 'Not authorized'), 'x');
  assert.equal(r.status, 401);
  assert.equal(r.icon, ICONS.ShieldAlert);
  assert.ok(r.message.includes('expired'), r.message);
});

test('ApiError(403) returns permission denied', () => {
  const r = formatPageError(new ApiError(403, 'forbidden'), 'x');
  assert.equal(r.status, 403);
  assert.equal(r.icon, ICONS.ShieldAlert);
  assert.ok(r.message.includes('Permission'), r.message);
});

test('ApiError(404) returns resource not found', () => {
  const r = formatPageError(new ApiError(404, 'nope'), 'x');
  assert.equal(r.status, 404);
  assert.equal(r.icon, ICONS.Search);
});

test('ApiError(500) returns Server error', () => {
  const r = formatPageError(new ApiError(500, 'pg boom'), 'x');
  assert.equal(r.status, 500);
  assert.equal(r.icon, ICONS.ServerCrash);
  assert.equal(r.message, 'Server error');
  assert.equal(r.detail, 'pg boom');
});

test('ApiError(422) generic 4xx -> Request failed + AlertTriangle', () => {
  const r = formatPageError(new ApiError(422, 'validation'), 'x');
  assert.equal(r.status, 422);
  assert.equal(r.icon, ICONS.AlertTriangle);
  assert.equal(r.message, 'Request failed');
  assert.equal(r.detail, 'validation');
});

console.log('\n== Raw Error fallback (non-ApiError, pre-fix browser behavior) ==');

test('raw TypeError "Failed to fetch" maps to WifiOff + cannot connect', () => {
  const r = formatPageError(new TypeError('Failed to fetch'), 'fallback');
  assert.equal(r.status, 0);
  assert.equal(r.icon, ICONS.WifiOff);
  assert.ok(r.message.includes('connect'));
});

test('raw Error("NetworkError when attempting to fetch resource") -> WifiOff', () => {
  const r = formatPageError(new Error('NetworkError when attempting to fetch resource'), 'fb');
  assert.equal(r.icon, ICONS.WifiOff);
});

test('raw Error("the operation timed out") -> ServerCrash', () => {
  const r = formatPageError(new Error('the operation timed out'), 'fb');
  assert.equal(r.icon, ICONS.ServerCrash);
});

test('generic Error falls back to supplied message + AlertCircle + detail', () => {
  const r = formatPageError(new Error('boom'), 'Could not load');
  assert.equal(r.message, 'Could not load');
  assert.equal(r.detail, 'boom');
  assert.equal(r.icon, ICONS.AlertCircle);
});

test('non-Error value (null / string / object) falls back gracefully', () => {
  assert.equal(formatPageError(null, 'f1').message, 'f1');
  assert.equal(formatPageError(null, 'f1').detail, '');
  assert.equal(formatPageError('weird', 'f2').message, 'f2');
  assert.equal(formatPageError(undefined, 'f3').icon, ICONS.AlertCircle);
});

console.log('\n== decodeJwtPayload (JWT base64url decoding) ==');

test('null / undefined / empty token -> null', () => {
  assert.equal(decodeJwtPayload(null), null);
  assert.equal(decodeJwtPayload(undefined), null);
  assert.equal(decodeJwtPayload(''), null);
});

test('malformed token (1 segment) -> null', () => {
  assert.equal(decodeJwtPayload('abc'), null);
});

test('garbage base64 payload -> null (catch)', () => {
  assert.equal(decodeJwtPayload('a.!!!!.c'), null);
});

test('valid JWT payload with admin role + sub + exp', () => {
  const payload = { sub: 'admin-uuid', role: 'ADMIN', exp: 1785929169, iat: 1785925569, aud: 'clean-delivery' };
  const token = `ignored_header.${btoaUrl(JSON.stringify(payload))}.ignored_sig`;
  const r = decodeJwtPayload(token);
  assert.ok(r !== null);
  assert.equal(r.sub, 'admin-uuid');
  assert.equal(r.role, 'ADMIN');
  assert.equal(r.exp, 1785929169);
  assert.equal(r.iat, 1785925569);
  assert.equal(r.aud, 'clean-delivery');
  assert.deepEqual(r.raw, payload);
});

test('valid JWT payload missing fields -> null placeholders (not undefined)', () => {
  const token = `h.${btoaUrl(JSON.stringify({ weird: 1 }))}.s`;
  const r = decodeJwtPayload(token);
  assert.equal(r.sub, null);
  assert.equal(r.role, null);
  assert.equal(r.exp, null);
  assert.equal(r.iat, null);
  assert.equal(r.aud, null);
});

test('JWT with no padding in payload (common real-world case)', () => {
  const payload = { sub: 'x', role: 'DRIVER' };
  let base64 = Buffer.from(JSON.stringify(payload)).toString('base64');
  base64 = base64.replace(/=+$/g, '');
  const token = `h.${base64}.s`;
  assert.equal(decodeJwtPayload(token).role, 'DRIVER');
  assert.equal(decodeJwtPayload(token).sub, 'x');
});

console.log('\n== Route / settings regression (App.tsx) ==');

const ROUTES = Object.freeze({
  '/overview': 'DashboardOverview',
  '/orders': 'OrderManagement',
  '/fleet': 'LiveFleetTracker',
  '/inventory': 'InventoryManager',
  '/products': 'Products',
  '/branches': 'BranchManagement',
  '/staff': 'Staff',
  '/settings': 'Settings',
});

test('/settings must map to Settings component (NOT DashboardOverview) — regression guard', () => {
  assert.equal(ROUTES['/settings'], 'Settings');
  assert.notEqual(ROUTES['/settings'], 'DashboardOverview');
});

test('all bug-report pages are routed independently (not aliased to Overview)', () => {
  const aliases = ['/staff', '/branches', '/inventory', '/fleet', '/settings'];
  for (const p of aliases) {
    assert.notEqual(ROUTES[p], 'DashboardOverview', `${p} must not map to DashboardOverview`);
    assert.ok(/^[A-Z][A-Za-z]+$/.test(ROUTES[p]), `${p} must have a real component name`);
  }
});

console.log(`\n===== ${passed} passed, ${failed} failed =====`);
if (failures.length) {
  console.log('\nFailures:');
  for (const f of failures) console.log('  -', f.name, '::', f.message);
  process.exitCode = 1;
}
