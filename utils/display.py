"""Display utilities for Streamlit app."""

import streamlit as st
from typing import Optional
import pandas as pd


class DisplayHelper:
    """Helper class for displaying recommendations in Streamlit."""
    
    @staticmethod
    def display_recommendations(dataframe: pd.DataFrame, title: str = ""):
        """
        Display recommendation cards in Streamlit.
        
        Args:
            dataframe: DataFrame with product recommendations
            title: Optional title for the section
        """
        if dataframe.empty:
            return
        
        if title:
            st.subheader(title)
        
        cols = st.columns(min(len(dataframe), 5))
        for idx, (row_idx, row) in enumerate(dataframe.iterrows()):
            if idx >= 5:  # Limit to 5 columns
                break
            
            with cols[idx]:
                # Extract data from CSV
                name = row.get('item_name', 'Product')
                price = row.get('item_price', 'Price N/A')
                web_img = row.get('image_url', None)
                link = row.get('product_link', None)
                similarity = row.get('similarity', None)
                
                # Display Web Image
                if web_img:
                    try:
                        st.image(web_img, width='stretch')
                    except Exception:
                        st.error("Image Error")
                
                st.markdown(f"**{name}**")
                st.markdown(f"💰 **{price}**")
                
                if similarity is not None:
                    st.caption(f"Similarity: {similarity:.2%}")
                
                if link:
                    # Ensure link is complete URL
                    if not link.startswith('http'):
                        link = 'https://www.ikea.com' + link
                    st.markdown(f"👉 [View on IKEA]({link})")
    
    @staticmethod
    def display_detected_items(detected_photos: list, max_items: int = 5):
        """
        Display detected furniture items in Streamlit.
        
        Args:
            detected_photos: List of detected items with metadata
            max_items: Maximum number of items to display
            
        Returns:
            List of furniture option strings for selectbox
        """
        if not detected_photos:
            return []
        
        cols = st.columns(min(len(detected_photos), max_items))
        furniture_options = []
        
        for i, item in enumerate(detected_photos):
            if i < max_items:
                with cols[i]:
                    st.image(
                        item['path'],
                        caption=f"{i + 1}. {item['class']}"
                    )
            furniture_options.append(f"{i + 1} - {item['class']}")
        
        return furniture_options
