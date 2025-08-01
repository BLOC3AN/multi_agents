import React from 'react';
import MessageRenderer from './MessageRenderer';

const LaTeXTest: React.FC = () => {
  const testCases = [
    {
      name: "Simple Inline Math",
      content: "The formula $a^2 + b^2 = c^2$ is the Pythagorean theorem.",
      expected: "Should render inline math"
    },
    {
      name: "Simple Display Math",
      content: "$$E = mc^2$$",
      expected: "Should render as display math"
    },
    {
      name: "Fraction",
      content: "$$\\frac{a}{b} = \\frac{c}{d}$$",
      expected: "Should render fraction"
    },
    {
      name: "Integral",
      content: "$$\\int_{0}^{1} x^2 dx = \\frac{1}{3}$$",
      expected: "Should render integral"
    },
    {
      name: "LaTeX Code Block",
      content: `\`\`\`latex
\\frac{d}{dx}\\left( \\int_{0}^{x} f(u) \\, du\\right) = f(x)
\`\`\``,
      expected: "Should render as math formula"
    },
    {
      name: "Mixed Content",
      content: "Here is some text with $x = y + z$ and then more text with $$\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}$$ and final text.",
      expected: "Should render mixed inline and display math"
    }
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">LaTeX Rendering Test</h1>
      
      <div className="space-y-6">
        {testCases.map((testCase, index) => (
          <div key={index} className="border border-gray-300 rounded-lg p-4">
            <h3 className="font-semibold mb-2 text-lg">{testCase.name}</h3>
            
            <div className="mb-3">
              <strong className="text-sm text-gray-700">Input:</strong>
              <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                {testCase.content}
              </pre>
            </div>
            
            <div className="mb-2">
              <strong className="text-sm text-gray-700">Expected:</strong>
              <span className="ml-2 text-sm text-gray-600">{testCase.expected}</span>
            </div>
            
            <div>
              <strong className="text-sm text-gray-700">Result:</strong>
              <div className="mt-1 p-3 border border-gray-200 rounded bg-white">
                <MessageRenderer content={testCase.content} />
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded">
        <h3 className="font-semibold text-blue-800 mb-2">LaTeX Support:</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• <code>```latex</code> blocks should render as display math</li>
          <li>• <code>```math</code> blocks should render as display math</li>
          <li>• <code>$...$</code> should render as inline math</li>
          <li>• <code>$$...$$</code> should render as display math</li>
        </ul>
      </div>
    </div>
  );
};

export default LaTeXTest;
