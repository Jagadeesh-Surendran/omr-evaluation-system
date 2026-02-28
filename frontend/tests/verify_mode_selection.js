// Simple verification script for mode selection
console.log('=== Mode Selection Verification ===');

// Test 1: Valid manual mode
console.log('\nTest 1: Valid manual mode');
try {
  selectMode(EVALUATION_MODES.MANUAL);
  console.log('✓ Manual mode selected successfully');
  console.log('  Current mode:', appState.currentMode);
  console.log('  Current screen:', appState.currentScreen);
} catch (e) {
  console.error('✗ Error:', e.message);
}

// Reset
resetAppState();

// Test 2: Valid AI mode
console.log('\nTest 2: Valid AI mode');
try {
  selectMode(EVALUATION_MODES.AI);
  console.log('✓ AI mode selected successfully');
  console.log('  Current mode:', appState.currentMode);
  console.log('  Current screen:', appState.currentScreen);
} catch (e) {
  console.error('✗ Error:', e.message);
}

// Reset
resetAppState();

// Test 3: Invalid mode
console.log('\nTest 3: Invalid mode');
try {
  selectMode('invalid');
  console.log('  Current mode:', appState.currentMode);
  console.log('  Should be null:', appState.currentMode === null ? '✓' : '✗');
} catch (e) {
  console.error('✗ Error:', e.message);
}

console.log('\n=== Verification Complete ===');
