# Personalized Search Engine Project

This project has been created during the group project for the course Search Engines and Information Retrieval Systems (DD2477) at KTH University.

The goal is to implement a personalized search engine. A simple flask web interface has been developed in order to allow users to create a profile, search for documents as well as viewing these documents. As the user interacts with the website, actions are logged and the information is then used to influence the ranking of the search results.

## Local Elasticsearch Launching

This application uses Elasticsearch as a search engine and a database. Therefore, you will need to launch a local instance of Elasticsearch. In order to do so, follow the steps of the official [Elasticsearch GitHub repository](https://github.com/elastic/elasticsearch#run-elasticsearch-locally). We use the 8.7.0 docker image version.

During launching, copy your personal Elasticsearch password as it will be needed during the following steps. Once the container is up, go to the 'elasticsearch'-container in Docker Desktop, go to files and then `/usr/share/elasticsearch/config/certs`, and copy the file `http_ca.crt`.

## Run the Project Locally

Clone the project

```bash
git clone https://github.com/alanroussel/DD2477-elasticsearch-python-playing
```

Go to the project directory

```bash
cd DD2477-elasticsearch-python-playing
```

Install needed dependencies and packages, for instance with conda.

```bash
conda env create -f environment.yml
conda activate elasticsearch_env
```

Unzip `davisWiki.tar`.

Before indexing davisWiki dataset into Elasticsearch, we need to ensure a secure connection between this application and your elasticsearch instance. Therefore, enter `credentials` folder, paste your password inside already existing `config.json` and drop `http_ca.crt` file.You should be able to index the dataset. It should take between 30 seconds and 2 minutes.

```bash
python index.py
```

Start the server

```bash
python server.py
```

Go to [http://localhost:5000](http://localhost:5000) 🎉!
