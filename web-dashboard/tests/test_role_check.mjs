
import assert from 'node:assert/strict';

// Mocking the behavior of auth.tsx verifyOtp logic
const ADMIN_ROLES = ['ADMIN', 'BRANCH_MANAGER'];

function verifyOtpLogic(role) {
  if (!ADMIN_ROLES.includes(role)) {
    throw new Error('This account does not have admin access.');
  }
  return { success: true, role };
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

console.log('== Frontend Auth Role Check Tests ==');

test('Allows ADMIN role', () => {
  const result = verifyOtpLogic('ADMIN');
  assert.equal(result.success, true);
});

test('Allows BRANCH_MANAGER role', () => {
  const result = verifyOtpLogic('BRANCH_MANAGER');
  assert.equal(result.success, true);
});

test('Blocks CUSTOMER role', () => {
  assert.throws(() => verifyOtpLogic('CUSTOMER'), /admin access/);
});

test('Blocks unknown role', () => {
  assert.throws(() => verifyOtpLogic('DRIVER'), /admin access/);
});

console.log(`\nResults: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
