from elasticsearch import Elasticsearch
from langchain_huggingface import HuggingFaceEmbeddings
import json
import sys

es = Elasticsearch(
    cloud_id="tt:dXMtZWFzdC0yLmF3cy5lbGFzdGljLWNsb3VkLmNvbTo0NDMkOGM3ODQ0ZWVhZTEyNGY3NmFjNjQyNDFhNjI4NmVhYzMkZTI3YjlkNTQ0ODdhNGViNmEyMTcxMjMxNmJhMWI0ZGU=",
    basic_auth=("elastic", "sSz2BEGv56JRNjGFwoQ191RJ")
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def load_drug_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def index_documents(data):
    total_documents = len(data)
    for i, item in enumerate(data, start=1):
        doc_text = f"{item['link']} {item.get('pribalovy_letak', '')} {item.get('spc', '')}"

        vector = embeddings.embed_query(doc_text)

        es.index(index='drug_docs', id=i, body={
            'text': doc_text,
            'vector': vector,
            'full_data': item
        })


        sys.stdout.flush()




data_path = "../../data_adc_databaza/cleaned_general_info_additional.json"
drug_data = load_drug_data(data_path)
index_documents(drug_data)
