# app.py - Streamlit Application

import streamlit as st
from PIL import Image
import os
import glob
import re
import numpy as np
import shutil  # For safely cleaning up directories

# Import all necessary components from models.py
# Make sure models.py is in the same directory or accessible via Python path
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
    st.error(f"Failed to import from models.py. Ensure the file is present. Error: {e}")
    st.stop()

# --- 1. CONFIGURATION ---
APP_DIR = 'appdata/'
SAVE_IMG_DIR = os.path.join(APP_DIR, 'detect')
USER_UPLOAD_DIR = os.path.join(APP_DIR, 'uploads')


# --- 2. UTILITY FUNCTIONS ---

def compare_similarity(image_vector, ikeadf):
    """
    Compare image similarity with IKEA products using vectorized operations.
    """
    # Filter out rows where 'vector' might be NaN or incorrect type (if applicable)
    valid_vectors = ikeadf['vector'].apply(lambda x: isinstance(x, np.ndarray))
    filtered_df = ikeadf[valid_vectors].copy()

    # Extract product vectors, ensuring they are flattened arrays
    product_vectors = np.array([v.flatten() for v in filtered_df['vector'].values])

    # Calculate similarities using vectorized operations
    similarities = calculate_similarities_vectorized(image_vector, product_vectors)

    # Add similarity scores to the filtered dataframe
    filtered_df['similarity'] = similarities

    # Sort and return top 1000
    return filtered_df.sort_values(by=['similarity'], ascending=False).head(1000)


def cleanup_old_data():
    """Safely removes the application data directories."""
    try:
        if os.path.exists(APP_DIR):
            # shutil.rmtree is safer and cleans up the entire directory structure
            shutil.rmtree(APP_DIR)
        os.makedirs(SAVE_IMG_DIR, exist_ok=True)  # Recreate necessary directories
        os.makedirs(USER_UPLOAD_DIR, exist_ok=True)
    except Exception as e:
        st.warning(f"Could not clean up old data directories: {e}")


def get_furniture_list(img_dict):
    """Formats the detected furniture list for display."""
    return [f"{i + 1} - {item['class']} (Conf: {item['confidence']:.2f})" for i, item in enumerate(img_dict)]


# --- 3. STREAMLIT APP LAYOUT & LOGIC ---

st.set_page_config(layout="wide")
st.title("IKEA Furniture Recommender 🛋️")
st.write('**_Furnish your home with a click, just from your couch._**')
st.sidebar.header("Choose a furniture image for recommendation.")

# Initialize session state for models and data
if 'yolo_model' not in st.session_state:
    st.session_state.yolo_model = load_yolo_model()
if 'similarity_model' not in st.session_state:
    st.session_state.similarity_model = load_similarity_model()
if 'ikeadf' not in st.session_state:
    st.session_state.ikeadf = load_ikea_dataframe()

# Initialize session state for dynamic data
if 'similarity_results' not in st.session_state:
    st.session_state.similarity_results = {}
if 'detected_photos' not in st.session_state:
    st.session_state.detected_photos = None
if 'user_img_path' not in st.session_state:
    st.session_state.user_img_path = None
if 'last_upload_name' not in st.session_state:
    st.session_state.last_upload_name = None

# Get models and data from session state
yolo_model = st.session_state.yolo_model
similarity_model = st.session_state.similarity_model
ikeadf = st.session_state.ikeadf

# Clean up old data at the start of the app's main loop (or based on a button press)
# It's better to clear when a new file is uploaded rather than every app run
# cleanup_old_data()

uploaded_file = st.file_uploader("Choose an image with .jpg format", type=["jpg", "jpeg"])

