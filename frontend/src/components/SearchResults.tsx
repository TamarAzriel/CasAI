import { motion } from "framer-motion";

interface Product {
  item_name: string;
  item_cat: string;
  item_price: number;
  item_url: string;
  item_img: string;
  similarity?: number;
}

interface SearchResultsProps {
  results: Product[];
}

const SearchResults = ({ results }: SearchResultsProps) => {
  if (!results || results.length === 0) return null;

  return (
    <section id="results" className="py-24 px-6 md:px-12 bg-stone-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16 text-center"
        >
          <h2 className="font-display text-4xl md:text-5xl font-light text-charcoal mb-4">
            Curated For You
          </h2>
          <p className="font-body text-gray-500 max-w-lg mx-auto">
            Based on your vision, here are the best matches from our collection.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-12">
          {results.map((item, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              viewport={{ once: true }}
              className="group bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-500 cursor-default"
            >
              {/* Image Container */}
              <div className="aspect-[4/3] overflow-hidden bg-gray-100 relative">
                <img 
                  src={item.item_img} 
                  alt={item.item_name}
                  className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700 ease-out"
                />
                {/* Match Badge */}
                {item.similarity && (
                  <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase shadow-sm">
                    {Math.round(item.similarity * 100)}% Match
                  </div>
                )}
              </div>
              
              {/* Content */}
              <div className="p-8">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-widest mb-3">
                  {item.item_cat}
                </p>
                <h3 className="font-display text-2xl text-gray-900 mb-2 truncate">
                  {item.item_name}
                </h3>
                <div className="flex justify-between items-end mt-6 border-t border-gray-100 pt-6">
                  <span className="font-display text-xl text-gray-900">
                    ₪{item.item_price}
                  </span>
                  <a 
                    href={item.item_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn-editorial text-xs bg-charcoal text-white hover:bg-black px-6 py-2 rounded-full transition-colors"
                  >
                    View Details
                  </a>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default SearchResults;