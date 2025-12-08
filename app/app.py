"""Streamlit Application for IKEA Furniture Recommender."""

import streamlit as st
from PIL import Image
import os
import shutil
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from new modular structure
from core.config import DETECT_DIR, UPLOADS_DIR, ensure_directories
from core.recommender import Recommender
from utils.display import DisplayHelper
from models import (
    load_yolo_model,
    load_similarity_model,
    load_ikea_dataframe,
    get_detected_photos
)

# Initialize display helper
display_helper = DisplayHelper()

# Ensure directories exist
ensure_directories()


# --- UTILITY FUNCTIONS ---

def cleanup_old_data():
    """Clean up old detection data."""
    try:
        if os.path.exists(str(DETECT_DIR.parent)):
            shutil.rmtree(str(DETECT_DIR.parent))
        ensure_directories()
    except Exception:
        pass


# --- STREAMLIT APP ---

st.set_page_config(layout="wide", page_title="IKEA Recommender")

st.title("IKEA Furniture Recommender 🛋️")
st.write('**_Upload a photo, select an item, OR search by text to get similar IKEA products with prices and links!_**')

# --- SIDEBAR & UPLOAD ---
st.sidebar.header("Search Options")

# Text query option - available always
st.sidebar.subheader("Text Search")
text_query = st.sidebar.text_input("Describe what you're looking for", 
                                    placeholder="e.g., 'modern sofa', 'scandinavian chair'",
                                    help="You can also use style names like 'modern', 'scandinavian', 'industrial', etc.")

# Image upload option
st.sidebar.markdown("---")
st.sidebar.subheader("Image Search (Optional)")
uploaded_file = st.sidebar.file_uploader("Or upload an image (JPG/JPEG/PNG)", type=["jpg", "jpeg", "png"])

# Initialize State
if 'yolo_model' not in st.session_state:
    with st.spinner('Loading YOLO model...'):
        try:
            st.session_state.yolo_model = load_yolo_model()
        except Exception as e:
            st.error(f"Failed to load YOLO model: {e}")
            st.stop()

if 'similarity_model' not in st.session_state:
    with st.spinner('Loading CLIP model...'):
        try:
            st.session_state.similarity_model = load_similarity_model()
        except Exception as e:
            st.error(f"Failed to load CLIP model: {e}")
            st.stop()

if 'ikeadf' not in st.session_state:
    with st.spinner('Loading IKEA database...'):
        try:
            st.session_state.ikeadf = load_ikea_dataframe()
            st.success(f"✅ Loaded {len(st.session_state.ikeadf)} products")
        except Exception as e:
            st.error(f"Failed to load IKEA database: {e}")
            st.info("💡 Tip: Run 'python embedding/embed-ds.py' first to create embeddings")
            st.stop()

if 'similarity_results' not in st.session_state:
    st.session_state.similarity_results = {}
if 'last_upload_name' not in st.session_state:
    st.session_state.last_upload_name = None

# Main Logic - Text-only search (no image)
if uploaded_file is None:
    if text_query and text_query.strip():
        st.header("Text-Based Search")
        if st.button('🔍 Search by Text', type="primary"):
            with st.spinner(f'Searching for "{text_query}"...'):
                try:
                    recommender = Recommender(
                        st.session_state.similarity_model,
                        st.session_state.ikeadf
                    )
                    results_df = recommender.recommend(
                        query_text=text_query.strip(),
                        top_k=10
                    )
                    
                    if results_df is not None and not results_df.empty:
                        display_helper.display_recommendations(results_df, "Top 10 Recommendations")
                    else:
                        st.info("No results found. Try a different search term.")
                except Exception as e:
                    st.error(f"Search failed: {e}")
        else:
            st.info("👆 Click the button above to search by text")
    else:
        st.info("👈 Enter a search term in the sidebar to find furniture, or upload an image to detect furniture items.")
        
