import React, { useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MathJaxRenderer, MixedLatexRenderer } from './MathJaxRenderer';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { github, vs2015 } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import javascript from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import cpp from 'react-syntax-highlighter/dist/esm/languages/hljs/cpp';

// Register languages
SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('cpp', cpp);
SyntaxHighlighter.registerLanguage('c', cpp);

// Helper function to process mixed LaTeX content
const processMixedLatex = (content: string): React.ReactNode => {
  return <MixedLatexRenderer content={content} />;
};

// Preprocess content to handle math expressions
const preprocessMathContent = (content: string): string => {
  // Handle display math $$...$$
  content = content.replace(/\$\$([^$]+)\$\$/g, (match, mathContent) => {
    return `\n\n__MATH_DISPLAY_START__${mathContent.trim()}__MATH_DISPLAY_END__\n\n`;
  });

  // Handle inline math $...$
  content = content.replace(/\$([^$\n]+)\$/g, (match, mathContent) => {
    return `__MATH_INLINE_START__${mathContent.trim()}__MATH_INLINE_END__`;
  });

  return content;
};

// Component to process text nodes and render math
const MathTextProcessor: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  if (typeof children !== 'string') {
    return <>{children}</>;
  }

  const text = children as string;

  // Split by math placeholders
  const parts = text.split(/(__MATH_(?:DISPLAY|INLINE)_START__.*?__MATH_(?:DISPLAY|INLINE)_END__)/);

  return (
    <>
      {parts.map((part, index) => {
        // Check for display math
        const displayMatch = part.match(/^__MATH_DISPLAY_START__(.*?)__MATH_DISPLAY_END__$/);
        if (displayMatch) {
          return (
            <div key={index} className="not-prose my-4">
              <div className="math-display-wrapper bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md p-4 overflow-x-auto">
                <MathJaxRenderer
                  latex={displayMatch[1]}
                  display={true}
                  className="text-center"
                />
              </div>
            </div>
          );
        }

        // Check for inline math
        const inlineMatch = part.match(/^__MATH_INLINE_START__(.*?)__MATH_INLINE_END__$/);
        if (inlineMatch) {
          return (
            <MathJaxRenderer
              key={index}
              latex={inlineMatch[1]}
              display={false}
            />
          );
        }

        // Regular text
        return part;
      })}
    </>
  );
};

// Custom dark theme for better readability
const customDarkTheme = {
  'hljs': {
    display: 'block',
    overflowX: 'auto',
    padding: '0.5em',
    background: 'transparent',
    color: '#e6e6e6'
  },
  'hljs-comment': { color: '#7c7c7c', fontStyle: 'italic' },
  'hljs-quote': { color: '#7c7c7c', fontStyle: 'italic' },
  'hljs-keyword': { color: '#ff6b6b', fontWeight: 'bold' },
  'hljs-selector-tag': { color: '#ff6b6b' },
  'hljs-literal': { color: '#ff6b6b' },
  'hljs-section': { color: '#ff6b6b' },
  'hljs-link': { color: '#ff6b6b' },
  'hljs-function': { color: '#4ecdc4' },
  'hljs-class': { color: '#4ecdc4' },
  'hljs-number': { color: '#45b7d1' },
  'hljs-regexp': { color: '#45b7d1' },
  'hljs-string': { color: '#96ceb4' },
  'hljs-built_in': { color: '#feca57' },
  'hljs-symbol': { color: '#feca57' },
  'hljs-variable': { color: '#feca57' },
  'hljs-template-variable': { color: '#feca57' },
  'hljs-type': { color: '#ff9ff3' },
  'hljs-tag': { color: '#ff9ff3' },
  'hljs-name': { color: '#ff9ff3' },
  'hljs-attribute': { color: '#ff9ff3' },
  'hljs-selector-id': { color: '#ff9ff3' },
  'hljs-selector-class': { color: '#ff9ff3' },
  'hljs-title': { color: '#54a0ff', fontWeight: 'bold' },
  'hljs-emphasis': { fontStyle: 'italic' },
  'hljs-strong': { fontWeight: 'bold' }
};

