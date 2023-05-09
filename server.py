import time
import numpy as np
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session
from elasticsearch import Elasticsearch
from elasticsearch import NotFoundError
from credentials import get_es_password_and_credentials_path
password, ca_certs = get_es_password_and_credentials_path()

es_instance = Elasticsearch('https://localhost:9200', ca_certs=ca_certs, basic_auth=("elastic", password))
app = Flask(__name__, template_folder='./Website/template_folder')

USERNAME = "admin"
PASSWORD = "admin"
INDEX_ENGINE_NAME = "engine"
INDEX_PROFILES_NAME = "user_profiles"

USERNAMES = ["admin", "user1", "user2"]
PASSWORDS = dict()
PASSWORDS["admin"] = "admin"
PASSWORDS["user1"] = "pass1"
PASSWORDS["user2"] = "pass2"


# Global variable to keep track of the latest query entered by the user
curr_query = ""
start_time_tracked = None
filename_tracked = None
length_of_doc = None

app.secret_key = 'supersecretkey'

## ENGINE INDEX
def search_documents_in_index(terms, size=1000):
    """ search documents in engine index given string terms, such as 'zombie' or 'money transfer' """
    query = {
            "query": {
                "match": {
                    "content": terms
                }
            }
        }
    
    res = es_instance.search(index=INDEX_ENGINE_NAME, query=query['query'],size=size) 
    return res


## USER PERSONAL INDEX
def create_user_index(username):
    """ create a personal index for this user """
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

def get_user_index_name(username):
    """ Returns the Elasticsearch index for the specified user """
    return f"{username}_index"

def get_documents_from_past_queries(username, terms):
    """ retrieve something from the personal index for this user ?"""
    query = {
            "query": {
                "match": {
                    "query": terms
                }
            }
        }

    results_from_user_past_queries = es_instance.search(index=get_user_index_name(username), query=query["query"])
    return results_from_user_past_queries


## PROFILE 
def create_profile_index():
    """ create the index to index all the profiles 
    returns void """
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

    es_instance.indices.create(index=INDEX_PROFILES_NAME, body=mapping)


def get_profile(username):
    """ get profile (favorite sport, favorite subject & hobby) from this user 
    return: object of INDEX_PROFILES_NAME's mapping """
    profile_query = {
            "query": {
                "match": {
                    "profile_ID": username
                }
            }
        }
    
    res = es_instance.search(index=INDEX_PROFILES_NAME, query=profile_query['query'])
    return res


def get_documents_from_profile(profile):
    """ retrieves documents given user's profile
    return: hashmap filename->score containing the top 100 results retrieved """

    terms_to_search = profile['favorite_sport'] + " " + profile['favorite_subject'] + " " + profile['hobby']
    res = search_documents_in_index(terms_to_search, size=100) #only get top-100 results. why ?
    profile_results_map = dict() # build a hashmap filename->score in order to alter the search engine score

    for hit in res['hits']['hits']:
        filename = hit['_source']['filename']
        score = hit['_score']
        profile_results_map[filename] = score

    return profile_results_map

## BOOST FUNCTION

def get_boost(count):
    """ computes a boost according to the number of time user visited a page ? """
    return np.log(count+1) * 10 # maybe change 




