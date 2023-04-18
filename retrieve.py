from elasticsearch import Elasticsearch

# Connect to Elasticsearch instance
es_instance = Elasticsearch('http://localhost:9200')
term = "zombie"
# Define query
query = {
	"query": {
		"match": {
			"content": term
		}
	}
}

# Execute query
results = es_instance.search(index='engine', query=query['query'], min_score=0, size=1000)

# Extract document names from results
document_names = [hit['_source']['filename'] for hit in results['hits']['hits']]

#Print content
for doc in results['hits']['hits']:
	print(doc['_source']['filename'])
# Print document names
print(f'for "{term}", retrieve {len(document_names)} documents :  {document_names}')

query_by_title = {
	"query": {
		"match": {
			"filename": "EmilyMaas.f"
		}
	}
}