# Image-based search (with optional text)
elif uploaded_file is not None:
    # Reset if new file
    if st.session_state.last_upload_name != uploaded_file.name:
        cleanup_old_data()
        st.session_state.similarity_results = {}
        st.session_state.detected_photos = None

    st.session_state.last_upload_name = uploaded_file.name

    # Save and display user image
    image = Image.open(uploaded_file)
    user_img_path = str(UPLOADS_DIR / uploaded_file.name)
    image.save(user_img_path)

    st.sidebar.image(image, caption="Your Photo", width='stretch')

    # 1. Detection
    if st.session_state.get('detected_photos') is None:
        with st.spinner('Detecting furniture...'):
            try:
                img_dict = get_detected_photos(
                    user_img_path,
                    st.session_state.yolo_model,
                    save_dir=str(DETECT_DIR)
                )
                st.session_state.detected_photos = img_dict
            except Exception as e:
                st.error(f"Detection failed: {e}")
                img_dict = []
                st.session_state.detected_photos = []
    else:
        img_dict = st.session_state.detected_photos

    if not img_dict:
        st.warning("No furniture detected. Try a clearer photo or use text search in the sidebar.")
        
        # Allow text-only search even when image is uploaded but nothing detected
        if text_query and text_query.strip():
            st.markdown("---")
            st.header("Text-Based Search")
            if st.button('🔍 Search by Text', type="primary"):
                with st.spinner(f'Searching for "{text_query}"...'):
                    try:
                        recommender = Recommender(
                            st.session_state.similarity_model,
                            st.session_state.ikeadf
                        )
                        results_df = recommender.recommend(
                            query_text=text_query.strip(),
                            top_k=10
                        )
                        
                        if results_df is not None and not results_df.empty:
                            display_helper.display_recommendations(results_df, "Top 10 Recommendations")
                        else:
                            st.info("No results found. Try a different search term.")
                    except Exception as e:
                        st.error(f"Search failed: {e}")
    else:
        # Display detected crops
        st.header("1. Detected Items")
        cols = st.columns(min(len(img_dict), 5))
        furniture_options = []

        for i, item in enumerate(img_dict):
            if i < 5:  # Limit display columns
                with cols[i]:
                    st.image(item['path'], caption=f"{i + 1}. {item['class']}")
            furniture_options.append(f"{i + 1} - {item['class']}")

        # 2. Selection
        st.markdown("---")
        st.header("2. Find Recommendations")

        selected_idx = st.selectbox("Select an item to match:", range(len(furniture_options)),
                                    format_func=lambda x: furniture_options[x])

        if st.button('Find Matches'):
            selected_photo = img_dict[selected_idx]

            with st.spinner(f'Searching IKEA for similar {selected_photo["class"]}s...'):
                try:
                    recommender = Recommender(
                        st.session_state.similarity_model,
                        st.session_state.ikeadf
                    )
                    results_df = recommender.recommend(
                        query_text=text_query.strip() if text_query and text_query.strip() else None,
                        query_image_path=selected_photo['path'],
                        top_k=10
                    )

                    if results_df is not None and not results_df.empty:
                        # Check if item_cat column exists before filtering
                        if 'item_cat' not in results_df.columns:
                            # If column doesn't exist, show all results without filtering
                            st.subheader("Top Recommendations")
                            display_helper.display_recommendations(results_df.head(10), "")
                        else:
                            # Filter Categories
                            target_cat = selected_photo['class']  # e.g. "Chair"

                            try:
                                # Handle NaN values - treat them as non-matching
                                # First check for non-NaN values, then check if category contains target
                                match_mask = results_df['item_cat'].notna() & results_df['item_cat'].str.contains(target_cat, case=False, na=False)

                                df_exact = results_df[match_mask].head(5)
                                df_other = results_df[~match_mask].head(5)

                                st.subheader(f"Best Matches in '{target_cat}'")
                                if not df_exact.empty:
                                    display_helper.display_recommendations(df_exact, "")
                                else:
                                    st.info("No exact category matches found.")

                                st.markdown("---")
                                st.subheader("Similar Items (Other Categories)")
                                if not df_other.empty:
                                    display_helper.display_recommendations(df_other, "")
                                else:
                                    st.info("No items found in other categories.")
                            except Exception as filter_error:
                                # Fallback: if filtering fails, show all results
                                st.warning(f"Category filtering failed: {filter_error}. Showing all results.")
                                display_helper.display_recommendations(results_df.head(10), "")
                    else:
                        st.info("No results found. Try adjusting your search.")
                except Exception as e:
                    st.error(f"Search failed: {e}")
                    import traceback
                    st.code(traceback.format_exc())
