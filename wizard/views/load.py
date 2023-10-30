import streamlit as st
import mlcroissant as mlc

def render_load():
    file = st.file_uploader("Select a croissant file to load")
    if file is not None:
        try:
            dataset = mlc.Dataset(file)
        except:
            st.toast(body="failed to load file", icon="🔥")