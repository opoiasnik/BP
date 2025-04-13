import json
import sys
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from langchain_huggingface import HuggingFaceEmbeddings

# Подключение к Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

# Инициализация векторизатора (убедитесь, что модель доступна)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def create_index():
    # Определение маппинга для индекса
    mapping = {
        "mappings": {
            "properties": {
                "text": {"type": "text", "analyzer": "standard"},
                "vector": {"type": "dense_vector", "dims": 384},
                "full_data": {"type": "object", "enabled": False}
            }
        }
    }
    # Создание индекса, если он ещё не существует
    try:
        es.indices.create(index="drug_docs", body=mapping)
    except Exception as e:
        print("Ошибка при создании индекса:", e)


def load_drug_data(json_path):
    # Загрузка данных из JSON-файла
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def index_documents(data):
    actions = []
    total_docs = len(data)
    for i, item in enumerate(data, start=1):
        # Формирование текста документа из полей
        doc_text = f"{item['link']} {item.get('pribalovy_letak', '')} {item.get('spc', '')}"

        # Получение векторного представления текста
        vector = embeddings.embed_query(doc_text)

        # Подготовка действия для пакетной загрузки в Elasticsearch
        action = {
            "_index": "drug_docs",
            "_id": i,
            "_source": {
                "text": doc_text,
                "vector": vector,
                "full_data": item
            }
        }
        actions.append(action)

        # Обновление прогресса в одной строке
        sys.stdout.write(f"\rИндексируется документ {i} из {total_docs}")
        sys.stdout.flush()

        # Если накопилось 100 документов или это последний документ, выполнять bulk-загрузку
        if i % 100 == 0 or i == total_docs:
            bulk(es, actions)
            actions = []

    # Переход на новую строку после завершения
    sys.stdout.write("\nИндексирование завершено!\n")


if __name__ == "__main__":
    create_index()
    # Укажите путь к вашему JSON файлу с данными
    data_path = "../../esDB/cleaned_general_info_additional.json"
    drug_data = load_drug_data(data_path)
    index_documents(drug_data)
