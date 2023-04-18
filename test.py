from datetime import datetime
from elasticsearch import Elasticsearch
es = Elasticsearch('http://localhost:9200')

doc = {
    'author': 'author_name',
    'text': 'Interensting content...',
    'timestamp': datetime.now(),
}
resp = es.index(index="test-index", id=2, document=doc)
print(resp['result'])

resp = es.get(index="test-index", id=1)
print(resp['_source'])