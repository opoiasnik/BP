from elasticsearch import Elasticsearch
import json
import requests
from langchain.chains import SequentialChain
from langchain.chains import LLMChain, SequentialChain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mistral_api_key = "hXDC4RBJk1qy5pOlrgr01GtOlmyCBaNs"
if not mistral_api_key:
    raise ValueError("API ключ не найден.")

# Класс для работы с моделями Mistral через OpenAI API
class CustomMistralLLM:
    def __init__(self, api_key: str, endpoint_url: str, model_name: str):
        self.api_key = api_key
        self.endpoint_url = endpoint_url
        self.model_name = model_name

    def generate_text(self, prompt: str, max_tokens=512, temperature=0.7):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            response = requests.post(self.endpoint_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Полный ответ от модели {self.model_name}: {result}")
            return result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
        except requests.exceptions.HTTPError as e:
            error_content = response.content.decode('utf-8')
            logger.error(f"HTTP Error: {e}")
            logger.error(f"Response content: {error_content}")
            raise e


logger.info("Загрузка модели HuggingFaceEmbeddings...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

config_file_path = "config.json"

with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)

# Определяем имя индекса
index_name = 'drug_docs'

# Подключение к Elasticsearch
if config.get("useCloud", False):
    logger.info("CLOUD ELASTIC")
    cloud_id = "tt:dXMtZWFzdC0yLmF3cy5lbGFzdGljLWNsb3VkLmNvbTo0NDMkOGM3ODQ0ZWVhZTEyNGY3NmFjNjQyNDFhNjI4NmVhYzMkZTI3YjlkNTQ0ODdhNGViNmEyMTcxMjMxNmJhMWI0ZGU="
    vectorstore = ElasticsearchStore(
        es_cloud_id=cloud_id,
        index_name=index_name,
        embedding=embeddings,
        es_user="elastic",
        es_password="sSz2BEGv56JRNjGFwoQ191RJ",
    )
else:
    logger.info("LOCAL ELASTIC")
    vectorstore = ElasticsearchStore(
        es_url="http://localhost:9200",
        index_name=index_name,
        embedding=embeddings,
    )

logger.info(f"Подключение установлено к {'облачному' if config.get('useCloud', False) else 'локальному'} Elasticsearch")

# Инициализация моделей
llm_small = CustomMistralLLM(
    api_key=mistral_api_key,
    endpoint_url="https://api.mistral.ai/v1/chat/completions",
    model_name="mistral-small-latest"
)

llm_large = CustomMistralLLM(
    api_key=mistral_api_key,
    endpoint_url="https://api.mistral.ai/v1/chat/completions",
    model_name="mistral-large-latest"
)

def process_query_with_mistral(query, k=10):
    logger.info("Обработка запроса началась.")
    try:
        # --- ВЕКТОРНЫЙ ПОИСК ---
        vector_results = vectorstore.similarity_search(query, k=k)
        vector_documents = [hit.metadata.get('text', '') for hit in vector_results]
        vector_links = [hit.metadata.get('link', '-') for hit in vector_results]

        # Ограничиваем количество документов и их длину
        max_docs = 5
        max_doc_length = 1000  # или другое подходящее значение
        vector_documents = [doc[:max_doc_length] for doc in vector_documents[:max_docs]]

        if not vector_documents:
            vector_summaries = {
                "small": "Nenašli sa žiadne výsledky vo vektorovom vyhľadávaní.",
                "large": "Nenašli sa žiadne výsledky vo vektorovom vyhľadávaní."
            }
            vector_status_log = ["Nenašli sa žiadne výsledky vo vektorovom vyhľadávaní."]
        else:
            # Формируем запрос для моделей на основе векторных результатов
            vector_prompt = (
                f"Na základe otázky: '{query}' a nasledujúcich informácií o liekoch: {vector_documents}. "
                "Uveďte tri vhodné lieky alebo riešenia s krátkym vysvetlením pre každý z nich. "
                "Odpoveď musí byť v slovenčine."
            )
            # Получаем ответы от моделей для векторного поиска
            summary_small_vector = llm_small.generate_text(prompt=vector_prompt, max_tokens=512, temperature=0.7)
            summary_large_vector = llm_large.generate_text(prompt=vector_prompt, max_tokens=512, temperature=0.7)

            # Разделяем ответы на более мелкие части
            splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
            split_summary_small_vector = splitter.split_text(summary_small_vector)
            split_summary_large_vector = splitter.split_text(summary_large_vector)

            vector_summaries = {
                "small": split_summary_small_vector,
                "large": split_summary_large_vector
            }
            vector_status_log = ["Ответы получены от моделей на основе векторного поиска."]

        # --- ТЕКСТОВЫЙ ПОИСК ---
        es_results = vectorstore.client.search(
            index=index_name,
            body={
                "size": k,
                "query": {
                    "match": {
                        "text": query
                    }
                }
            }
        )

        text_results = []
        for hit in es_results['hits']['hits']:
            doc = Document(
                page_content=hit['_source'].get('text', ''),
                metadata={
                    'text': hit['_source'].get('text', ''),
                    'link': hit['_source'].get('full_data', {}).get('link', '-')
                }
            )
            text_results.append(doc)

        text_documents = [doc.metadata.get('text', '') for doc in text_results]
        text_links = [doc.metadata.get('link', '-') for doc in text_results]

        # Ограничиваем количество документов и их длину
        text_documents = [doc[:max_doc_length] for doc in text_documents[:max_docs]]

        if not text_documents:
            text_summaries = {
                "small": "Nenašli sa žiadne výsledky v textovom vyhľadávaní.",
                "large": "Nenašli sa žiadne výsledky v textovom vyhľadávaní."
            }
            text_status_log = ["Nenašli sa žiadne výsledky v textovom vyhľadávaní."]
        else:
            # Формируем запрос для моделей на основе текстовых результатов
            text_prompt = (
                f"Na základe otázky: '{query}' a nasledujúcich informácií o liekoch: {text_documents}. "
                "Uveďte tri vhodné lieky alebo riešenia s krátkym vysvetlením pre každý z nich. "
                "Odpoveď musí byť v slovenčine."
            )
            # Получаем ответы от моделей для текстового поиска
            summary_small_text = llm_small.generate_text(prompt=text_prompt, max_tokens=512, temperature=0.7)
            summary_large_text = llm_large.generate_text(prompt=text_prompt, max_tokens=512, temperature=0.7)

            # Разделяем ответы на более мелкие части
            splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
            split_summary_small_text = splitter.split_text(summary_small_text)
            split_summary_large_text = splitter.split_text(summary_large_text)

            text_summaries = {
                "small": split_summary_small_text,
                "large": split_summary_large_text
            }
            text_status_log = ["Ответы получены от моделей na základe текстového vyhľadávania."]

        # Возвращаем результаты обоих поисков
        return {
            "vector_search": {
                "summaries": vector_summaries,
                "links": vector_links[:max_docs],
                "status_log": vector_status_log
            },
            "text_search": {
                "summaries": text_summaries,
                "links": text_links[:max_docs],
                "status_log": text_status_log
            }
        }

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return {
            "vector_search": {
                "summaries": {
                    "small": "Došlo k chybe vo vektorovom vyhľadávaní.",
                    "large": "Došlo k chybe vo vektorovom vyhľadávaní."
                },
                "links": [],
                "status_log": [f"Ошибка: {str(e)}"]
            },
            "text_search": {
                "summaries": {
                    "small": "Došlo k chybe v textovom vyhľadávaní.",
                    "large": "Došlo k chybe v textovom vyhľadávaní."
                },
                "links": [],
                "status_log": [f"Ошибка: {str(e)}"]
            }
        }




