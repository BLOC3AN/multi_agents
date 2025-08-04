import React, { useEffect, useRef, useState } from 'react';
import { loadMathJax, renderMath, renderInlineMath, renderDisplayMath } from '../utils/mathJaxLoader';

interface MathJaxRendererProps {
  latex: string;
  display?: boolean;
  className?: string;
}

export const MathJaxRenderer: React.FC<MathJaxRendererProps> = ({ 
  latex, 
  display = false, 
  className = '' 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [renderedHtml, setRenderedHtml] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const renderLatex = async () => {
      setIsLoading(true);
      setError(null);

      try {
        await loadMathJax();
        
        const html = display 
          ? await renderDisplayMath(latex)
          : await renderInlineMath(latex);
        
        setRenderedHtml(html);
      } catch (err) {
        console.error('MathJax rendering error:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    };

    if (latex.trim()) {
      renderLatex();
    } else {
      setIsLoading(false);
    }
  }, [latex, display]);

  if (isLoading) {
    return (
      <span className={`inline-block animate-pulse ${className}`}>
        {display ? (
          <div className="h-8 bg-gray-200 rounded w-32 mx-auto"></div>
        ) : (
          <span className="h-4 bg-gray-200 rounded w-16 inline-block"></span>
        )}
      </span>
    );
  }

  if (error) {
    return (
      <span className={`text-red-500 ${className}`}>
        Error rendering math: {latex}
      </span>
    );
  }

  if (display) {
    return (
      <div 
        className={`math-display-container my-4 overflow-x-auto ${className}`}
        dangerouslySetInnerHTML={{ __html: renderedHtml }}
      />
    );
  }

  return (
    <span 
      className={`math-inline-container ${className}`}
      dangerouslySetInnerHTML={{ __html: renderedHtml }}
    />
  );
};

interface MathJaxBlockProps {
  children: React.ReactNode;
  className?: string;
}

export const MathJaxBlock: React.FC<MathJaxBlockProps> = ({ 
  children, 
  className = '' 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const setupMathJax = async () => {
      try {
        await loadMathJax();
        if (containerRef.current) {
          await renderMath(containerRef.current);
        }
        setIsReady(true);
      } catch (error) {
        console.error('MathJax setup error:', error);
        setIsReady(true); // Still show content even if MathJax fails
      }
    };

    setupMathJax();
  }, [children]);

  return (
    <div 
      ref={containerRef}
      className={`mathjax-block ${isReady ? 'ready' : 'loading'} ${className}`}
    >
      {children}
    </div>
  );
};

// Helper component for processing mixed content with LaTeX
interface MixedLatexRendererProps {
  content: string;
  className?: string;
}

export const MixedLatexRenderer: React.FC<MixedLatexRendererProps> = ({ 
  content, 
  className = '' 
}) => {
  const parts = content.split(/(\$[^$]*\$)/);
  
  return (
    <span className={className}>
      {parts.map((part, index) => {
        if (part.startsWith('$') && part.endsWith('$') && part.length > 2) {
          const mathContent = part.slice(1, -1);
          return (
            <MathJaxRenderer 
              key={index} 
              latex={mathContent} 
              display={false}
            />
          );
        } else {
          return <span key={index}>{part}</span>;
        }
      })}
    </span>
  );
};

// Hook for MathJax readiness
export const useMathJax = () => {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    loadMathJax().then(() => {
      setIsReady(true);
    }).catch((error) => {
      console.error('Failed to load MathJax:', error);
    });
  }, []);

  return isReady;
};