// Hook to detect dark mode
const useDarkMode = () => {
  const [isDark, setIsDark] = React.useState(false);

  React.useEffect(() => {
    const checkDarkMode = () => {
      const isDarkMode = document.documentElement.classList.contains('dark') ||
                        document.documentElement.getAttribute('data-theme') === 'dark';
      setIsDark(isDarkMode);
    };

    checkDarkMode();

    // Watch for theme changes
    const observer = new MutationObserver(checkDarkMode);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class', 'data-theme']
    });

    return () => observer.disconnect();
  }, []);

  return isDark;
};

// Custom syntax coloring theme - chỉ màu chữ, không highlight background
const customSyntaxColors = {
  'code[class*="language-"]': {
    color: '#24292e',
    background: 'transparent',
    fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
    fontSize: '0.875rem',
    lineHeight: '1.25rem',
    direction: 'ltr',
    textAlign: 'left',
    whiteSpace: 'pre',
    wordSpacing: 'normal',
    wordBreak: 'normal',
    tabSize: 4,
    hyphens: 'none'
  },
  'pre[class*="language-"]': {
    color: '#24292e',
    background: 'transparent',
    fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
    fontSize: '0.875rem',
    lineHeight: '1.25rem',
    direction: 'ltr',
    textAlign: 'left',
    whiteSpace: 'pre',
    wordSpacing: 'normal',
    wordBreak: 'normal',
    tabSize: 4,
    hyphens: 'none',
    padding: '1rem',
    margin: 0,
    overflow: 'auto'
  },
  // Comments - màu xám
  'comment': { color: '#6a737d', fontStyle: 'italic', background: 'transparent' },
  'prolog': { color: '#6a737d', fontStyle: 'italic', background: 'transparent' },
  'doctype': { color: '#6a737d', fontStyle: 'italic', background: 'transparent' },
  'cdata': { color: '#6a737d', fontStyle: 'italic', background: 'transparent' },

  // Punctuation - màu đen
  'punctuation': { color: '#24292e', background: 'transparent' },

  // Properties, numbers, booleans - màu xanh dương
  'property': { color: '#005cc5', background: 'transparent' },
  'boolean': { color: '#005cc5', background: 'transparent' },
  'number': { color: '#005cc5', background: 'transparent' },
  'constant': { color: '#005cc5', background: 'transparent' },
  'symbol': { color: '#005cc5', background: 'transparent' },
  'builtin': { color: '#005cc5', background: 'transparent' },

  // Tags, selectors - màu xanh lá
  'tag': { color: '#22863a', background: 'transparent' },
  'selector': { color: '#22863a', background: 'transparent' },
  'inserted': { color: '#22863a', background: 'transparent' },
  'entity': { color: '#22863a', background: 'transparent' },
  'url': { color: '#22863a', background: 'transparent' },
  'atrule': { color: '#22863a', background: 'transparent' },

  // Strings - màu xanh navy
  'string': { color: '#032f62', background: 'transparent' },
  'char': { color: '#032f62', background: 'transparent' },
  'attr-value': { color: '#032f62', background: 'transparent' },
  'regex': { color: '#032f62', background: 'transparent' },

  // Functions, classes - màu tím
  'function': { color: '#6f42c1', background: 'transparent' },
  'class-name': { color: '#6f42c1', background: 'transparent' },
  'attr-name': { color: '#6f42c1', background: 'transparent' },

  // Keywords, operators - màu đỏ
  'keyword': { color: '#d73a49', background: 'transparent' },
  'operator': { color: '#d73a49', background: 'transparent' },
  'deleted': { color: '#d73a49', background: 'transparent' },
  'important': { color: '#d73a49', fontWeight: 'bold', background: 'transparent' },

  // Variables - màu cam
  'variable': { color: '#e36209', background: 'transparent' }
};

