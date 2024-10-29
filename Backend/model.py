import json
import requests
import logging
import time
import re
from requests.exceptions import HTTPError
from elasticsearch import Elasticsearch
from langchain.chains import SequentialChain
from langchain.chains import LLMChain, SequentialChain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
config_file_path = "config.json"

with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)

# Загрузка API ключа Mistral
mistral_api_key = "hXDC4RBJk1qy5pOlrgr01GtOlmyCBaNs"
if not mistral_api_key:
    raise ValueError("API ключ Mistral не найден в конфигурации.")


# Класс для работы с моделями Mistral через OpenAI API
class CustomMistralLLM:
    def __init__(self, api_key: str, endpoint_url: str, model_name: str):
        self.api_key = api_key
        self.endpoint_url = endpoint_url
        self.model_name = model_name

    def generate_text(self, prompt: str, max_tokens=512, temperature=0.7, retries=3, delay=2):
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
        attempt = 0
        while attempt < retries:
            try:
                response = requests.post(self.endpoint_url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(f"Полный ответ от модели {self.model_name}: {result}")
                return result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
            except HTTPError as e:
                if response.status_code == 429:  # Too Many Requests
                    logger.warning(f"Превышен лимит запросов. Ожидание {delay} секунд перед повторной попыткой.")
                    time.sleep(delay)
                    attempt += 1
                else:
                    logger.error(f"HTTP Error: {e}")
                    raise e
            except Exception as e:
                logger.error(f"Ошибка: {str(e)}")
                raise e
        raise Exception("Превышено количество попыток запроса к API")


# Инициализация эмбеддингов
logger.info("Загрузка модели HuggingFaceEmbeddings...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Определяем имя индекса
index_name = 'drug_docs'

# Подключение к Elasticsearch
if config.get("useCloud", False):
    logger.info("CLOUD ELASTIC")
    cloud_id = "tt:dXMtZWFzdC0yLmF3cy5lbGFzdGljLWNsb3VkLmNvbTo0NDMkOGM3ODQ0ZWVhZTEyNGY3NmFjNjQyNDFhNjI4NmVhYzMkZTI3YjlkNTQ0ODdhNGViNmEyMTcxMjMxNmJhMWI0ZGU="  # Замените на ваш Cloud ID
    vectorstore = ElasticsearchStore(
        es_cloud_id=cloud_id,
        index_name='drug_docs',
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


# Функция для оценки релевантности результатов
def evaluate_results(query, summaries, model_name):
    """
    Оценивает результаты на основе длины текста, наличия ключевых слов из запроса
    и других подходящих критериев. Используется для определения качества вывода от модели.
    """
    query_keywords = query.split()  # Получаем ключевые слова из запроса
    total_score = 0
    explanation = []

    for i, summary in enumerate(summaries):
        # Оценка по длине ответа
        length_score = min(len(summary) / 100, 10)
        total_score += length_score
        explanation.append(f"Document {i+1}: Length score - {length_score}")

        # Оценка по количеству совпадений ключевых слов
        keyword_matches = sum(1 for word in query_keywords if word.lower() in summary.lower())
        keyword_score = min(keyword_matches * 2, 10)  # Максимальная оценка за ключевые слова - 10
        total_score += keyword_score
        explanation.append(f"Document {i+1}: Keyword match score - {keyword_score}")

    # Средняя оценка по количеству документов
    final_score = total_score / len(summaries) if summaries else 0
    explanation_summary = "\n".join(explanation)

    logger.info(f"Оценка для модели {model_name}: {final_score}/10")
    logger.info(f"Пояснение оценки:\n{explanation_summary}")

    return {"rating": round(final_score, 2), "explanation": explanation_summary}



# Функция для сравнения результатов двух моделей
# Функция для сравнения результатов двух моделей
# Функция для сравнения результатов двух моделей
def compare_models(small_model_results, large_model_results, query):
    logger.info("Начато сравнение моделей Mistral Small и Mistral Large")

    # Логируем результаты
    logger.info("Сравнение оценок моделей:")
    logger.info(f"Mistral Small: Оценка - {small_model_results['rating']}, Объяснение - {small_model_results['explanation']}")
    logger.info(f"Mistral Large: Оценка - {large_model_results['rating']}, Объяснение - {large_model_results['explanation']}")

    # Форматируем вывод для текстового и векторного поиска
    comparison_summary = {
        "query": query,
        "text_search": f"Текстовый поиск: Mistral Small - {small_model_results['rating']}/10, Mistral Large - {large_model_results['rating']}/10",
        "vector_search": f"Векторный поиск: Mistral Small - {small_model_results['rating']}/10, Mistral Large - {large_model_results['rating']}/10"
    }

    logger.info(f"Результат сравнения: \n{comparison_summary['text_search']}\n{comparison_summary['vector_search']}")

    return comparison_summary




# Функция для обработки запроса
# Функция для обработки запроса
# Функция для обработки запроса
def process_query_with_mistral(query, k=10):
    logger.info("Обработка запроса началась.")
    try:
        # --- ВЕКТОРНЫЙ ПОИСК ---
        vector_results = vectorstore.similarity_search(query, k=k)
        vector_documents = [hit.metadata.get('text', '') for hit in vector_results]

        # Ограничиваем количество документов и их длину
        max_docs = 5
        max_doc_length = 1000
        vector_documents = [doc[:max_doc_length] for doc in vector_documents[:max_docs]]

        if vector_documents:
            vector_prompt = (
                f"Na základe otázky: '{query}' a nasledujúcich informácií o liekoch: {vector_documents}. "
                "Uveďte tri vhodné lieky или riešenia с кратким vysvetlením pre každý z nich. "
                "Odpoveď musí byť в slovenčine."
            )
            summary_small_vector = llm_small.generate_text(prompt=vector_prompt, max_tokens=700, temperature=0.7)
            summary_large_vector = llm_large.generate_text(prompt=vector_prompt, max_tokens=700, temperature=0.7)

            splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
            split_summary_small_vector = splitter.split_text(summary_small_vector)
            split_summary_large_vector = splitter.split_text(summary_large_vector)

            # Оценка векторных результатов
            small_vector_eval = evaluate_results(query, split_summary_small_vector, 'Mistral Small')
            large_vector_eval = evaluate_results(query, split_summary_large_vector, 'Mistral Large')
        else:
            small_vector_eval = {"rating": 0, "explanation": "No results"}
            large_vector_eval = {"rating": 0, "explanation": "No results"}

        # --- ТЕКСТОВЫЙ ПОИСК ---
        es_results = vectorstore.client.search(
            index=index_name,
            body={"size": k, "query": {"match": {"text": query}}}
        )
        text_documents = [hit['_source'].get('text', '') for hit in es_results['hits']['hits']]
        text_documents = [doc[:max_doc_length] for doc in text_documents[:max_docs]]

        if text_documents:
            text_prompt = (
                f"Na základe otázky: '{query}' a nasledujúcich informácií о liekoch: {text_documents}. "
                "Uveďte три vhodné lieky alebo riešenia с кратким vysvetленím pre každý з них. "
                "Odpoveď musí byť в slovenčine."
            )
            summary_small_text = llm_small.generate_text(prompt=text_prompt, max_tokens=700, temperature=0.7)
            summary_large_text = llm_large.generate_text(prompt=text_prompt, max_tokens=700, temperature=0.7)

            split_summary_small_text = splitter.split_text(summary_small_text)
            split_summary_large_text = splitter.split_text(summary_large_text)

            # Оценка текстовых результатов
            small_text_eval = evaluate_results(query, split_summary_small_text, 'Mistral Small')
            large_text_eval = evaluate_results(query, split_summary_large_text, 'Mistral Large')
        else:
            small_text_eval = {"rating": 0, "explanation": "No results"}
            large_text_eval = {"rating": 0, "explanation": "No results"}

        # Выбираем лучший результат среди всех
        all_results = [
            {"eval": small_vector_eval, "summary": summary_small_vector, "model": "Mistral Small Vector"},
            {"eval": large_vector_eval, "summary": summary_large_vector, "model": "Mistral Large Vector"},
            {"eval": small_text_eval, "summary": summary_small_text, "model": "Mistral Small Text"},
            {"eval": large_text_eval, "summary": summary_large_text, "model": "Mistral Large Text"},
        ]

        best_result = max(all_results, key=lambda x: x["eval"]["rating"])

        logger.info(f"Лучший результат от модели {best_result['model']} с оценкой {best_result['eval']['rating']}.")

        # Возвращаем только лучший ответ
        return {
            "best_answer": best_result["summary"],
            "model": best_result["model"],
            "rating": best_result["eval"]["rating"],
            "explanation": best_result["eval"]["explanation"]
        }

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return {
            "best_answer": "Произошла ошибка при обработке запроса.",
            "error": str(e)
        }
