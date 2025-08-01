// Test in browser console
// Copy this to browser console to test markdown parsing

const testMarkdown = '**`cout << "Hello" << endl;`:** This is a test case.';

console.log('Testing markdown:', testMarkdown);

// Expected behavior:
// - ** should create <strong> element
// - ` should create <code> element with inline=true inside the strong
// - Result should be: <strong><code>cout << "Hello" << endl;</code>:</strong> This is a test case.

// But current behavior seems to be:
// - The whole thing is treated as a code block instead of bold with inline code
