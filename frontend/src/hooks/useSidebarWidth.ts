import { useState, useEffect } from 'react';

interface SidebarWidthConfig {
  expandedWidth: number;
  collapsedWidth: number;
  expandedWidthPx: string;
  collapsedWidthPx: string;
  // Derived sizes based on the base width
  sizes: {
    padding: {
      small: string;      // 0.01 ratio
      medium: string;     // 0.02 ratio
      large: string;      // 0.04 ratio
      xlarge: string;     // 0.05 ratio
    };
    gap: {
      small: string;      // 0.02 ratio
      medium: string;     // 0.025 ratio
      large: string;      // 0.03 ratio
    };
    button: {
      small: string;      // 0.04 ratio
      medium: string;     // 0.06 ratio
      large: string;      // 0.12 ratio
      xlarge: string;     // 0.15 ratio
      xxlarge: string;    // 0.25 ratio
    };
    font: {
      small: string;      // 0.04 ratio
      medium: string;     // 0.06 ratio
    };
  };
}

const STORAGE_KEY = 'sidebar-base-width';
const DEFAULT_RATIO = 1 / 7; // 1/7 of screen width
const COLLAPSED_RATIO = 0.3; // 30% of expanded width when collapsed

export const useSidebarWidth = (): SidebarWidthConfig => {
  const [baseWidth, setBaseWidth] = useState<number>(() => {
    // Try to get stored width first
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsedWidth = parseFloat(stored);
      if (!isNaN(parsedWidth) && parsedWidth > 0) {
        return parsedWidth;
      }
    }
    
    // Calculate initial width based on current screen size
    const initialWidth = window.innerWidth * DEFAULT_RATIO;
    localStorage.setItem(STORAGE_KEY, initialWidth.toString());
    return initialWidth;
  });

  // Only calculate once on mount, don't listen to resize events
  useEffect(() => {
    // If no stored width exists, calculate and store it
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      const initialWidth = window.innerWidth * DEFAULT_RATIO;
      setBaseWidth(initialWidth);
      localStorage.setItem(STORAGE_KEY, initialWidth.toString());
    }
  }, []);

  const expandedWidth = baseWidth;
  const collapsedWidth = baseWidth * COLLAPSED_RATIO;

  // Calculate all derived sizes based on the base width
  const sizes = {
    padding: {
      small: `${baseWidth * 0.01}px`,
      medium: `${baseWidth * 0.02}px`,
      large: `${baseWidth * 0.04}px`,
      xlarge: `${baseWidth * 0.05}px`,
    },
    gap: {
      small: `${baseWidth * 0.02}px`,
      medium: `${baseWidth * 0.025}px`,
      large: `${baseWidth * 0.03}px`,
    },
    button: {
      small: `${baseWidth * 0.04}px`,
      medium: `${baseWidth * 0.06}px`,
      large: `${baseWidth * 0.12}px`,
      xlarge: `${baseWidth * 0.15}px`,
      xxlarge: `${baseWidth * 0.25}px`,
    },
    font: {
      small: `${baseWidth * 0.04}px`,
      medium: `${baseWidth * 0.06}px`,
    },
  };

  return {
    expandedWidth,
    collapsedWidth,
    expandedWidthPx: `${expandedWidth}px`,
    collapsedWidthPx: `${collapsedWidth}px`,
    sizes,
  };
};

// Utility function to reset sidebar width (if needed for debugging)
export const resetSidebarWidth = (): void => {
  localStorage.removeItem(STORAGE_KEY);
  window.location.reload();
};
