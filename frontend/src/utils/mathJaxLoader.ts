// MathJax loader utility for React integration
declare global {
  interface Window {
    MathJax: any;
  }
}

export interface MathJaxConfig {
  tex: {
    inlineMath: string[][];
    displayMath: string[][];
    processEscapes: boolean;
    processEnvironments: boolean;
    packages: string[];
  };
  svg: {
    fontCache: string;
  };
  startup: {
    ready: () => void;
  };
}

let mathJaxLoaded = false;
let mathJaxPromise: Promise<void> | null = null;

const defaultConfig: MathJaxConfig = {
  tex: {
    inlineMath: [['$', '$']],
    displayMath: [['$$', '$$']],
    processEscapes: true,
    processEnvironments: true,
    packages: ['base', 'ams', 'newcommand', 'configmacros', 'action']
  },
  svg: {
    fontCache: 'global'
  },
  startup: {
    ready: () => {
      window.MathJax.startup.defaultReady();
      mathJaxLoaded = true;
    }
  }
};

export const loadMathJax = (): Promise<void> => {
  if (mathJaxLoaded && window.MathJax) {
    return Promise.resolve();
  }

  if (mathJaxPromise) {
    return mathJaxPromise;
  }

  mathJaxPromise = new Promise((resolve, reject) => {
    // Set MathJax configuration
    window.MathJax = defaultConfig;

    // Create script element
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js';
    script.async = true;

    script.onload = () => {
      // Wait for MathJax to be ready
      const checkReady = () => {
        if (window.MathJax && window.MathJax.startup && window.MathJax.startup.document) {
          mathJaxLoaded = true;
          resolve();
        } else {
          setTimeout(checkReady, 100);
        }
      };
      checkReady();
    };

    script.onerror = () => {
      reject(new Error('Failed to load MathJax'));
    };

    document.head.appendChild(script);
  });

  return mathJaxPromise;
};

export const renderMath = async (element: HTMLElement): Promise<void> => {
  await loadMathJax();
  
  if (window.MathJax && window.MathJax.typesetPromise) {
    try {
      await window.MathJax.typesetPromise([element]);
    } catch (error) {
      console.warn('MathJax rendering failed:', error);
    }
  }
};

export const renderInlineMath = async (latex: string): Promise<string> => {
  await loadMathJax();

  if (window.MathJax && window.MathJax.tex2svg) {
    try {
      // Clean up common LaTeX issues
      const cleanLatex = latex
        .replace(/\\begin\{document\}.*?\\end\{document\}/gs, '') // Remove document wrapper
        .replace(/\\documentclass.*?\n/g, '') // Remove documentclass
        .replace(/\\usepackage.*?\n/g, '') // Remove usepackage
        .trim();

      if (!cleanLatex) {
        return `<span class="text-gray-500 italic">Empty math expression</span>`;
      }

      const result = window.MathJax.tex2svg(cleanLatex, { display: false });
      return result.outerHTML;
    } catch (error) {
      console.warn('MathJax inline rendering failed:', error);
      return `<span class="text-red-500 text-sm" title="LaTeX Error: ${error}">⚠️ ${latex}</span>`;
    }
  }

  return `<span class="text-blue-600 font-mono">${latex}</span>`;
};

export const renderDisplayMath = async (latex: string): Promise<string> => {
  await loadMathJax();

  if (window.MathJax && window.MathJax.tex2svg) {
    try {
      // Clean up common LaTeX issues
      const cleanLatex = latex
        .replace(/\\begin\{document\}.*?\\end\{document\}/gs, '') // Remove document wrapper
        .replace(/\\documentclass.*?\n/g, '') // Remove documentclass
        .replace(/\\usepackage.*?\n/g, '') // Remove usepackage
        .trim();

      if (!cleanLatex) {
        return `<div class="text-gray-500 italic text-center">Empty math expression</div>`;
      }

      const result = window.MathJax.tex2svg(cleanLatex, { display: true });
      return result.outerHTML;
    } catch (error) {
      console.warn('MathJax display rendering failed:', error);
      return `<div class="text-red-500 text-center text-sm" title="LaTeX Error: ${error}">
        <div class="mb-2">⚠️ LaTeX Rendering Error</div>
        <div class="font-mono text-xs bg-red-50 dark:bg-red-900/20 p-2 rounded border">
          ${latex}
        </div>
      </div>`;
    }
  }

  return `<div class="text-blue-600 font-mono text-center">${latex}</div>`;
};

export const isMathJaxReady = (): boolean => {
  return mathJaxLoaded && !!window.MathJax;
};
