import React, { useState, useEffect } from 'react';
import { Upload, Sparkles, ArrowRight, Check, ShoppingBag, Loader2, Zap, ChevronRight, Github } from 'lucide-react';

// Curated Luxury Styles
const STYLES = [
  { id: 'modern', name: 'MODERN MINIMALIST', img: 'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&q=80&w=400' },
  { id: 'classic', name: 'PARISIAN CHIC', img: 'https://images.unsplash.com/photo-1600607686527-6fb886090705?auto=format&fit=crop&q=80&w=400' },
  { id: 'industrial', name: 'URBAN LOFT', img: 'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&q=80&w=400' },
  { id: 'japandi', name: 'JAPANDI ZEN', img: 'https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?auto=format&fit=crop&q=80&w=400' }
];

export default function App() {
  const [step, setStep] = useState(1);
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedStyle, setSelectedStyle] = useState(null);
  const [processingStage, setProcessingStage] = useState(0);
  const [resultData, setResultData] = useState(null);
  const [sliderPosition, setSliderPosition] = useState(50);

  // Load elegant fonts
  useEffect(() => {
    const link = document.createElement('link');
    link.href = 'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=Lato:wght@300;400;700&display=swap';
    link.rel = 'stylesheet';
    document.head.appendChild(link);
  }, []);

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImage(reader.result);
        setStep(2);
      };
      reader.readAsDataURL(file);
    }
  };

  const useDemoImage = () => {
    setSelectedImage('https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&q=80&w=800');
    setStep(2);
  };

  // Connect to backend
  useEffect(() => {
    if (step === 3 && selectedImage) {
      const processDesign = async () => {
        try {
          // Simulate loading stages for UX
          const stages = [
            "Analyzing Architecture...",
            "Detecting Furniture...",
            "Applying Aesthetic...",
            "Rendering High-Res Image...",
            "Finalizing Details..."
          ];
          
          let currentStage = 0;
          const stageInterval = setInterval(() => {
            if (currentStage < stages.length) {
              setProcessingStage(currentStage);
              currentStage++;
            }
          }, 1500);

          // Prepare data
          const response = await fetch(selectedImage);
          const blob = await response.blob();
          const formData = new FormData();
          formData.append('image', blob, 'upload.jpg');
          formData.append('style', selectedStyle?.id || 'modern');

          // Send to Python backend
          const res = await fetch('http://localhost:5000/api/predict', {
            method: 'POST',
            body: formData,
          });

          const data = await res.json();
          clearInterval(stageInterval);

          if (data.status === 'success') {
            setResultData(data);
            setStep(4);
          } else {
            alert('Error: ' + (data.error || 'Unknown error'));
            setStep(1);
          }
        } catch (error) {
          console.error("Connection Error:", error);
          alert("Could not connect to server. Please ensure 'app.py' is running.");
          setStep(1);
        }
      };

      processDesign();
    }
  }, [step, selectedImage, selectedStyle]);

  const resetApp = () => {
    setStep(1);
    setSelectedImage(null);
    setSelectedStyle(null);
    setProcessingStage(0);
    setResultData(null);
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7] text-[#1A1A1A] font-sans selection:bg-black selection:text-white">
      
      {/* Minimalist Header */}
      <header className="fixed w-full top-0 z-50 bg-[#FDFBF7]/90 backdrop-blur-md border-b border-[#E5E5E5]">
        <div className="max-w-7xl mx-auto px-8 h-24 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={resetApp}>
            <span className="font-serif text-3xl tracking-widest font-medium italic">CasAI</span>
          </div>
          
          <nav className="hidden md:flex gap-12 text-[10px] tracking-[0.25em] font-light uppercase text-gray-400">
            <span className={step === 1 ? "text-black font-bold border-b border-black pb-1 transition-all" : "hover:text-black transition-colors"}>Upload</span>
            <span className={step === 2 ? "text-black font-bold border-b border-black pb-1 transition-all" : "hover:text-black transition-colors"}>Style</span>
            <span className={step >= 3 ? "text-black font-bold border-b border-black pb-1 transition-all" : "hover:text-black transition-colors"}>Result</span>
          </nav>
        </div>
      </header>

      <main className="pt-32 pb-20 px-8 max-w-7xl mx-auto min-h-screen flex flex-col justify-center">
        
        {/* STEP 1: HERO & UPLOAD */}
        {step === 1 && (
          <div className="flex flex-col items-center text-center space-y-16 animate-fade-in">
            <div className="space-y-8 max-w-4xl">
              <span className="text-[10px] font-bold tracking-[0.4em] uppercase text-gray-400">Interior Intelligence</span>
              <h1 className="text-7xl md:text-8xl font-serif font-light leading-[1.1] text-gray-900">
                Design your home <br/> 
                <span className="italic font-light text-gray-500">from comfort</span>
              </h1>
              <p className="text-lg font-light text-gray-500 max-w-xl mx-auto leading-relaxed tracking-wide">
                Experience the future of interior design. Upload a photo and let our AI curate a bespoke space tailored to your unique taste.
              </p>
            </div>

            <div className="flex flex-col items-center gap-6">
              <div className="relative group cursor-pointer overflow-hidden">
                <input 
                  type="file" 
                  className="absolute inset-0 w-full h-full opacity-0 z-20 cursor-pointer"
                  accept="image/*"
                  onChange={handleImageUpload}
                />
                <button className="relative z-10 bg-[#1A1A1A] text-white px-16 py-6 text-xs tracking-[0.2em] uppercase transition-all duration-500 shadow-xl group-hover:bg-white group-hover:text-black group-hover:shadow-2xl border border-black">
                  Upload Photo
                </button>
              </div>

              <button 
                onClick={useDemoImage}
                className="text-[10px] tracking-[0.15em] uppercase text-gray-400 border-b border-transparent hover:border-gray-400 hover:text-black transition-all"
              >
                Try with Demo Image
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: STYLE SELECTION */}
        {step === 2 && (
          <div className="space-y-16 animate-fade-in w-full">
            <div className="text-center space-y-6">
              <span className="text-[10px] font-bold tracking-[0.3em] text-gray-400 uppercase">Step 02</span>
              <h2 className="text-5xl font-serif font-light">Choose your Aesthetic</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              {STYLES.map((style) => (
                <div 
                  key={style.id}
                  onClick={() => setSelectedStyle(style)}
                  className={`group relative aspect-[3/4] cursor-pointer transition-all duration-700 ${selectedStyle?.id === style.id ? 'grayscale-0' : 'grayscale hover:grayscale-0'}`}
                >
                  <div className={`absolute inset-0 border-[1px] transition-all duration-500 p-3 ${selectedStyle?.id === style.id ? 'border-black' : 'border-transparent group-hover:border-gray-200'}`}>
                    <div className="w-full h-full overflow-hidden relative">
                      <img src={style.img} alt={style.name} className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" />
                      {selectedStyle?.id === style.id && (
                        <div className="absolute inset-0 bg-black/20 flex items-center justify-center backdrop-blur-[2px]">
                          <div className="bg-white/90 p-6 rounded-full shadow-2xl">
                            <Check className="w-6 h-6 text-black" />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="mt-6 text-center space-y-2">
                    <h3 className="font-serif text-2xl italic">{style.name.split(' ')[0]}</h3>
                    <p className="text-[10px] tracking-[0.2em] text-gray-400 uppercase">{style.name.split(' ').slice(1).join(' ')}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-center pt-8">
              <button 
                disabled={!selectedStyle}
                onClick={() => setStep(3)}
                className={`flex items-center gap-6 px-20 py-6 text-xs tracking-[0.2em] uppercase border border-black transition-all duration-500 ${selectedStyle ? 'bg-black text-white hover:bg-white hover:text-black' : 'bg-transparent text-gray-300 border-gray-200 cursor-not-allowed'}`}
              >
                Generate Design
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: PROCESSING */}
        {step === 3 && (
          <div className="flex flex-col items-center justify-center space-y-12 animate-fade-in py-24">
            <div className="relative">
              <div className="w-32 h-32 border-[1px] border-gray-100 rounded-full"></div>
              <div className="w-32 h-32 border-[1px] border-black rounded-full border-t-transparent animate-spin absolute inset-0 duration-[2s]"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-black/30 animate-pulse" />
              </div>
            </div>
            
            <div className="text-center space-y-4">
              <h3 className="font-serif text-3xl italic">Curating your space...</h3>
              <div className="h-4 overflow-hidden">
                <p className="text-[10px] tracking-[0.3em] uppercase text-gray-400 animate-pulse">
                  {processingStage === 0 && "Analyzing Architecture"}
                  {processingStage === 1 && "Measuring Lighting"}
                  {processingStage === 2 && "Selecting Furniture"}
                  {processingStage === 3 && "Rendering Details"}
                  {processingStage === 4 && "Finalizing Vision"}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* STEP 4: RESULT */}
        {step === 4 && resultData && (
          <div className="space-y-24 animate-fade-in w-full">
            <div className="flex flex-col md:flex-row justify-between items-end gap-8 border-b border-gray-200 pb-8">
              <div className="space-y-4">
                <span className="text-[10px] font-bold tracking-[0.3em] text-gray-400 uppercase">The Transformation</span>
                <h2 className="text-6xl font-serif font-light">Your New Vision</h2>
              </div>
              <button onClick={resetApp} className="text-[10px] tracking-[0.2em] border-b border-black pb-1 hover:opacity-50 transition-opacity uppercase">
                Design Another Room
              </button>
            </div>

            {/* Result Image Slider */}
            <div className="w-full bg-gray-50 shadow-2xl p-4 md:p-8 border border-gray-100 select-none">
               <div className="relative aspect-[16/9] w-full overflow-hidden cursor-ew-resize">
                  {/* After Image */}
                  <img 
                    src={resultData.result_image} 
                    alt="Redesigned Room" 
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                  
                  {/* Before Image (Clipped) */}
                  <div 
                    className="absolute inset-0 w-full h-full overflow-hidden border-r border-white"
                    style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
                  >
                    <img 
                      src={selectedImage} 
                      alt="Before" 
                      className="absolute inset-0 w-full h-full object-cover filter grayscale contrast-125"
                    />
                    <div className="absolute top-8 left-8 bg-black text-white text-[10px] tracking-[0.2em] px-4 py-2 uppercase font-bold">Original</div>
                  </div>

                  <div className="absolute top-8 right-8 bg-white text-black text-[10px] tracking-[0.2em] px-4 py-2 uppercase font-bold shadow-lg">
                    {selectedStyle?.name} Edition
                  </div>

                  {/* Slider Handle */}
                  <div 
                    className="absolute top-0 bottom-0 w-[1px] bg-white z-20 pointer-events-none"
                    style={{ left: `${sliderPosition}%` }}
                  >
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-xl">
                      <div className="w-8 h-8 rounded-full border border-gray-200 flex items-center justify-center gap-2">
                        <div className="w-[1px] h-3 bg-black"></div>
                        <div className="w-[1px] h-3 bg-black"></div>
                      </div>
                    </div>
                  </div>

                  {/* Invisible Range Input */}
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={sliderPosition}
                    onChange={(e) => setSliderPosition(e.target.value)}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-30"
                  />
               </div>
            </div>

            {/* Product Recommendations */}
            {resultData.products && (
              <div className="space-y-12">
                <div className="text-center space-y-6">
                  <h3 className="font-serif text-4xl italic">Shop the Look</h3>
                  <div className="w-16 h-[1px] bg-black mx-auto"></div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
                  {resultData.products.map((product, idx) => (
                    <div key={idx} className="group cursor-pointer space-y-6">
                      <div className="aspect-[4/5] bg-[#F5F5F5] overflow-hidden relative">
                        {product.img && <img src={product.img} alt={product.name} className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-105 mix-blend-multiply" />}
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-500"></div>
                        <button className="absolute bottom-0 left-0 w-full bg-white py-6 text-[10px] tracking-[0.2em] uppercase font-bold translate-y-full group-hover:translate-y-0 transition-transform duration-500 border-t border-gray-100 hover:bg-black hover:text-white">
                          Add to Collection
                        </button>
                      </div>
                      <div className="text-center space-y-2">
                        <h4 className="font-serif text-2xl">{product.name}</h4>
                        <p className="text-xs text-gray-500 font-bold tracking-widest">{product.price}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

      </main>
      
      {/* Footer */}
      <footer className="border-t border-gray-200 py-12 text-center mt-20">
        <p className="text-[10px] tracking-[0.3em] text-gray-400 uppercase">Powered by CasAI Architecture</p>
      </footer>
    </div>
  );
}