import { motion } from "framer-motion";
import heroImage from "@/assets/hero-interior.jpg";

interface HomeScreenProps {
  onStartProject: () => void;
}

const HomeScreen = ({ onStartProject }: HomeScreenProps) => {
  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      {/* Full-screen Background Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${heroImage})` }}
      />
      
      {/* Subtle vignette - not heavy white fade */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />

      {/* Header - Minimal Logo */}
      <motion.header 
        className="absolute top-0 left-0 right-0 z-10 p-6 md:p-10"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.3 }}
      >
        <h2 className="font-display text-xl md:text-2xl font-light tracking-wider text-white text-shadow-editorial">
          CasAI
        </h2>
      </motion.header>

      {/* Hero Content - Bottom Left */}
      <div className="absolute bottom-0 left-0 right-0 p-6 md:p-10 lg:p-16">
        <motion.div
          className="max-w-4xl"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
        >
          <h1 className="font-display text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-light leading-none tracking-tight text-white text-shadow-editorial mb-8 md:mb-12">
            Redefine Your<br />Reality.
          </h1>
        </motion.div>

        {/* CTA Button - Bottom Center */}
        <motion.div 
          className="flex justify-center md:justify-start mt-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
        >
          <button
            onClick={onStartProject}
            className="btn-editorial bg-charcoal text-bone hover:bg-charcoal/90"
          >
            Start Project
          </button>
        </motion.div>
      </div>
    </div>
  );
};

export default HomeScreen;
