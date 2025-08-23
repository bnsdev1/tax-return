import React from 'react';

interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  children: React.ReactNode;
  className?: string;
}

export const Label: React.FC<LabelProps> = ({ children, className = '', ...props }) => (
  <label 
    className={`block text-sm font-medium text-gray-700 mb-1 ${className}`}
    {...props}
  >
    {children}
  </label>
);