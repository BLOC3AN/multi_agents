import React from 'react';
import MessageRenderer from './MessageRenderer';

const SyntaxTest: React.FC = () => {
  const testCode = `\`\`\`javascript
function hello() {
  console.log("Hello World!");
  return true;
}
\`\`\``;

  return (
    <div className="p-4">
      <h2 className="text-lg font-bold mb-4">Syntax Coloring Test</h2>
      <div className="border p-4 rounded">
        <div className="mb-2">
          <strong>Input:</strong> 
          <pre className="bg-gray-100 p-2 text-sm mt-1">{testCode}</pre>
        </div>
        <div>
          <strong>Output:</strong>
          <div className="border p-2 mt-1">
            <MessageRenderer content={testCode} />
          </div>
        </div>
      </div>
      <div className="mt-4 text-sm text-gray-600">
        Check browser console for debug info
      </div>
    </div>
  );
};

export default SyntaxTest;
