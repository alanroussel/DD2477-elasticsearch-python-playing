from elasticsearch import Elasticsearch
import os
import json
from tqdm import tqdm
credentials_path = '../credentials/'
with open(credentials_path + 'config.json', 'r') as f:
    config = json.load(f)
# Connect to ElasticSearch

ELASTIC_PASSWORD = config["password"]
es_instance = Elasticsearch('https://localhost:9200', ca_certs=credentials_path + "http_ca.crt", basic_auth=("elastic", ELASTIC_PASSWORD))
# Define the index and mapping
INDEX_NAME = 'engine'
mappings = {
    "mappings": {
        "properties": {
            "filename": {"type": "text"},
            "content": {"type": "text"}
        }
    }
}


# Define the directory containing the files to be indexed
dir_path = '../../lab1/davisWiki'
files_to_read = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)) and f.endswith('.f')]

# Loop through the files in the directory and index each file
for filename in tqdm(files_to_read):
    file_path = os.path.join(dir_path, filename)
    if os.path.isfile(file_path):
        # Read the content of the file
        with open(file_path, 'r') as f:
            content = f.read()

        # Define the document to be indexed
        doc = {
            "filename": filename,
            "content": content
        }

        # Index the document in ElasticSearch
        es_instance.index(index=INDEX_NAME, document=doc)
        
print("Files indexed successfully!")
