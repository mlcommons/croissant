import iso639
import glob
import json
import os
import streamlit as st

class JSONParser:
    def __init__(self, data):
        self.data = data

    def parse_json(self):
        name = self.data.get('name', '')
        description = self.data.get('description', '')
        url = self.data.get('url', '')
        keywords = self.data.get('keywords', '')
        language = self.parse_language()
        license = self.data.get('license', '')
        citation = self.data.get('citation', '')
        return name, description, url, keywords, language, license, citation
    
    def parse_records(self):
        records = self.data.get('recordSet')
        categories = {}
        if records:
            for record in records:
                category = record.get('name')
                description = record.get('description')
                fields = record.get('field')
                columns = {}
                for field in fields:
                    field_names = field.get('name')
                    data_types = field.get('dataType')
                    columns[field_names] = data_types
                categories[category] = {'description': description, 'columns': columns}
            return categories
        else:
            return {}
    
    def parse_language(self):
        language_code = self.data.get('@language')
        if language_code:
             language = iso639.languages.get(alpha2=language_code)
             return language.name
        else:
            return language_code

class DatasetRetriever:
    def __init__(self):
        pass
    def get_dataset_names(self):
        all_datasets = glob.glob("./datasets/*")
        dataset_names = []
        for path in all_datasets:
            if os.path.isdir(path):
                dataset_names.append(path.split("/")[-1])
        dataset_names = [dataset.capitalize() for dataset in dataset_names]
        return dataset_names
    
    def prettify_json(self, json_data: dict):
        parser = JSONParser(json_data)
        name, description, url, keywords, language, license, citation = parser.parse_json()
        columns = parser.parse_records()
        
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
        st.write(columns)
        st.subheader("Citation:")
        st.code(citation)