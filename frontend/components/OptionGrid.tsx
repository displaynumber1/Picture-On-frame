import React from 'react';

interface OptionGridProps {
  title: string;
  options: string[];
  selected: string;
  onSelect: (value: string) => void;
  customKey?: string;
  customValue?: string;
  onCustomChange?: (value: string) => void;
}

const OptionGrid: React.FC<OptionGridProps> = ({ 
  title, 
  options, 
  selected, 
  onSelect, 
  customKey, 
  customValue, 
  onCustomChange 
}) => {
  return (
    <div className="space-y-4">
      <h3 className="text-[10px] font-bold text-purple-950 tracking-widest uppercase">{title}</h3>
      <div className="grid grid-cols-2 gap-2">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onSelect(opt)}
            className={`py-2 px-3 text-xs rounded-lg border transition-all text-left ${
              selected === opt
                ? 'bg-purple-900 border-purple-900 text-purple-50 shadow-lg'
                : 'bg-white border-purple-50 text-purple-700 hover:border-pink-200 hover:bg-pink-50/30'
            }`}
          >
            {opt}
          </button>
        ))}
      </div>
      {customKey && selected === customKey && onCustomChange && (
        <textarea
          value={customValue || ''}
          onChange={(e) => onCustomChange(e.target.value)}
          placeholder={`Enter custom ${title.toLowerCase()} details...`}
          className="w-full p-3 text-xs border border-purple-100 bg-white/50 rounded-xl focus:ring-2 focus:ring-pink-300 outline-none min-h-[80px] text-purple-800"
        />
      )}
    </div>
  );
};

export default OptionGrid;



