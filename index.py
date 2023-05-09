from elasticsearch import Elasticsearch
import os
from tqdm import tqdm

from credentials import get_es_password_and_credentials_path

password, ca_certs = get_es_password_and_credentials_path()

es_instance = Elasticsearch('https://localhost:9200', ca_certs=ca_certs, basic_auth=("elastic", password))
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
dir_path = './davisWiki'
files_to_read = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)) and f.endswith('.f')]

# Loop through the files in the directory and index each file
for filename in tqdm(files_to_read, "indexing the file into your elasticsearch instance"):
    file_path = os.path.join(dir_path, filename)
    if os.path.isfile(file_path):
        # Read the content of the file
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # Define the document to be indexed
        doc = {
            "filename": filename,
            "content": content
        }

        # Index the document in ElasticSearch
        es_instance.index(index=INDEX_NAME, document=doc)
        
print("Files indexed successfully!")
