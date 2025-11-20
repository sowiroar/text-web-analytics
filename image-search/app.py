import streamlit as st

page = st.navigation(
    [st.Page(title="Upload Images", page="upload_images.py", icon="📤"),
    st.Page(title="Image Search", page="image_search.py", icon="🔍"),
    st.Page(title="Reverse Search", page="reverse_search.py", icon="🔍")]
)

page.run()