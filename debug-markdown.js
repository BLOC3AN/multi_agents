// Simple test to understand markdown parsing
const text = '**`cout << "Tong cua " << a << " va " << b << " la: " << sum << endl;`:** In kết quả ra màn hình.';

console.log('Input text:', text);

// This should parse as:
// - ** should create <strong> element
// - ` should create <code> element with inline=true
// - The combination should be: <strong><code>...</code>:</strong>

// But it seems like it's being parsed as just <code> element