// Custom transformer to prevent p wrapping of code blocks and other block elements
const remarkUnwrapCodeBlocks = () => {
  return (tree: any) => {
    const visit = (node: any, parent: any, index: number) => {
      if (node.type === 'paragraph' && node.children) {
        // Check if paragraph contains only block elements that shouldn't be in p tags
        const hasOnlyBlockElements = node.children.length === 1 && (
          (node.children[0].type === 'code' && node.children[0].lang) || // Code blocks
          node.children[0].type === 'html' || // HTML blocks
          node.children[0].type === 'blockquote' ||
          node.children[0].type === 'list' ||
          node.children[0].type === 'table'
        );

        if (hasOnlyBlockElements && parent && typeof index === 'number') {
          // Replace paragraph with just the block element
          parent.children[index] = node.children[0];
          return;
        }

        // Also check for mixed content that contains block elements (but NOT inline code)
        const hasBlockElements = node.children.some((child: any) =>
          (child.type === 'code' && child.lang) || // Only code blocks with language, not inline code
          child.type === 'html' ||
          child.type === 'blockquote' ||
          child.type === 'list' ||
          child.type === 'table'
        );

        if (hasBlockElements && parent && typeof index === 'number') {
          // Split the paragraph into separate elements
          const newElements: any[] = [];
          let currentTextGroup: any[] = [];

          node.children.forEach((child: any) => {
            if ((child.type === 'code' && child.lang) || // Only code blocks with language
                child.type === 'html' ||
                child.type === 'blockquote' ||
                child.type === 'list' ||
                child.type === 'table') {
              // Flush current text group as paragraph
              if (currentTextGroup.length > 0) {
                newElements.push({
                  type: 'paragraph',
                  children: currentTextGroup
                });
                currentTextGroup = [];
              }
              // Add block element directly
              newElements.push(child);
            } else {
              // Add to current text group (including inline code)
              currentTextGroup.push(child);
            }
          });

          // Flush remaining text group
          if (currentTextGroup.length > 0) {
            newElements.push({
              type: 'paragraph',
              children: currentTextGroup
            });
          }

          // Replace with new elements
          parent.children.splice(index, 1, ...newElements);
          return;
        }
      }

      // Recursively visit children
      if (node.children) {
        for (let i = 0; i < node.children.length; i++) {
          visit(node.children[i], node, i);
        }
      }
    };

    visit(tree, null, 0);
  };
};

interface MessageRendererProps {
  content: string;
  className?: string;
}

