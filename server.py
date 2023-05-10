'''
This file is the server of our application. It permits to load information stored in elasticsearch, render html pages, keep track of user's actions, etc. 


'''

################################################
##### PACKAGES LOADING AND GLOBAL VARIABLES ####
################################################

# Import packages
import time
import numpy as np
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from elasticsearch import Elasticsearch
from elasticsearch import NotFoundError

# Load password and credentials in order to connect to elasticsearch API. 
from credentials import get_es_password_and_credentials_path
password, ca_certs = get_es_password_and_credentials_path()
es_instance = Elasticsearch('https://localhost:9200', ca_certs=ca_certs, basic_auth=("elastic", password))

# Initiate flask application. Flask is using a combinaison of python code and html pages
app = Flask(__name__, template_folder='./Website/template_folder')
app.secret_key = 'supersecretkey'

# Index names. Indexes are like database in elasticsearch
INDEX_ENGINE_NAME = "engine"
INDEX_PROFILES_NAME = "user_profiles"

# List of already created users. You can also register a new user
USERNAMES = ["admin", "user1", "user2"]
PASSWORDS = dict()
PASSWORDS["admin"] = "admin"
PASSWORDS["user1"] = "pass1"
PASSWORDS["user2"] = "pass2"

# Global variables to keep track of the latest query entered by the user
curr_query = ""
start_time_tracked = None
filename_tracked = None
length_of_doc = None

# Variables used to alter the ranking 
ALPHA = 2 # click boosting
BETA = 0.25 # profile boosting




################################################
#####  UTIL FUNCTIONS TO ELASTICSEARCH API  ####
################################################

## ENGINE INDEX
def search_documents_in_index(terms, size=1000):
    """ 
    search documents in engine index given string terms, such as 'zombie' or 'money transfer' 
    returns: object containing all matched documents
    """
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
    """ 
    create a personal index for this user
    returns: string describing the index name
    """
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
    """ 
    get the documents tracked as relevant to the user, from its previous searchs and clicks
    returns: object containing all matched documents
    """
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
    """ 
    create the index to store all the profiles 
    returns: void 
    """
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
    """ 
    get profile (favorite sport, favorite subject & hobby) from this user 
    returns: object of INDEX_PROFILES_NAME's mapping """
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
    """ 
    get the documents tracked as relevant to the user, according to its profile information
    returns: hashmap filename->score containing the top 100 results retrieved
    """

    # build search query from the informations of its profile
    terms_to_search = profile['favorite_sport'] + " " + profile['favorite_subject'] + " " + profile['hobby']
    res = search_documents_in_index(terms_to_search, size=100)

    # build a hashmap filename->score in order to alter the search engine score
    profile_results_map = dict() 
    for hit in res['hits']['hits']:
        filename = hit['_source']['filename']
        score = hit['_score']
        profile_results_map[filename] = score

    return profile_results_map

## BOOST FUNCTION

def get_boost(count):
    """ computes a boost according to the number of time user visited a page  """
    return np.log(count+1) * 10


################################################
#####     FLASK CONTROLLERS AND ROUTES      ####
################################################

@app.route('/', methods=['GET', 'POST'])
def login():
    # connected to a very local instance database : the file users.db
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')

    # add list of predefined users : admin, user1 and user2
    for username in USERNAMES:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, PASSWORDS[username]))
        conn.commit()
    conn.close()

    if request.method == 'POST':
        # if the request is from an allowed user, redirect to home page
        if request.form['username'] in USERNAMES and request.form['password'] == PASSWORDS[request.form['username']]:
            session['username'] = request.form['username']
            if not es_instance.indices.exists(index=INDEX_PROFILES_NAME):
                create_profile_index()
            return redirect(url_for('home'))
        else:
            # user not allowed, invalied credentials
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

    # POST method is when a query as been typed into the search engine
    if request.method == 'POST':
        search_query = request.form['search']
        global curr_query 
        curr_query = search_query
        
        # get documents given the query of the user
        results_from_engine_index = search_documents_in_index(search_query, size=1000) # get top 1000
        results = results_from_engine_index['hits']['hits']
        
        # get documents given the past queries of the user
        results_from_user_past_queries = get_documents_from_past_queries(username=session['username'], terms=search_query)
        
        # get documents given the profile of the user 
        
        try:
            profile = get_profile(session['username']) # can throw error if the profile is not indexed yet 
            results_from_profile_hashmap = get_documents_from_profile(profile['hits']['hits'][0]['_source']) # can throw error if the profile is currently empty
        except:
            results_from_profile_hashmap = False

        ## boost results with results from clicking, i.e. from the past queries and search of the user
        if results_from_user_past_queries['hits']['total']['value'] > 0:
            doc_counts = results_from_user_past_queries['hits']['hits'][0]['_source']['doc_counts']

            for result in results:
                if result['_source']['filename'] in doc_counts:
                    # Boost score
                    doc_count = doc_counts[result['_source']['filename']]
                    result['_score'] += ALPHA*get_boost(doc_count)
            
            results = sorted(results, key=lambda x: x['_score'], reverse=True)
        
        # boost results with results from profile, i.e. from the information user has wrote in its profile.
        # check that the profile is not empty
        if(results_from_profile_hashmap):
            for i, result in enumerate(results):
                
                if i >= 100: 
                    break

                filename = result['_source']['filename']
                if filename in results_from_profile_hashmap:
                    
                    result['_score'] += BETA*results_from_profile_hashmap[filename]
                    
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
    # Get the new information from the form
    favorite_sport = request.form['favorite_sport']
    favorite_subject = request.form['favorite_subject']
    hobby = request.form['hobby']

    # build the profile object to send to elasticsearch

    new_profile = {
            "profile_ID": session['username'],
            "favorite_sport": favorite_sport,
            "favorite_subject": favorite_subject,
            "hobby": hobby
        }

    # check if a profile already exist
    res = get_profile(session['username'])

    if res['hits']['total']['value'] == 0:
        # create a new profile
        print("INSERTING NEW PROFILE")
        new_profile = {
            "profile_ID": session['username'],
            "favorite_sport": favorite_sport,
            "favorite_subject": favorite_subject,
            "hobby": hobby
        }
        es_instance.index(index=INDEX_PROFILES_NAME, body=new_profile)

    else:
        # update the current profile
        body = {
            "favorite_sport": favorite_sport,
            "favorite_subject": favorite_subject,
            "hobby": hobby
        }
        es_instance.update(index='user_profiles', id=res["hits"]["hits"][0]["_id"], body={"doc": body})
    
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
    
    # Prepare tracking 
    global start_time_tracked, filename_tracked, length_of_doc
    start_time_tracked = time.time()
    filename_tracked = filename
    length_of_doc = len(content.split())

    # Render document html page
    return render_template('document.html', filename=filename, content=content)

@app.route("/update_user_data")
def update_user_data():
    # controller called after leaving a document.html
    username = session['username']
    index_name = get_user_index_name(username)

    # retrieve tracked metrics : time spent, filename, of length of the document
    global start_time_tracked, filename_tracked, length_of_doc
    if(start_time_tracked and filename_tracked and length_of_doc):
        duration = time.time() - start_time_tracked
        filename = filename_tracked

        stayed_enough_time = False
        if(duration > 3):
            stayed_enough_time = True
        
        # check if duration is enough
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