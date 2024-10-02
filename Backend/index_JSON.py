import json
from elasticsearch import Elasticsearch

es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

def load_drug_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def index_documents(data):
    for i, item in enumerate(data):
        doc = f"{item['link']} {item.get('pribalovy_letak', '')} {item.get('spc', '')}"
        es.index(index='drug_docs', id=i, body={'text': doc, 'full_data': item})

data_path = "../data/cleaned_general_info_additional.json"
drug_data = load_drug_data(data_path)
index_documents(drug_data)

print("Индексирование завершено.")
