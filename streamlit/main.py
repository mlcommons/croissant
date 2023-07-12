import os
import glob
import json
import time
import pandas as pd
import streamlit as st
from utils import DatasetRetriever

st.title("POC Croissant Datasets")

def change_state(field:str):
    st.session_state[field] = not st.session_state[field]

def clear_text(cur_key:str):
    st.session_state[cur_key] = ''

if 'record_state' not in st.session_state:
    st.session_state.record_state = {
        'name': '',
        'description': '',
        'key': []
    }
def checkout_form():
    if 'metadata' not in st.session_state:
        st.session_state['metadata'] = False
    if 'distribution' not in st.session_state:
        st.session_state['distribution'] = False
    if 'recordsets' not in st.session_state:
        st.session_state['recordsets'] = False
    if 'mlsemantics' not in st.session_state:
        st.session_state['mlsemantics'] = False

    with st.sidebar:
        st.markdown('### New Croissant Dataset')
        st.markdown(""" A croissant comes in layers. So does your dataset. 
                    To create a new schema you can use the tool to your right. 
                    As you go through the creation process, the following checklist
                    will be updated. Only when all the steps are completed 
                    you will be able to store your dataset schema in the database. """)
        
        st.checkbox('Completed Metadata',key='met', value=st.session_state['metadata'])
        st.checkbox('Completed Distribution',key='dist', value=st.session_state['distribution'])
        st.checkbox('Completed Record Sets',key='rec', value=st.session_state['recordsets'])
        st.checkbox('Completed ML Semantics',key='mls', value=st.session_state['mlsemantics'])

    with st.expander('#### Fill the information for all the croissant layers',expanded=True): 
        options = ['Metadata','Distribution','Record Sets','ML Semantics']        
        radio_cols = st.columns([1.5,10])
        step = radio_cols[1].radio(label='',label_visibility='collapsed', options=options,horizontal=True,index=0)                
        if step == 'Metadata':
            dataset_name = st.text_input('**Name**', placeholder='e.g. Titanic')
            url = st.text_input('**URL**',placeholder='e.g. https://www.openml.org/d/40945')
            description  = st.text_area('**Description**', placeholder='e.g. The original Titanic dataset, describing the status of individual passengers..')
            license = st.text_input('**License**',placeholder='e.g. Public Domain')
            citation = st.text_input('**Citation**',placeholder='e.g. The principal source for data about Titanic passengers is the Encyclopedia')
            metadata = {'name':dataset_name,'url':url,'description':description,'license':license,'citation':citation}
            st.button('Save Metadata', type = 'primary', on_click = change_state, args = ['metadata'])
        if step == 'Distribution':
            df = pd.DataFrame({"Name": ['passengers.csv','genders.csv'],
                               "Description": ['Passenger info','Maps genders values'],
                               "Content URL": ['https://.','/data/...'],
                               "Size (B)": [10000,10000],
                               "Encoding Format": ['text/csv','text/csv']})
            edited_df = st.data_editor(df, num_rows = "dynamic", hide_index = True)
            st.button('Save Distribution', type = 'primary', on_click = change_state, args = ['distribution'])           
        if step == 'Record Sets':          
            record_name = st.text_input('**Name**', placeholder='e.g. genders', key = 'record_name')
            record_description  = st.text_area('**Description**', placeholder='e.g. Maps gender labels to semantic definitions', key = 'record_description')
            record_key = st.multiselect('**Select the key**', ['#key', '#label'], key = 'record_key')
            if record_key:
                st.markdown('---')
                st.markdown('**Complete the information for the record**')
                cur_record = pd.DataFrame({"Name": ['gender','age'],
                               "Description": ['Gender of passenger','Age at time of death'],
                               "DataType": ['"sc:Text"','"sc:Float"'],
                               "source": ["#{passengers.csv/gender}","#{passengers.csv/age}"],
                               "references": [None, None]})
                cur_record_df = st.data_editor(cur_record, num_rows = "dynamic", hide_index = True)
                record_buttons = st.columns(3)
                if record_buttons[0].button('Add Record', type = 'primary'):
                    st.markdown('---')
                    st.write("This is how your record looks")
                    st.json({"name":record_name,"description":record_description,"key":record_key,"record":cur_record.to_dict('records')})
                if record_buttons[1].button('Add another record', type = 'primary'):
                    st.experimental_rerun()
                record_buttons[2].button('Finalize Records', type = 'primary', on_click = change_state, args = ['recordsets'])

        if step == 'ML Semantics':
            st.text_input('**ML Semantic**',placeholder='Write here')
            exp_cols = st.columns(2)
            exp_cols[0].text_input('',placeholder='Lorem',label_visibility='collapsed')
            exp_cols[1].text_input('',placeholder='Ipsum',label_visibility='collapsed')
            footer_cols = st.columns([5,1])                 
            agreed = footer_cols[0].checkbox('I agree to terms and conditions')
            footer_cols[1].button('Submit',type='primary',key='submit_btn',disabled=not agreed, on_click = change_state, args = ['mlsemantics'])

dataset_retriever = DatasetRetriever()
#validator = Validator()
def display_dataset():
    dataset_names = dataset_retriever.get_dataset_names()
    dataset_name = st.selectbox("Select a dataset", dataset_names) 
    if dataset_name:
        all_jsons = glob.glob(f"./datasets/{dataset_name.lower()}/*.json")
        if len(all_jsons) > 1:
            json_name = st.selectbox("Select a JSON file", all_jsons)
        else:
            json_name = all_jsons[0]
        if json_name:
            with open(json_name) as json_file:
                data = json.load(json_file)    
    dataset_retriever.prettify_json(data)

def display_uploaded_file():
    uploaded_file = st.file_uploader("Upload your file here", type=["json"])
    if uploaded_file is not None:
        data = json.load(uploaded_file)
        print("Here data is")
        #validator.validate(data)
        dataset_retriever.prettify_json(data)

form_example = st.selectbox('**What do you want to do**?',options=['Create new dataset','Display existing dataset from dataset db', 'Upload json file'])
if form_example == 'Create new dataset':
    checkout_form()
elif form_example == 'Display existing dataset from dataset db':
    display_dataset()
else:
    display_uploaded_file()