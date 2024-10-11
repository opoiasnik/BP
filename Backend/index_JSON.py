import json
from elasticsearch import Elasticsearch
from langchain_huggingface import HuggingFaceEmbeddings

# Инициализация Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

# Инициализация модели для создания векторов
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def load_drug_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def index_documents(data):
    for i, item in enumerate(data):
        doc_text = f"{item['link']} {item.get('pribalovy_letak', '')} {item.get('spc', '')}"

        # Генерация векторного представления
        vector = embeddings.embed_query(doc_text)

        # Добавление документа с полем вектора
        es.index(index='drug_docs', id=i, body={
            'text': doc_text,
            'vector': vector,
            'full_data': item
        })


# Путь к данным
data_path = "data/cleaned_general_info_additional.json"
drug_data = load_drug_data(data_path)
index_documents(drug_data)

print("Индексирование завершено.")
