import datetime
import random
import time
import numpy as np

from flask import Flask, render_template, request, redirect, url_for, session
from elasticsearch import Elasticsearch
from elasticsearch import NotFoundError
from credentials import get_es_password_and_credentials_path
password, ca_certs = get_es_password_and_credentials_path('./credentials/')

es_instance = Elasticsearch('https://localhost:9200', ca_certs=ca_certs, basic_auth=("elastic", password))
app = Flask(__name__, template_folder='./Website/template_folder')

USERNAME = "admin"
PASSWORD = "admin"
INDEX_NAME = "engine"

USERNAMES = ["admin", "user1", "user2"]
PASSWORDS = dict()
PASSWORDS["admin"] = "admin"
PASSWORDS["user1"] = "pass1"
PASSWORDS["user2"] = "pass2"

# Global variable to keep track of the latest query entered by the user
curr_query = ""

app.secret_key = 'supersecretkey'


def create_user_index(username):
    # create index with user's name
    index_name = f"{username}_index"
    body = {
        "mappings": {
            "properties": {
                "query": {"type": "keyword"},
                "doc_counts": {"type": "object", "enabled": False}
            }
        }
    }
    es_instance.indices.create(index=index_name, body=body)
    return index_name

def create_profile_index():
    mapping = {
        "mappings": {
            "properties": {
                "profile_ID": {"type": "keyword"},
                "favorite_sport": {"type": "text"},
                "favorite_subject": {"type": "text"},
                "hobby": {"type": "text"}
            }
        }
    }

    es_instance.indices.create(index="user_profiles", body=mapping)

def get_user_index_name(username):
    """
    Returns the Elasticsearch index for the specified user.
    """
    return f"{username}_index"

def get_boost(count):
    return np.log(count+1) * 10

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Check credentials and redirect to home page if successful
        if request.form['username'] in USERNAMES and request.form['password'] == PASSWORDS[request.form['username']]:
            session['username'] = request.form['username']
            # create_user_index(session['username'])
            if not es_instance.indices.exists(index="user_profiles"):
                create_profile_index()
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials')
    else:
        return render_template('login.html')

@app.route('/home', methods=['GET', 'POST'])
def home():

    
    if 'username' not in session:
        return redirect(url_for('login'))

    # Create index for user if it does not exist
    user_index_name = get_user_index_name(session['username'])
    if not es_instance.indices.exists(index=user_index_name):
        create_user_index(session['username'])

    # User has entered a search query
    if request.method == 'POST':
        # Get search query from user
        search_query = request.form['search']
        global curr_query
        curr_query = search_query
        

        # Define query for Elasticsearch
        query_from_user_in_search_engine = {
            "query": {
                "match": {
                    "content": search_query
                }
            }
        }

        # Execute query
        results_from_engine_index = es_instance.search(index=INDEX_NAME, query=query_from_user_in_search_engine['query'],size=1000) 
        #size parameter is the number of documents we want to retrieve, by default it's 10
        document_names = [hit['_source']['filename'] for hit in results_from_engine_index['hits']['hits']]


        query_from_user_in_past_queries = {
            "query": {
                "match": {
                    "query": search_query
                }
            }
        }

        results_from_user_past_queries = es_instance.search(index=user_index_name, query=query_from_user_in_past_queries["query"])
        
        print(results_from_user_past_queries['hits']['hits'])
        
        results_with_boost = results_from_engine_index['hits']['hits']
        if results_from_user_past_queries['hits']['total']['value'] > 0:
            hit = results_from_user_past_queries['hits']['hits'][0]['_source']

            doc_counts = results_from_user_past_queries['hits']['hits'][0]['_source']['doc_counts']

            # results_with_boost = results['hits']['hits']
            for result in results_with_boost:
                if result['_source']['filename'] in doc_counts:
                    # Boost score
                    doc_count = doc_counts[result['_source']['filename']]
                    result['_score'] += get_boost(doc_count)
            
            results_with_boost = sorted(results_with_boost, key=lambda x: x['_score'], reverse=True)
        return render_template('search_results.html', search_query=search_query, document_names=document_names, results=results_with_boost)

    if 'logout' in request.args:
        session.clear()
        return redirect(url_for('login'))

    if 'logout' in request.form:
        session.clear()
        return redirect(url_for('login'))

    return render_template('home.html', username=session['username'])

