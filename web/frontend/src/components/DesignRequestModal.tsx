import { useState, useRef, ChangeEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, X, Image as ImageIcon } from "lucide-react";

interface DesignRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (image: string | null) => void;
}

const DesignRequestModal = ({ isOpen, onClose, onGenerate }: DesignRequestModalProps) => {
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [vision, setVision] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setUploadedImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleGenerate = () => {
    onGenerate(uploadedImage);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 z-40 bg-black/60"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            onClick={onClose}
          />

          {/* Glass Modal */}
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 pointer-events-none"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="glass-crystal w-full max-w-md pointer-events-auto"
              initial={{ opacity: 0, y: 60, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 40, scale: 0.95 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            >
              {/* Close Button */}
              <button
                onClick={onClose}
                className="absolute top-4 right-4 text-white/60 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="p-8 md:p-10">
                {/* Title */}
                <h2 className="font-display text-3xl md:text-4xl font-light text-white mb-8">
                  New Vision
                </h2>

                {/* Upload Zone */}
                <div className="mb-6">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept="image/*"
                    className="hidden"
                  />
                  
                  <div
                    onClick={handleUploadClick}
                    className="upload-zone aspect-[4/3] w-full"
                  >
                    {uploadedImage ? (
                      <div className="relative w-full h-full">
                        <img
                          src={uploadedImage}
                          alt="Uploaded room"
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                          <span className="font-body text-xs uppercase tracking-widest text-white">
                            Change Photo
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center py-12">
                        <div className="w-10 h-10 border border-white/30 flex items-center justify-center mb-4">
                          <Plus className="w-5 h-5 text-white/60" />
                        </div>
                        <span className="font-body text-xs uppercase tracking-widest text-white/60">
                          Tap to upload room photo
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Vision Input */}
                <div className="mb-8">
                  <textarea
                    value={vision}
                    onChange={(e) => setVision(e.target.value)}
                    placeholder="Describe your dream space..."
                    rows={3}
                    className="input-editorial w-full resize-none font-body text-sm"
                  />
                </div>

                {/* Submit Button */}
                <button
                  onClick={handleGenerate}
                  className="btn-editorial w-full bg-charcoal text-bone hover:bg-charcoal/90"
                >
                  Generate
                </button>
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default DesignRequestModal;
