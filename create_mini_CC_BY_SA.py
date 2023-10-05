import jsonlines
import requests
import os

dir_count = 0

with jsonlines.open('CC_BY_SA.jsonl') as f:

    for line in f.iter():
        if dir_count >= 20:
            break
        
        if line["metadata"]["mediatype"] == "audio":
            path = "mini_CC_BY_SA/CC_BY_SA/" + line["metadata"]["identifier"]
            os.mkdir(path)
            
            curl_prefix = "https://" +  line["server"] + line["dir"]
            
            for file in line["files"]:
                if file["format"] == "VBR MP3":
                    mp3_file = open(path + "/" + file["name"], "wb")
                    mp3_file.write(requests.get(curl_prefix + "/" + file["name"]).content)
                    mp3_file.close()
            
            dir_count += 1
        
