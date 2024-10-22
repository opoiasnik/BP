from elasticsearch import Elasticsearch
import json
import requests
from langchain.chains import SequentialChain
from langchain.chains import LLMChain, SequentialChain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




mistral_api_key = "hXDC4RBJk1qy5pOlrgr01GtOlmyCBaNs"
if not mistral_api_key:
    raise ValueError("API ключ не найден.")


class CustomMistralLLM:
    def __init__(self, api_key: str, endpoint_url: str):
        self.api_key = api_key
        self.endpoint_url = endpoint_url

    def generate_text(self, prompt: str, max_tokens=512, temperature=0.7):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        response = requests.post(self.endpoint_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Полный ответ от модели Mistral: {result}")
        return result.get("choices", [{}])[0].get("message", {}).get("content", "No response")


logger.info("Загрузка модели HuggingFaceEmbeddings...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


config_file_path = "config.json"


with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)

#  Cloud ID
if config.get("useCloud", False):
    logger.info("CLOUD ELASTIC")
    cloud_id = "tt:dXMtZWFzdC0yLmF3cy5lbGFzdGljLWNsb3VkLmNvbTo0NDMkOGM3ODQ0ZWVhZTEyNGY3NmFjNjQyNDFhNjI4NmVhYzMkZTI3YjlkNTQ0ODdhNGViNmEyMTcxMjMxNmJhMWI0ZGU="  # Замените на ваш Cloud ID
    vectorstore = ElasticsearchStore(
        es_cloud_id=cloud_id,
        index_name='drug_docs',
        embedding=embeddings,
        es_user = "elastic",
        es_password = "sSz2BEGv56JRNjGFwoQ191RJ",
    )
else:
    logger.info("LOCAL ELASTIC")
    vectorstore = ElasticsearchStore(
        es_url="http://localhost:9200",
        index_name='drug_docs',
        embedding=embeddings,
    )

logger.info(f"Подключение установлено к {'облачному' if config.get('useCloud', False) else 'локальному'} Elasticsearch")

# LLM
llm = CustomMistralLLM(
    api_key=mistral_api_key,
    endpoint_url="https://api.mistral.ai/v1/chat/completions"
)

def process_query_with_mistral(query, k=10):
    logger.info("Обработка запроса началась.")
    try:
        # Elasticsearch LangChain
        response = vectorstore.similarity_search(query, k=k)
        if not response:
            return {"summary": "Ничего не найдено", "links": [], "status_log": ["Ничего не найдено."]}

        documents = [hit.metadata.get('text', '') for hit in response]
        links = [hit.metadata.get('link', '-') for hit in response]
        structured_prompt = (
            f"Na základe otázky: '{query}' a nasledujúcich informácií o liekoch: {documents}. "
            "Uveďte tri vhodné lieky alebo riešenia s krátkym vysvetlením pre každý z nich. "
            "Odpoveď musí byť v slovenčine."
        )

        summary = llm.generate_text(prompt=structured_prompt, max_tokens=512, temperature=0.7)

        #TextSplitter
        splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
        split_summary = splitter.split_text(summary)

        return {"summary": split_summary, "links": links, "status_log": ["Ответ получен от модели Mistral."]}
    except Exception as e:
        logger.info(f"Ошибка: {str(e)}")
        return {"summary": "Произошла ошибка", "links": [], "status_log": [f"Ошибка: {str(e)}"]}
