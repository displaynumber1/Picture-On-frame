import React, { useRef } from 'react';

interface UploaderProps {
  label: string;
  onImageSelected: (base64: string) => void;
  preview?: string;
  className?: string;
  icon?: React.ReactNode;
}

const Uploader: React.FC<UploaderProps> = ({ label, onImageSelected, preview, className, icon }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        onImageSelected(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div 
      onClick={() => fileInputRef.current?.click()}
      className={`relative cursor-pointer border-2 border-dashed border-purple-200 rounded-2xl flex flex-col items-center justify-center p-4 transition-all hover:border-pink-400 hover:bg-pink-50/30 overflow-hidden ${className}`}
    >
      <input 
        type="file" 
        className="hidden" 
        ref={fileInputRef} 
        accept="image/*"
        onChange={handleFileChange} 
      />
      {preview ? (
        <img src={preview} alt="Preview" className="w-full h-full object-cover rounded-xl" />
      ) : (
        <>
          <div className="text-pink-400 mb-2">
            {icon || (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
            )}
          </div>
          <p className="text-xs font-medium text-purple-700 uppercase tracking-wider">{label}</p>
        </>
      )}
      {preview && (
        <div className="absolute inset-0 bg-purple-950/40 opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[2px]">
            <span className="text-purple-50 text-xs font-bold uppercase tracking-widest">Change</span>
        </div>
      )}
    </div>
  );
};

export default Uploader;



