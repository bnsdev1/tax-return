import React from 'react';

interface SeparatorProps {
  className?: string;
}

export const Separator: React.FC<SeparatorProps> = ({ className = '' }) => (
  <hr className={`border-gray-200 ${className}`} />
);