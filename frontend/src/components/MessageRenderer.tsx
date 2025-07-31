import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

interface MessageRendererProps {
  content: string;
  className?: string;
}

const MessageRenderer: React.FC<MessageRendererProps> = ({ content, className = '' }) => {
  return (
    <div className={`message-renderer ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          // Code blocks
          code: ({ node, inline, className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '');
            const language = match ? match[1] : '';

            if (inline) {
              return (
                <code
                  className="inline-code px-2 py-1 bg-blue-50 dark:bg-blue-900/30 rounded-md text-sm font-mono text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            // Language-specific colors - subtle backgrounds
            const getLanguageColor = (lang: string) => {
              const colors: Record<string, string> = {
                javascript: 'bg-yellow-50/50 dark:bg-yellow-900/10 border-yellow-200/50 dark:border-yellow-700/30',
                python: 'bg-green-50/50 dark:bg-green-900/10 border-green-200/50 dark:border-green-700/30',
                sql: 'bg-purple-50/50 dark:bg-purple-900/10 border-purple-200/50 dark:border-purple-700/30',
                bash: 'bg-gray-50/50 dark:bg-gray-900/10 border-gray-200/50 dark:border-gray-700/30',
                json: 'bg-orange-50/50 dark:bg-orange-900/10 border-orange-200/50 dark:border-orange-700/30',
                css: 'bg-pink-50/50 dark:bg-pink-900/10 border-pink-200/50 dark:border-pink-700/30',
                html: 'bg-red-50/50 dark:bg-red-900/10 border-red-200/50 dark:border-red-700/30',
                typescript: 'bg-blue-50/50 dark:bg-blue-900/10 border-blue-200/50 dark:border-blue-700/30',
              };
              return colors[lang] || 'bg-gray-50/50 dark:bg-gray-800/50 border-gray-200/50 dark:border-gray-600/30';
            };

            const copyToClipboard = (text: string) => {
              navigator.clipboard.writeText(text).then(() => {
                // Could add toast notification here
                console.log('Code copied to clipboard');
              });
            };

            return (
              <div className="code-block my-4 rounded-lg overflow-hidden border border-gray-200/50 dark:border-gray-600/50">
                {language && (
                  <div className={`code-header px-4 py-2 text-xs font-medium text-gray-700 dark:text-gray-300 border-b border-gray-200/50 dark:border-gray-600/50 ${getLanguageColor(language)}`}>
                    <div className="flex items-center justify-between">
                      <span className="uppercase tracking-wide font-semibold">{language}</span>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => copyToClipboard(String(children))}
                          className="flex items-center space-x-1 px-2 py-1 text-xs bg-white/20 dark:bg-black/20 rounded hover:bg-white/30 dark:hover:bg-black/30 transition-colors"
                          title="Copy code"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                          <span>Copy</span>
                        </button>
                        <div className="flex space-x-1">
                          <div className="w-3 h-3 rounded-full bg-red-400/70"></div>
                          <div className="w-3 h-3 rounded-full bg-yellow-400/70"></div>
                          <div className="w-3 h-3 rounded-full bg-green-400/70"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <pre className={`code-content p-4 overflow-x-auto bg-gray-800/90 dark:bg-gray-900/90`}>
                  <code className="font-mono text-sm text-gray-100" {...props}>
                    {children}
                  </code>
                </pre>
              </div>
            );
          },
          
          // Headings
          h1: ({ children }) => (
            <h1 className="text-xl font-universal-semibold text-gray-900 dark:text-white mt-6 mb-4 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-universal-semibold text-gray-900 dark:text-white mt-5 mb-3 first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-universal-medium text-gray-900 dark:text-white mt-4 mb-2 first:mt-0">
              {children}
            </h3>
          ),
          
          // Paragraphs
          p: ({ children }) => (
            <p className="text-universal-14 mb-3 last:mb-0 leading-relaxed">
              {children}
            </p>
          ),
          
          // Lists
          ul: ({ children }) => (
            <ul className="list-disc list-inside mb-3 space-y-1 text-universal-14">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside mb-3 space-y-1 text-universal-14">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-universal-14 leading-relaxed">
              {children}
            </li>
          ),
          
          // Links
          a: ({ href, children }) => (
            <a 
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline"
            >
              {children}
            </a>
          ),
          
          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 py-2 my-4 bg-gray-50 dark:bg-gray-800 rounded-r-lg">
              <div className="text-gray-700 dark:text-gray-300 italic">
                {children}
              </div>
            </blockquote>
          ),
          
          // Tables
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full border border-gray-200 dark:border-gray-600 rounded-lg">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-gray-50 dark:bg-gray-700">
              {children}
            </thead>
          ),
          th: ({ children }) => (
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider border-b border-gray-200 dark:border-gray-600">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-2 text-sm text-gray-900 dark:text-gray-100 border-b border-gray-200 dark:border-gray-600">
              {children}
            </td>
          ),
          
          // Horizontal rule
          hr: () => (
            <hr className="my-6 border-gray-200 dark:border-gray-600" />
          ),
          
          // Strong and emphasis
          strong: ({ children }) => (
            <strong className="font-bold text-gray-900 dark:text-white font-universal">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-gray-800 dark:text-gray-200 font-universal">
              {children}
            </em>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MessageRenderer;
