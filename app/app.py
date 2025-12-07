from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import numpy as np
import shutil

# --- CONFIGURATION ---
APP_DIR = 'appdata/'
SAVE_IMG_DIR = os.path.join(APP_DIR, 'detect')
USER_UPLOAD_DIR = os.path.join(APP_DIR, 'uploads')

# Import components from models.py
try:
    from models import (
        load_yolo_model,
        load_similarity_model,
        load_ikea_dataframe,
        get_detected_photos,
        get_image_vector,
        calculate_similarities_vectorized
    )
except ImportError as e:
    st.error(f"Failed to import from models.py: {e}")
    st.stop()


# --- UTILITY FUNCTIONS ---

def compare_similarity(image_vector, ikeadf):
    """Compare image similarity and return top matches."""
    valid_vectors = ikeadf['vector'].apply(lambda x: isinstance(x, np.ndarray))
    filtered_df = ikeadf[valid_vectors].copy()

    if filtered_df.empty:
        return filtered_df

    product_vectors = np.array([v.flatten() for v in filtered_df['vector'].values])
    similarities = calculate_similarities_vectorized(image_vector, product_vectors)
    filtered_df['similarity'] = similarities

    return filtered_df.sort_values(by=['similarity'], ascending=False).head(500)


def cleanup_old_data():
    try:
        if os.path.exists(APP_DIR):
            shutil.rmtree(APP_DIR)
        os.makedirs(SAVE_IMG_DIR, exist_ok=True)
        os.makedirs(USER_UPLOAD_DIR, exist_ok=True)
    except Exception:
        pass


# --- STREAMLIT APP ---

st.set_page_config(layout="wide", page_title="IKEA Recommender")

st.title("IKEA Furniture Recommender 🛋️")
st.write('**_Upload a photo, select an item, and get similar IKEA products with prices and links!_**')

# --- SIDEBAR & UPLOAD ---
st.sidebar.header("Upload Image")
uploaded_file = st.sidebar.file_uploader("Choose an image (JPG/JPEG)", type=["jpg", "jpeg", "png"])

# Initialize State
if 'yolo_model' not in st.session_state:
    st.session_state.yolo_model = load_yolo_model()
if 'similarity_model' not in st.session_state:
    st.session_state.similarity_model = load_similarity_model()
if 'ikeadf' not in st.session_state:
    st.session_state.ikeadf = load_ikea_dataframe()

if 'similarity_results' not in st.session_state: st.session_state.similarity_results = {}
if 'last_upload_name' not in st.session_state: st.session_state.last_upload_name = None

# Main Logic
if uploaded_file is not None:
    # Reset if new file
    if st.session_state.last_upload_name != uploaded_file.name:
        cleanup_old_data()
        st.session_state.similarity_results = {}
        st.session_state.detected_photos = None

    st.session_state.last_upload_name = uploaded_file.name

    # Save and display user image
    image = Image.open(uploaded_file)
    os.makedirs(USER_UPLOAD_DIR, exist_ok=True)
    user_img_path = os.path.join(USER_UPLOAD_DIR, uploaded_file.name)
    image.save(user_img_path)

    st.sidebar.image(image, caption="Your Photo", use_container_width=True)

    # 1. Detection
    if st.session_state.get('detected_photos') is None:
        with st.spinner('Detecting furniture...'):
            img_dict = get_detected_photos(user_img_path, st.session_state.yolo_model, save_dir=SAVE_IMG_DIR)
            st.session_state.detected_photos = img_dict
    else:
        img_dict = st.session_state.detected_photos

    if not img_dict:
        st.warning("No furniture detected. Try a clearer photo.")
    else:
        # Display detected crops
        st.header("1. Detected Items")
        cols = st.columns(len(img_dict))
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
                # Get embedding
                query_vec = get_image_vector(selected_photo['path'], st.session_state.similarity_model)
                results_df = compare_similarity(query_vec, st.session_state.ikeadf)

            if results_df is not None and not results_df.empty:
                # Filter Categories
                target_cat = selected_photo['class']  # e.g. "Chair"

                # Filter: Check if target category is inside the item_cat string
                # (Scraper uses "Chair", App uses "Chair", CSV might have "Chair" or "Chairs")
                match_mask = results_df['item_cat'].str.contains(target_cat, case=False, na=False)

                df_exact = results_df[match_mask].head(5)
                df_other = results_df[~match_mask].head(5)


                # --- Helper to display cards ---
                def display_cards(dataframe):
                    cols = st.columns(len(dataframe))
                    for idx, (row_idx, row) in enumerate(dataframe.iterrows()):
                        with cols[idx]:
                            # Data from CSV
                            name = row.get('item_name', 'Product')
                            price = row.get('item_price', 'Price N/A')
                            web_img = row.get('image_url', None)
                            link = row.get('product_link', None)

                            # Display Web Image
                            if web_img:
                                try:
                                    st.image(web_img, use_container_width=True)
                                except:
                                    st.error("Img Error")

                            st.markdown(f"**{name}**")
                            st.markdown(f"💰 **{price}**")

                            if link:
                                st.markdown(f"👉 [View on IKEA]({link})")


                st.subheader(f"Best Matches in '{target_cat}'")
                if not df_exact.empty:
                    display_cards(df_exact)
                else:
                    st.info("No exact category matches found.")

                st.markdown("---")
                st.subheader("Similar Items (Other Categories)")
                if not df_other.empty:
                    display_cards(df_other)