@app.route('/', methods=['GET', 'POST'])
def login():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')

    for username in USERNAMES:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, PASSWORDS[username]))
        conn.commit()
    conn.close()

    if request.method == 'POST':
        # Check credentials and redirect to home page if successful
        if request.form['username'] in USERNAMES and request.form['password'] == PASSWORDS[request.form['username']]:
            session['username'] = request.form['username']
            # create_user_index(session['username'])
            # why is this line commented ? is it normal ?
            if not es_instance.indices.exists(index=INDEX_PROFILES_NAME):
                create_profile_index()
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials')
    else:
        return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Add new user to PASSWORDS dictionary
        if username in PASSWORDS:
            return render_template('register.html', error='Username already taken')
        else:
            USERNAMES.append(username)
            PASSWORDS[username] = password
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            # create_user_index(username)
            # Why is this line commented? Is it normal?
            return redirect(url_for('home'))
    else:
        return render_template('register.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Create index for user if it does not exist
    if not es_instance.indices.exists(index=get_user_index_name(session['username'])):
        create_user_index(session['username'])

    
    if request.method == 'POST':
        print("POST", request.form)
        search_query = request.form['search']
        global curr_query # i dont understand 
        curr_query = search_query
        
        # get documents given the query of the user
        results_from_engine_index = search_documents_in_index(search_query, size=1000) # get top 1000
        document_names = [hit['_source']['filename'] for hit in results_from_engine_index['hits']['hits']]
        results = results_from_engine_index['hits']['hits']
        
        # get documents given the past queries of the user
        results_from_user_past_queries = get_documents_from_past_queries(username=session['username'], terms=search_query)
        
        # get documents given the profile of the user 
        profile = get_profile(session['username'])
        try:
            results_from_profile_hashmap = get_documents_from_profile(profile['hits']['hits'][0]['_source'])
        except:
            results_from_profile_hashmap = False

        ## boost results with results from the past search of the user
        if results_from_user_past_queries['hits']['total']['value'] > 0:
            doc_counts = results_from_user_past_queries['hits']['hits'][0]['_source']['doc_counts']

            for result in results:
                if result['_source']['filename'] in doc_counts:
                    # Boost score
                    doc_count = doc_counts[result['_source']['filename']]
                    result['_score'] += get_boost(doc_count)
            
            results = sorted(results, key=lambda x: x['_score'], reverse=True)
        
        # If profile contains keywork, boost scores of documents that are relevant according to the user's interests (profile)
        if(results_from_profile_hashmap):
            for i, result in enumerate(results):
                
                if i >= 100: # Only check for the top-100, why ? 
                    break

                filename = result['_source']['filename']
                if filename in results_from_profile_hashmap:
                    
                    result['_score'] += results_from_profile_hashmap[filename]
                    
            results = sorted(results, key=lambda x: x['_score'], reverse=True)

        return render_template('search_results.html', search_query=search_query,results=results)

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
    res = get_profile(username)
    if res['hits']['total']['value'] > 0:
        profile = res['hits']['hits'][0]['_source']
        
    else:
        
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

    res = get_profile(session['username'])

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
        es_instance.index(index=INDEX_PROFILES_NAME, body=new_profile)

    else:
        body = {
            "favorite_sport": favorite_sport,
            "favorite_subject": favorite_subject,
            "hobby": hobby
        }
        es_instance.update(index='user_profiles', id=res["hits"]["hits"][0]["_id"], body={"doc": body})
    res = es_instance.search(index=INDEX_PROFILES_NAME, body={"query": {"match": {"profile_ID": session['username']}}})
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
    results = es_instance.search(index=INDEX_ENGINE_NAME, query=query_by_title['query'], min_score=0, size=1000)

    # Extract content from results
    content = results["hits"]["hits"][0]['_source']['content']
    print(f'content file length = {len(content.split())}')
    global start_time_tracked, filename_tracked, length_of_doc
    start_time_tracked = time.time()
    filename_tracked = filename
    length_of_doc = len(content.split())
    return render_template('document.html', filename=filename, content=content)

@app.route("/update_user_data")
def update_user_data():
    print("update user data")
    username = session['username']
    index_name = get_user_index_name(username)

    global start_time_tracked, filename_tracked, length_of_doc
    if(start_time_tracked and filename_tracked and length_of_doc):
        duration = time.time() - start_time_tracked
        filename = filename_tracked
        print(f'update user data - filename = {filename} duration = {duration}')

        stayed_enough_time = False
        if(length_of_doc<100 and duration > 3):
            stayed_enough_time = True
        if(length_of_doc>=100 and duration > 5):
            stayed_enough_time = True
        
        # check if duration is greater than 3 seconds
        if stayed_enough_time:
            
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
    print("tracking reset")
    start_time_tracked = None
    filename_tracked = None
    length_of_doc = None
    return redirect("/home")



if __name__ == '__main__':
    app.run(debug=True)