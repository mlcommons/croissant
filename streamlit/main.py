import os
import glob
import json
import streamlit as st
from utils import JSONParser

st.title("Croissant POC Viewer")
st.sidebar.image("../croissant.png", use_column_width=True)
add_selectbox = st.sidebar.selectbox(
    "Do you have  a JSON file, do you want to create a new one using a text box, or do you want to check a created dataset?",
    ("File", "Text box", "Dataset from database")
)

data = {}

if add_selectbox == "File":
    uploaded_file = st.file_uploader("Upload your file here", type=["json"])
    if uploaded_file is not None:
        data = json.load(uploaded_file)
elif add_selectbox == "Text box":
    uploaded_file = st.text_input("Paste your JSON here")
    if uploaded_file is not None:
        data = json.loads(uploaded_file)
else:
    all_datasets = glob.glob("../datasets/*")
    dataset_names = []
    for path in all_datasets:
        if os.path.isdir(path):
            dataset_names.append(path.split("/")[-1])
    dataset_names = [dataset.capitalize() for dataset in dataset_names]
    dataset_name = st.selectbox("Select a dataset", dataset_names)   
    if dataset_name:
        all_jsons = glob.glob(f"../datasets/{dataset_name.lower()}/*.json")
        if len(all_jsons) > 1:
            json_name = st.selectbox("Select a JSON file", all_jsons)
        else:
            json_name = all_jsons[0]
        if json_name:
            with open(json_name) as json_file:
                data = json.load(json_file)


json_parser = JSONParser(data)
name, description, url, keywords, language, license, citation = json_parser.parse_json()

st.header(f"{name.capitalize()} Dataset Information")
st.subheader("Description:")
st.write(description)

st.subheader("URL:")
st.write(url)

st.subheader("Language:")
st.write(language)

st.subheader("License:")
st.write(license)

if keywords:
    st.subheader("Keywords:")
    st.write(keywords)

st.subheader("Data Types:")
columns = json_parser.parse_records()
st.write(columns)

st.subheader("Citation:")
st.code(citation)

