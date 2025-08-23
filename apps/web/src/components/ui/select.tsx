import React, { useState } from 'react';

interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  disabled?: boolean;
}

interface SelectTriggerProps {
  children: React.ReactNode;
  className?: string;
}

interface SelectContentProps {
  children: React.ReactNode;
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
}

interface SelectValueProps {
  placeholder?: string;
}

export const Select: React.FC<SelectProps> = ({ value, onValueChange, children, disabled }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="relative">
      {React.Children.map(children, child => 
        React.isValidElement(child) 
          ? React.cloneElement(child as React.ReactElement<any>, { 
              value, 
              onValueChange, 
              isOpen, 
              setIsOpen, 
              disabled 
            })
          : child
      )}
    </div>
  );
};

export const SelectTrigger: React.FC<SelectTriggerProps & any> = ({ 
  children, 
  className = '', 
  isOpen, 
  setIsOpen, 
  disabled 
}) => (
  <button
    type="button"
    disabled={disabled}
    onClick={() => setIsOpen?.(!isOpen)}
    className={`w-full px-3 py-2 text-left border border-gray-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 ${className}`}
  >
    {children}
  </button>
);

export const SelectContent: React.FC<SelectContentProps & any> = ({ 
  children, 
  isOpen, 
  setIsOpen, 
  onValueChange 
}) => {
  if (!isOpen) return null;
  
  return (
    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
      {React.Children.map(children, child =>
        React.isValidElement(child)
          ? React.cloneElement(child as React.ReactElement<any>, { 
              onValueChange, 
              setIsOpen 
            })
          : child
      )}
    </div>
  );
};

export const SelectItem: React.FC<SelectItemProps & any> = ({ 
  value, 
  children, 
  onValueChange, 
  setIsOpen 
}) => (
  <button
    type="button"
    onClick={() => {
      onValueChange?.(value);
      setIsOpen?.(false);
    }}
    className="w-full px-3 py-2 text-left hover:bg-gray-100 focus:outline-none focus:bg-gray-100"
  >
    {children}
  </button>
);

export const SelectValue: React.FC<SelectValueProps & any> = ({ 
  placeholder, 
  value 
}) => (
  <span className={value ? 'text-gray-900' : 'text-gray-500'}>
    {value || placeholder}
  </span>
);