const MessageRenderer: React.FC<MessageRendererProps> = ({ content, className = '' }) => {
  const [copiedStates, setCopiedStates] = useState<{[key: string]: boolean}>({});
  const [collapsedStates, setCollapsedStates] = useState<{[key: string]: boolean}>({});
  const isDarkMode = useDarkMode();

  // Preprocess content to handle math expressions
  const processedContent = useMemo(() => {
    return preprocessMathContent(content);
  }, [content]);

  return (
    <div className={`message-renderer github-markdown max-w-none overflow-hidden ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        skipHtml={false}
        unwrapDisallowed={true}
        disallowedElements={[]}
        allowedElements={undefined}
        components={{
          // Paragraph - handle nesting issues properly
          p: ({ children, ...props }) => {
            // Convert children to array for analysis
            const childArray = React.Children.toArray(children);

            // Check if any child is a React element with block-level type
            const hasBlockElements = childArray.some(child => {
              if (React.isValidElement(child)) {
                const type = child.type;
                // Check for block elements by type name or component name
                if (typeof type === 'string') {
                  return ['div', 'pre', 'blockquote', 'ul', 'ol', 'table', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(type);
                }
                // Check for custom components that render block elements
                if (typeof type === 'function' && type.name) {
                  return ['CodeBlock', 'MathBlock'].includes(type.name);
                }
              }
              return false;
            });

            // Check if children contain only whitespace or empty content
            const hasOnlyWhitespace = childArray.every(child =>
              typeof child === 'string' && child.trim() === ''
            );

            // If contains block elements or only whitespace, use Fragment
            if (hasBlockElements || hasOnlyWhitespace) {
              return <React.Fragment>{children}</React.Fragment>;
            }

            // For text and inline content, use proper paragraph
            return <p className="text-universal-14 mb-3 last:mb-0 leading-relaxed" {...props}><MathTextProcessor>{children}</MathTextProcessor></p>;
          },

          // Code blocks with syntax highlighting
          code: ({ node, inline, className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '');
            const language = match ? match[1] : '';
            const content = String(children);

            // Debug logging
            console.log('🔍 Code component debug:', {
              inline,
              className,
              language,
              content: content.substring(0, 50) + '...',
              hasLanguage: Boolean(className && className.includes('language-')),
              contentLength: content.length
            });

            // Comprehensive inline detection
            const hasLanguage = Boolean(className && className.includes('language-'));
            const hasNewlines = content.includes('\n');
            const isShort = content.length < 100; // Reasonable threshold for inline code

            // Inline code conditions:
            // 1. Explicitly marked as inline AND no language
            // 2. OR: No language, no newlines, and reasonably short
            const isInlineCode = (inline && !hasLanguage) || (!hasLanguage && !hasNewlines && isShort);

            if (isInlineCode) {
              return (
                <code
                  className="text-sm px-1 rounded-sm !font-mono bg-orange-400/10 text-orange-500 dark:bg-orange-300/10 dark:text-orange-200"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            // Special handling for LaTeX/Math blocks
            if (language === 'latex' || language === 'tex' || language === 'math') {
              const mathContent = String(children).replace(/\n$/, '');

              // Check if it's pure LaTeX (no Vietnamese text mixed in)
              const hasVietnameseChars = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]/.test(mathContent);
              const hasMathDelimiters = /\$.*?\$/.test(mathContent);

              // Check if it's a document-level LaTeX (contains \documentclass, \begin{document}, etc.)
              const isDocumentLatex = /\\documentclass|\\begin\{document\}|\\usepackage/.test(mathContent);

              // Check if it's math-only LaTeX (contains math expressions but no document structure)
              const isMathLatex = /\\frac|\\int|\\sum|\\prod|\\sqrt|\\alpha|\\beta|\\gamma|\\delta|\\epsilon|\\theta|\\lambda|\\mu|\\pi|\\sigma|\\phi|\\psi|\\omega|\\infty|\\partial|\\nabla|\\times|\\cdot|\\pm|\\mp|\\leq|\\geq|\\neq|\\approx|\\equiv|\\propto|\\in|\\subset|\\supset|\\cup|\\cap|\\emptyset|\\forall|\\exists|\\therefore|\\because|\\implies|\\iff|\\land|\\lor|\\neg|\\oplus|\\otimes|\\langle|\\rangle|\\left|\\right|\\begin\{align\}|\\begin\{equation\}|\\begin\{matrix\}|\\begin\{pmatrix\}|\\begin\{bmatrix\}|\\begin\{vmatrix\}|\\begin\{cases\}/.test(mathContent);

              // If it has Vietnamese text but also math delimiters, process as mixed content
              if (hasVietnameseChars && hasMathDelimiters) {
                return (
                  <div className="not-prose my-4">
                    <div className="math-display-wrapper bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md p-4 overflow-x-auto">
                      <div className="prose prose-sm max-w-none text-gray-800 dark:text-gray-200">
                        {processMixedLatex(mathContent)}
                      </div>
                    </div>
                  </div>
                );
              }

              // If it's document-level LaTeX, show as code block (MathJax can't handle this)
              if (isDocumentLatex) {
                return (
                  <div className="not-prose my-4">
                    <div className="math-display-wrapper bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md p-4 overflow-x-auto">
                      <div className="text-center text-gray-600 dark:text-gray-400 mb-2 text-sm">
                        LaTeX Document (not renderable as math)
                      </div>
                      <pre className="text-left font-mono text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
                        {mathContent}
                      </pre>
                    </div>
                  </div>
                );
              }

              // If it's math LaTeX without Vietnamese, render with MathJax
              if (!hasVietnameseChars && isMathLatex) {
                return (
                  <div className="not-prose my-4">
                    <div className="math-display-wrapper bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md p-4 overflow-x-auto">
                      <MathJaxRenderer
                        latex={mathContent}
                        display={true}
                        className="text-center"
                      />
                    </div>
                  </div>
                );
              }
              // If not valid math LaTeX, continue to normal code block rendering
            }

            // Simple header styling - no language-specific colors
            const getHeaderStyle = () => {
              return 'bg-gray-100/50 dark:bg-gray-700/50 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors';
            };

            // Generate stable ID based on content
            const codeId = useMemo(() => {
              const content = String(children);
              return `code-${content.slice(0, 20).replace(/\W/g, '')}-${content.length}`;
            }, [children]);

            const copyToClipboard = async (text: string, id: string) => {
              try {
                await navigator.clipboard.writeText(text);
                setCopiedStates(prev => ({ ...prev, [id]: true }));
                setTimeout(() => {
                  setCopiedStates(prev => ({ ...prev, [id]: false }));
                }, 2000);
              } catch (err) {
                console.error('Failed to copy:', err);
              }
            };

            const toggleCollapse = (id: string) => {
              setCollapsedStates(prev => ({ ...prev, [id]: !prev[id] }));
            };

            const isCopied = copiedStates[codeId] || false;
            const isCollapsed = collapsedStates[codeId] || false;
            const codeString = String(children).replace(/\n$/, '');

            return (
              <div className="not-prose my-4">
                <div className="github-code-block rounded-md overflow-hidden group">
                  {language && (
                    <div className="github-code-header flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-800">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                        {language}
                      </span>
                      <div className="flex items-center space-x-2">
                        {/* Collapse/Expand Button */}
                        <button
                          onClick={() => toggleCollapse(codeId)}
                          className="flex items-center space-x-1 px-2 py-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-all duration-200"
                          title={isCollapsed ? "Expand code" : "Collapse code"}
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            {isCollapsed ? (
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            ) : (
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                            )}
                          </svg>
                          <span>{isCollapsed ? "Expand" : "Collapse"}</span>
                        </button>

                        {/* Copy Button */}
                        <button
                          onClick={() => copyToClipboard(codeString, codeId)}
                          className="flex items-center space-x-1 px-2 py-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-all duration-200"
                          title={isCopied ? "Copied!" : "Copy code"}
                        >
                          {isCopied ? (
                            <>
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              <span>Copied</span>
                            </>
                          ) : (
                            <>
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                  <div className="relative">
                    {!isCollapsed && (
                      <>
                        {language ? (
                          <div className="bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600">
                            {console.log('🎨 Using SyntaxHighlighter for language:', language)}
                            <SyntaxHighlighter
                              language={language}
                              style={isDarkMode ? customDarkTheme : github}
                              customStyle={{
                                margin: 0,
                                padding: '1rem',
                                backgroundColor: 'transparent',
                                border: 'none',
                                borderRadius: 0,
                                fontSize: '0.875rem',
                                lineHeight: '1.25rem'
                              }}
                              {...props}
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          </div>
                        ) : (
                          <pre className="p-4 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 overflow-x-auto">
                            <code className="font-mono text-sm text-gray-800 dark:text-gray-200" {...props}>
                              {children}
                            </code>
                          </pre>
                        )}
                      </>
                    )}

                    {/* Collapsed state */}
                    {isCollapsed && (
                      <div className="p-4 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-center">
                        <span className="text-sm text-gray-500 dark:text-gray-400 italic">
                          Code collapsed - click expand to view
                        </span>
                      </div>
                    )}

                    {/* Copy button for code blocks without language header */}
                    {!language && (
                      <div className="absolute top-2 right-2 flex items-center space-x-2">
                        <button
                          onClick={() => toggleCollapse(codeId)}
                          className="flex items-center space-x-1 px-2 py-1 text-xs bg-gray-200/80 dark:bg-gray-700/80 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                          title={isCollapsed ? "Expand code" : "Collapse code"}
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            {isCollapsed ? (
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            ) : (
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                            )}
                          </svg>
                        </button>
                        <button
                          onClick={() => copyToClipboard(codeString, codeId)}
                          className="flex items-center space-x-1 px-2 py-1 text-xs bg-gray-200/80 dark:bg-gray-700/80 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                          title={isCopied ? "Copied!" : "Copy code"}
                        >
                          {isCopied ? (
                            <>
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </>
                          ) : (
                            <>
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          },



          // Div element - handle block content
          div: ({ children, ...props }) => {
            return (
              <div className="my-2" {...props}>
                {children}
              </div>
            );
          },

          // Headings - GitHub style
          h1: ({ children }) => (
            <h1 className="github-h1 text-2xl font-semibold text-gray-900 dark:text-white mt-6 mb-4 first:mt-0 pb-2 border-b border-gray-200 dark:border-gray-700">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="github-h2 text-xl font-semibold text-gray-900 dark:text-white mt-5 mb-3 first:mt-0 pb-2 border-b border-gray-200 dark:border-gray-700">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="github-h3 text-lg font-semibold text-gray-900 dark:text-white mt-4 mb-2 first:mt-0">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="github-h4 text-base font-semibold text-gray-900 dark:text-white mt-3 mb-2">
              {children}
            </h4>
          ),
          h5: ({ children }) => (
            <h5 className="github-h5 text-sm font-semibold text-gray-900 dark:text-white mt-2 mb-1">
              {children}
            </h5>
          ),
          h6: ({ children }) => (
            <h6 className="github-h6 text-xs font-semibold text-gray-600 dark:text-gray-400 mt-2 mb-1">
              {children}
            </h6>
          ),

          // Lists - GitHub style
          ul: ({ children }) => (
            <ul className="github-list list-disc pl-6 mb-4 space-y-1 text-gray-900 dark:text-gray-100">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="github-list list-decimal pl-6 mb-4 space-y-1 text-gray-900 dark:text-gray-100">
              {children}
            </ol>
          ),
          li: ({ children, ...props }) => {
            // Check if li contains block elements
            const childArray = React.Children.toArray(children);
            const hasBlockElements = childArray.some(child => {
              if (React.isValidElement(child)) {
                const type = child.type;
                if (typeof type === 'string') {
                  return ['div', 'pre', 'blockquote', 'ul', 'ol', 'table', 'p'].includes(type);
                }
              }
              return false;
            });

            if (hasBlockElements) {
              return (
                <li className="text-universal-14 leading-relaxed" {...props}>
                  <div className="space-y-2">
                    {children}
                  </div>
                </li>
              );
            }

            return (
              <li className="text-universal-14 leading-relaxed" {...props}>
                {children}
              </li>
            );
          },
          
          // Links - GitHub style
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="github-link text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:underline transition-colors duration-200"
            >
              {children}
            </a>
          ),

          // Blockquotes - GitHub style
          blockquote: ({ children }) => (
            <blockquote className="github-blockquote border-l-4 border-blue-200 dark:border-blue-700 pl-4 py-2 my-4 bg-blue-50/50 dark:bg-blue-900/20 rounded-r">
              <div className="text-gray-700 dark:text-gray-300">
                {children}
              </div>
            </blockquote>
          ),
          
          // Tables - GitHub style
          table: ({ children }) => (
            <div className="github-table-wrapper overflow-x-auto my-4 border border-gray-200 dark:border-gray-700 rounded-md">
              <table className="min-w-full border-collapse">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-gray-50 dark:bg-gray-800">
              {children}
            </thead>
          ),
          th: ({ children }) => (
            <th className="github-th px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-600">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="github-td px-4 py-3 text-sm text-gray-900 dark:text-gray-100 border-b border-gray-200 dark:border-gray-600">
              {children}
            </td>
          ),
          tbody: ({ children }) => (
            <tbody className="github-tbody divide-y divide-gray-200 dark:divide-gray-700">
              {children}
            </tbody>
          ),
          tr: ({ children, ...props }) => (
            <tr className="github-tr hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors duration-150" {...props}>
              {children}
            </tr>
          ),

          // Horizontal rule - GitHub style
          hr: () => (
            <hr className="github-hr my-6 border-0 border-t border-gray-200 dark:border-gray-700" />
          ),
          
          // Strong and emphasis - GitHub style with forced styling
          strong: ({ children }) => (
            <strong className="force-bold text-gray-900 dark:text-white" style={{ fontWeight: 600 }}>
              {children}
            </strong>
          ),
          b: ({ children }) => (
            <b className="force-bold text-gray-900 dark:text-white" style={{ fontWeight: 600 }}>
              {children}
            </b>
          ),
          em: ({ children }) => (
            <em className="force-italic text-gray-700 dark:text-gray-300" style={{ fontStyle: 'italic' }}>
              {children}
            </em>
          ),
          i: ({ children }) => (
            <i className="force-italic text-gray-700 dark:text-gray-300" style={{ fontStyle: 'italic' }}>
              <MathTextProcessor>{children}</MathTextProcessor>
            </i>
          ),
          // Text processor for all text content
          text: ({ children }) => {
            return <MathTextProcessor>{children}</MathTextProcessor>;
          },
        }}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
};

// Math wrapper component to handle overflow
const MathWrapper: React.FC<{ children: React.ReactNode; displayMode?: boolean }> = ({
  children,
  displayMode = false
}) => {
  if (displayMode) {
    return (
      <div className="math-display-wrapper my-4 overflow-x-auto">
        <div className="min-w-0">
          {children}
        </div>
      </div>
    );
  }

  return (
    <span className="math-inline-wrapper inline-block max-w-full overflow-x-auto">
      {children}
    </span>
  );
};

export default MessageRenderer;
