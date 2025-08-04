import React from 'react';

interface TypingAnimationProps {
  className?: string;
}

const TypingAnimation: React.FC<TypingAnimationProps> = ({ className = '' }) => {
  return (
    <div 
      className={`w-full text-gray-900 dark:text-white rounded-2xl px-4 py-3 shadow-sm ${className}`}
      style={{
        backgroundColor: 'var(--bg-elevated-secondary, #f8f9fa)'
      }}
    >
      <div className="flex items-center space-x-2">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
        <span className="text-sm text-gray-500 dark:text-gray-400 font-universal">
          AI is thinking...
        </span>
      </div>
    </div>
  );
};

export default TypingAnimation;
