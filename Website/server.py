from flask import Flask, render_template, request, redirect, url_for, session
from elasticsearch import Elasticsearch

ELASTIC_PASSWORD = "DLrSyMSNlFb5kxl0Qg_f"
es_instance = Elasticsearch('http://localhost:9200')

app = Flask(__name__, template_folder='./template_folder')


INDEX_NAME = "engine"

app.secret_key = 'supersecretkey'

@app.route('/', methods=['GET', 'POST'])
def login():
    return redirect(url_for('home'))

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Get search query from user
        search_query = request.form['search']
        
        # Define query for Elasticsearch
        query = {
            "query": {
                "match": {
                    "content": search_query
                }
            }
        }
        
        # Execute query
        results = es_instance.search(index=INDEX_NAME, query=query['query'], size=1000, explain=True)
        ## (alan) size if how much document we want to retrieve for that `get`. default is 10

        # Extract document names from results
        hits = [hit for hit in results['hits']['hits']]
        
        return render_template('search_results.html', search_query=search_query, hits=hits)
    
    return render_template('home.html')

@app.route('/document')
def document():
    filename = request.args.get('filename')
    content = request.args.get('content')
    
    return render_template('document.html', filename=filename, content=content)

if __name__ == '__main__':
    app.run(debug=True)