@app.route('/edit_profile')
def edit_profile():
    return render_template('edit_profile.html')

@app.route('/profile/<username>')
def profile(username):
    # Get user profile from Elasticsearch index
    res = es_instance.search(index="user_profiles", body={"query": {"match": {"profile_ID": username}}})
    #print(res)
    if res['hits']['total']['value'] > 0:
        profile = res['hits']['hits'][0]['_source']
        print("Profile found for ", session['username'])
    else:
        print("DID NOT FIND PROFILE")
        profile = {'favorite_sport': '', 'favorite_subject': '', 'hobby': ''}
    
    # Render the HTML template with user profile data
    return render_template('profile.html', username=session['username'], 
                           favorite_sport=profile['favorite_sport'], 
                           favorite_subject=profile['favorite_subject'], 
                           hobby=profile['hobby'])

@app.route('/save_profile', methods=['POST'])
def save_profile():
    # Get the new profile data from the form
    favorite_sport = request.form['favorite_sport']
    favorite_subject = request.form['favorite_subject']
    hobby = request.form['hobby']

    res = es_instance.search(index="user_profiles", body={"query": {"match": {"profile_ID": session['username']}}})

    new_profile = {
            "profile_ID": session['username'],
            "favorite_sport": favorite_sport,
            "favorite_subject": favorite_subject,
            "hobby": hobby
        }

    if res['hits']['total']['value'] == 0:
        print("INSERTING NEW PROFILE")
        new_profile = {
            "profile_ID": session['username'],
            "favorite_sport": favorite_sport,
            "favorite_subject": favorite_subject,
            "hobby": hobby
        }
        es_instance.index(index="user_profiles", body=new_profile)

    else:
        body = {
            "favorite_sport": favorite_sport,
            "favorite_subject": favorite_subject,
            "hobby": hobby
        }
        es_instance.update(index='user_profiles', id=res["hits"]["hits"][0]["_id"], body={"doc": body})
    res = es_instance.search(index="user_profiles", body={"query": {"match": {"profile_ID": session['username']}}})
    print(res)
    # Redirect to the user's profile page
    return redirect(url_for('profile', username=session['username']))
    
@app.route('/document/<filename>')
def document(filename):
    # Define query for Elasticsearch
    query_by_title = {
        "query": {
            "match": {
                "filename": filename
            }
        }
    }

    # Execute query
    results = es_instance.search(index=INDEX_NAME, query=query_by_title['query'], min_score=0, size=1000)

    # Extract content from results
    content = results["hits"]["hits"][0]['_source']['content']
    
    return render_template('document.html', filename=filename, content=content)

@app.route("/update_user_data", methods=["POST"])
def update_user_data():
    
    username = session['username']
    index_name = get_user_index_name(username)

    filename = request.form.get("filename")
    duration = int(request.form.get("duration"))

    # check if duration is greater than 5 seconds
    if duration > 5000:
        query = curr_query
        
        try:
            # check if the query exists in the index
            body = {
                "query": {
                    "match": {
                        "query": query
                    }
                }
            }

            res = es_instance.search(index=index_name, body=body)
            if res["hits"]["total"]["value"] > 0:
                doc_counts = res["hits"]["hits"][0]["_source"]["doc_counts"]

                # check if the filename exists in the hashmap
                if filename in doc_counts:
                    # increment the value                    
                    doc_counts[filename] += 1
                else:
                    # create new entry with filename as key and 1 as value
                    doc_counts[filename] = 1
                # update the index
                es_instance.update(index=index_name, id=res["hits"]["hits"][0]["_id"], body={"doc": {"doc_counts": doc_counts}})
            else:
                
            
                es_instance.index(
                    index=index_name, 
                    body={
                        "query": curr_query,
                        "doc_counts": {
                            filename: 1
                        }
                    }
                )
                


        except NotFoundError:
            es_instance.index(
                    index=index_name, 
                    body={
                        "query": curr_query,
                        "doc_counts": {}
                    }
                )
            print("New query-entry created")
    
    return "OK"



if __name__ == '__main__':
    app.run(debug=True)