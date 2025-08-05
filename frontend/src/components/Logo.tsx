import React from 'react';

interface LogoProps {
  size?: 'small' | 'medium' | 'large';
  showText?: boolean;
  className?: string;
  style?: React.CSSProperties;
  onClick?: () => void;
}

const Logo: React.FC<LogoProps> = ({
  size = 'medium',
  showText = true,
  className = '',
  style = {},
  onClick
}) => {
  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          iconSize: 'calc(100vw / 7 * 0.08)',
          fontSize: 'calc(100vw / 7 * 0.035)',
          titleSize: 'calc(100vw / 7 * 0.045)',
          subtitleSize: 'calc(100vw / 7 * 0.03)'
        };
      case 'large':
        return {
          iconSize: 'calc(100vw / 7 * 0.35)',
          fontSize: 'calc(100vw / 7 * 0.25)',
          titleSize: 'calc(100vw / 7 * 0.08)',
          subtitleSize: 'calc(100vw / 7 * 0.05)'
        };
      default: // medium
        return {
          iconSize: 'calc(100vw / 7 * 0.15)',
          fontSize: 'calc(100vw / 7 * 0.08)',
          titleSize: 'calc(100vw / 7 * 0.065)',
          subtitleSize: 'calc(100vw / 7 * 0.045)'
        };
    }
  };

  const sizeStyles = getSizeStyles();

  return (
    <div className={`flex items-center ${className}`} style={style}>
      {/* Logo Icon */}
      <div
        className={`flex items-center justify-center font-bold ${onClick ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''}`}
        style={{
          width: sizeStyles.iconSize,
          height: sizeStyles.iconSize,
          fontSize: sizeStyles.fontSize
        }}
        onClick={onClick}
        title={onClick ? 'Click to expand sidebar' : undefined}
      >
        🤖
      </div>
      
      {/* Logo Text */}
      {showText && (
        <div style={{ marginLeft: 'calc(100vw / 7 * 0.02)' }}>
          <div 
            className="font-bold text-gray-900 dark:text-white"
            style={{ fontSize: sizeStyles.titleSize }}
          >
            Agent
          </div>
          <div 
            className="text-gray-500 dark:text-gray-400"
            style={{ fontSize: sizeStyles.subtitleSize }}
          >
            AI System
          </div>
        </div>
      )}
    </div>
  );
};

export default Logo;
