'''
file to load elastic search password and credentials 

to do : create a folder and put inside
a config.json file with 
{
  "password": {yourelasticpassword}
}
the http_ca.crt

do not push that folder into github
'''

import json

def get_es_password_and_credentials_path(credentials_path):
    #load password
    with open(credentials_path + 'config.json', 'r') as f:
        config = json.load(f)
        ELASTIC_PASSWORD = config["password"]

    ca_certs_path = credentials_path + "http_ca.crt"
    
    return ELASTIC_PASSWORD, ca_certs_path
