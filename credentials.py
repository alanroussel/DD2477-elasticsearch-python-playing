'''
file to load elastic search password and credentials 
'''

import json
credentials_path = "./credentials/"
def get_es_password_and_credentials_path():
    #load password
    with open(credentials_path + 'config.json', 'r') as f:
        config = json.load(f)
        ELASTIC_PASSWORD = config["password"]

    ca_certs_path = credentials_path + "http_ca.crt"
    
    return ELASTIC_PASSWORD, ca_certs_path