if uploaded_file is not None:
    # Check if a new file was uploaded
    if st.session_state.last_upload_name != uploaded_file.name:
        cleanup_old_data()  # Clean up old data only when a new image is uploaded
        st.session_state.similarity_results = {}  # Clear cached results

    st.session_state.last_upload_name = uploaded_file.name

    # Save user image
    image = Image.open(uploaded_file)
    user_img_path = os.path.join(USER_UPLOAD_DIR, uploaded_file.name)
    image.save(user_img_path)
    st.session_state.user_img_path = user_img_path

    st.sidebar.image(image, width=250)
    st.sidebar.success('Upload Successful! Processing...')

    # --- DETECTION STAGE ---
    with st.spinner('Working hard on finding furniture...'):
        try:
            # Use the fixed get_detected_photos with unique naming
            img_dict = get_detected_photos(st.session_state.user_img_path, yolo_model, save_dir=SAVE_IMG_DIR)
            st.session_state.detected_photos = img_dict
        except Exception as e:
            st.error(f"Error during object detection: {e}")
            img_dict = []

    if not img_dict:
        st.warning("No furniture detected in the image. Please try another image or adjust the confidence threshold.")
    else:
        furniture_list = get_furniture_list(img_dict)

        st.header("Detected Furniture")

        # Display detected furniture in the main area for better visibility
        cols = st.columns(len(furniture_list))

        for i, item in enumerate(img_dict):
            if i < len(cols):
                cols[i].caption(f"**{i + 1}. {item['class']}** (Conf: {item['confidence']:.2f})")
                cols[i].image(Image.open(item['path']), use_container_width=True)

        # --- SELECTION STAGE ---
        st.markdown("---")

        options = list(range(len(furniture_list)))
        option_index = st.selectbox(
            'Which piece of furniture do you want recommendations for?',
            options,
            format_func=lambda x: furniture_list[x]
        )

        if st.button('Find Similar IKEA Products'):
            selected_photo = img_dict[option_index]
            pred_path = selected_photo['path']

            # Cache key uses the path (which includes the unique crop name and class)
            cache_key = f"{pred_path}"

            # --- SIMILARITY STAGE ---
            if cache_key not in st.session_state.similarity_results:
                with st.spinner(f'Finding similar products for {selected_photo["class"]}...'):
                    try:
                        # Get embedding vector (cached)
                        image_vector = get_image_vector(image_path=pred_path, _similarity_model=similarity_model)

                        # Compare similarity with IKEA products (vectorized)
                        df = compare_similarity(image_vector, ikeadf)

                        # Cache results
                        st.session_state.similarity_results[cache_key] = df
                    except Exception as e:
                        st.error(f"Error during similarity comparison: {e}")
                        df = None
            else:
                df = st.session_state.similarity_results[cache_key]

            if df is not None:
                # --- RECOMMENDATION DISPLAY STAGE ---

                # Determine target class for filtering (e.g., 'Bed' -> 'beds')
                obj_class = selected_photo['class'].lower() + 's'

                # Filter and display recommendations
                df_same_class = df[df['item_cat'] == obj_class].head(5)
                df_other_class = df[df['item_cat'] != obj_class].head(5)

                st.markdown("## Top Recommendations (Same Category)")
                st.markdown(f"The most similar **{selected_photo['class']}s** from IKEA.")

                # Display same class recommendations
                if not df_same_class.empty:
                    cols_rec = st.columns(5)
                    for i, (idx, row) in enumerate(df_same_class.iterrows()):
                        if i >= 5: break

                        col = cols_rec[i]
                        # Safely extract title, price, and link
                        col_title = re.match(r"^([^,]*)", str(row['item_name'])).group()
                        col_cat = str(row['item_cat'])
                        col_pic = str(idx)
                        col_price = f'${row["item_price"]}'
                        col_link = str(row['prod_url'])

                        # Construct image URL based on project structure
                        col_url = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                               'data', 'ikea-data', col_cat, col_pic + '.jpg')

                        with col:
                            try:
                                # Display image and details
                                st.image(Image.open(col_url), use_container_width=True)
                                st.markdown(f"#### **{col_price}**")
                                st.markdown(f"###### {col_title}")
                                st.markdown(f"###### [View product info]({col_link})")
                            except Exception as e:
                                st.error(f"Image not found or error: {col_url}")

                st.markdown("---")
                st.markdown("## Alternative Recommendations")
                st.markdown("Other highly similar items across different categories.")

                # Display other class recommendations
                if not df_other_class.empty:
                    cols_alt = st.columns(5)
                    for i, (idx, row) in enumerate(df_other_class.iterrows()):
                        if i >= 5: break

                        col = cols_alt[i]
                        # Safely extract title, price, and link
                        col_title = re.match(r"^([^,]*)", str(row['item_name'])).group()
                        col_cat = str(row['item_cat'])
                        col_pic = str(idx)
                        col_price = f'${row["item_price"]}'
                        col_link = str(row['prod_url'])

                        # Construct image URL
                        col_url = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                               'data', 'ikea-data', col_cat, col_pic + '.jpg')

                        with col:
                            try:
                                # Display image and details
                                st.image(Image.open(col_url), use_container_width=True)
                                st.markdown(f"#### **{col_price}**")
                                st.markdown(f"###### {col_title}")
                                st.markdown(f"###### [View product info]({col_link})")
                            except Exception as e:
                                st.error(f"Image not found or error: {col_url}")
            else:
                st.error("Could not complete similarity search due to a previous error.")