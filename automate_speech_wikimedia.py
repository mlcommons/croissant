# To run the validation script, install all dependencies in the requirements.txt file

import json

# I am basing the automation off of the mnist metadata, since speech-wikimedia is also a huggingface dataset

f = open("datasets/huggingface-mnist/metadata.json",)

speech_wikimedia_format = json.load(f)

f.close()

# I changed the data based on the speech wikimedia information I was given

speech_wikimedia_format["name"] = "speech_wikimedia"

speech_wikimedia_format["description"] = "The People's Speech Dataset is among the world's largest English speech recognition corpus today that is licensed for academic and commercial usage under CC-BY-SA and CC-BY 4.0. It includes 30,000+ hours of transcribed speech in English languages with a diverse set of speakers. This open dataset is large enough to train speech-to-text systems and crucially is available with a permissive license."

speech_wikimedia_format["url"] = "https://huggingface.co/datasets/MLCommons/speech_wikimedia"

speech_wikimedia_format["distribution"][0]["contentUrl"] = "https://huggingface.co/datasets/MLCommons/speech_wikimedia/tree/refs%2Fconvert%2Fparquet"

# The record set is the main thing that needs to be changed.

speech_wikimedia_format["recordSet"].clear()

# The Huggingface website provides a curl command that can give you this information.
# To get the curl command, click on the API button and copy the curl command for the splits.

recordSetNames = ["training", "test", "validation"]

# This comes from the top curl command when you click on the API button
# You will find this in the "feeatures" section of the resulting json output.

fieldNames = ["audio"]

for recordSetName in recordSetNames:
    record_entry = {}

    record_entry["@type"] = "ml:RecordSet"

    record_entry["name"] = recordSetName

    record_entry["description"] = f"The {recordSetName} set of records in the database."

    record_entry["field"] = []

    for fieldName in fieldNames:
        field_entry = {}

        field_entry["@type"] = "ml:Field"

        field_entry["name"] = fieldName

        field_entry["description"] = "Column from Hugging Face parquet file."

        # For any feature in the "features" section, you can find the datatype by looking 
        # at feature["type"]["_type"]
        field_entry["dataType"] = "sc:Audio"

        field_entry["source"] = {
            "distribution": "parquet-files",
            "extract": {
              "csvColumn": fieldName
            }
        }

        record_entry["field"].append(field_entry)
    
    speech_wikimedia_format["recordSet"].append(record_entry)

# At the end, the dictionary I made should be able to act as the metadata

outfile = open("datasets/huggingface-speech-wikimedia/metadata.json", "w")

json.dump(speech_wikimedia_format, outfile, indent = 2)

outfile.close()



