from elasticsearch import Elasticsearch
from langchain.embeddings import HuggingFaceEmbeddings
from elasticsearch.helpers import bulk
import json

# Настройка подключения к Elasticsearch с аутентификацией и HTTPS
es = Elasticsearch(
    [{'host': 'localhost', 'port': 9200, 'scheme': 'https'}],
    http_auth=('elastic', 'S7DoO3ma=G=9USBPbqq3'),  # замените на ваш пароль
    verify_certs=False  # Отключить проверку SSL-сертификата, если используется самоподписанный сертификат
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def create_index():
    # Определяем маппинг для индекса
    mapping = {
        "mappings": {
            "properties": {
                "text": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "vector": {
                    "type": "dense_vector",
                    "dims": 384  # Размерность векторного представления
                },
                "full_data": {
                    "type": "object",
                    "enabled": False  # Отключаем индексацию вложенных данных
                }
            }
        }
    }
    es.indices.create(index='drug_docs', body=mapping, ignore=400)

def load_drug_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def index_documents(data):
    actions = []
    total_docs = len(data)
    for i, item in enumerate(data, start=1):
        doc_text = f"{item['link']} {item.get('pribalovy_letak', '')} {item.get('spc', '')}"

        vector = embeddings.embed_query(doc_text)

        action = {
            "_index": "drug_docs",
            "_id": i,
            "_source": {
                'text': doc_text,
                'vector': vector,
                'full_data': item
            }
        }
        actions.append(action)

        # Отображение прогресса
        print(f"Индексируется документ {i}/{total_docs}", end='\r')

        # Опционально: индексируем пакетами по N документов
        if i % 100 == 0 or i == total_docs:
            bulk(es, actions)
            actions = []

    # Если остались неиндексированные документы
    if actions:
        bulk(es, actions)

    print("\nИндексирование завершено.")

if __name__ == "__main__":
    create_index()
    data_path = "/home/poiasnik/esDB/cleaned_general_info_additional.json"
    drug_data = load_drug_data(data_path)
    index_documents(drug_data)

