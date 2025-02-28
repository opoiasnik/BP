import json
import requests
import logging
import time
import re
import difflib
from requests.exceptions import HTTPError
from elasticsearch import Elasticsearch
from langchain.chains import SequentialChain
from langchain.chains import LLMChain, SequentialChain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
# from googletrans import Translator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config_file_path = "config.json"
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)

mistral_api_key = "hXDC4RBJk1qy5pOlrgr01GtOlmyCBaNs"
if not mistral_api_key:
    raise ValueError("Mistral API key not found in configuration.")

###############################################################################
#            translate all answer to slovak (temporary closed :)            #
###############################################################################
def translate_to_slovak(text: str) -> str:
    """
    Функция перевода на словацкий.
    Сейчас функция является заглушкой и возвращает исходный текст без изменений.
    """
    return text

###############################################################################
#   Функция перевода описания лекарства с сохранением названия (до двоеточия)    #
###############################################################################
def translate_preserving_medicine_names(text: str) -> str:
    """
    Ищет строки вида "номер. Название лекарства: описание..." и переводит только описание,
    оставляя название без изменений.
    Сейчас функция является заглушкой и возвращает исходный текст без изменений.
    """
    return text

###############################################################################
#        Формирование динамического промта для генерации ответа               #
###############################################################################
def build_dynamic_prompt(query: str, documents: list) -> str:
    """
    Формирует финальный промт, который инструктирует модель:
      - проанализировать исходную вопрос пользователя и выявить дополнительные требования;
      - если они есть, в ответе сначала предоставить рекомендации по лекарствам
        (название, краткое объяснение и, если необходимо, дозировка или время приёма),
      - затем, в отдельной части, дать ответ на дополнительные вопросы;
      - если дополнительных требований нет – указать только рекомендации по лекарствам.
    """
    documents_str = "\n".join(documents)
    prompt = (
        f"Otázka: '{query}'.\n"
        "Na základe nasledujúcich informácií o liekoch:\n"
        f"{documents_str}\n\n"
        "Analyzuj uvedenú otázku a zisti, či obsahuje dodatočné požiadavky okrem odporúčania liekov. "
        "Ak áno, v odpovedi najprv uveď odporúčané lieky – pre každý liek uveď jeho názov, stručné vysvetlenie a, ak je to relevantné, "
        "odporúčané dávkovanie alebo čas užívania, a potom v ďalšej časti poskytnú odpoveď na dodatočné požiadavky. "
        "Ak dodatočné požiadavky nie sú prítomné, uveď len odporúčanie liekov. "
        "Odpovedz priamo a ľudským, priateľským tónom v číslovanom zozname, bez zbytočných úvodných fráz. "
        "Odpoveď musí byť v slovenčine."
    )
    return prompt

###############################################################################
#                             Custom Mistral LLM                              #
###############################################################################
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
                logger.info(f"Full response from model {self.model_name}: {result}")
                return result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
            except HTTPError as e:
                if response.status_code == 429:
                    logger.warning(f"Rate limit exceeded. Waiting {delay} seconds before retry.")
                    time.sleep(delay)
                    attempt += 1
                else:
                    logger.error(f"HTTP Error: {e}")
                    raise e
            except Exception as e:
                logger.error(f"Error: {str(e)}")
                raise e
        raise Exception("Reached maximum number of retries for API request")

###############################################################################
#                 Initialize embeddings and Elasticsearch store               #
###############################################################################
logger.info("Loading HuggingFaceEmbeddings model...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

index_name = 'drug_docs'

if config.get("useCloud", False):
    logger.info("Using cloud Elasticsearch.")
    cloud_id = "tt:dXMtZWFzdC0yLmF3cy5lbGFzdGljLWNsb3VkLmNvbTo0NDMkOGM3ODQ0ZWVhZTEyNGY3NmFjNjQyNDFhNjI4NmVhYzMkZTI3YjlkNTQ0ODdhNGViNmEyMTcxMjMxNmJhMWI0ZGU="
    vectorstore = ElasticsearchStore(
        es_cloud_id=cloud_id,
        index_name='drug_docs',
        embedding=embeddings,
        es_user="elastic",
        es_password="sSz2BEGv56JRNjGFwoQ191RJ"
    )
else:
    logger.info("Using local Elasticsearch.")
    vectorstore = ElasticsearchStore(
        es_url="http://localhost:9200",
        index_name=index_name,
        embedding=embeddings,
    )

logger.info(f"Connected to {'cloud' if config.get('useCloud', False) else 'local'} Elasticsearch.")

###############################################################################
#                 Initialize Mistral models (small & large)                   #
###############################################################################
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

###############################################################################
#       Новая функция для детальной оценки логики и полноты ответа           #
###############################################################################
def evaluate_complete_answer(query: str, answer: str) -> dict:
    """
    Отправляет промт LLM, который должен оценить, соответствует ли ответ следующим критериям:
      1. Ответ содержит рекомендации liekov vrátane názvu, stručného vysvetlenia
         a (ak bolo žiadané) aj dávkovania alebo času užívania.
      2. Если otázka obsahovala dodatočné požiadavky, odpoveď obsahuje aj samostatnú časť,
         ktorá tieto požiadavky rieši.
    Na základe týchto kritérií vráti hodnotenie od 0 do 10.
    """
    evaluation_prompt = (
         f"Vyhodnoť nasledujúcu odpoveď na základe týchto kritérií:\n"
         f"1. Odpoveď obsahuje odporúčania liekov vrátane názvu, stručného vysvetlenia a, ak bolo žiadané, aj dávkovanie alebo čas užívania.\n"
         f"2. Ak otázka obsahovala dodatočné požiadavky, odpoveď má samostatnú časť, ktorá tieto požiadavky rieši.\n\n"
         f"Otázka: '{query}'\n"
         f"Odpoveď: '{answer}'\n\n"
         "Na základe týchto kritérií daj odpovedi hodnotenie od 0 do 10, kde 10 znamená, že odpoveď je úplne logická a obsahuje všetky požadované informácie. "
         "Vráť len číslo."
    )
    score_str = llm_small.generate_text(prompt=evaluation_prompt, max_tokens=50, temperature=0.3)
    try:
         score = float(score_str.strip())
    except Exception as e:
         logger.error(f"Error parsing evaluation score: {e}")
         score = 0.0
    return {"rating": round(score, 2), "explanation": "Evaluation based on required criteria."}

###############################################################################
#             Validation of received answer against user question             #
###############################################################################
def validate_answer_logic(query: str, answer: str) -> str:
    """
    Проверяет, соответствует ли ответ логике вопроса.
    Если в ответе отсутствуют требуемые элементы (например, отсутствует раздел с dávkovanie/čas
    при наличии dodatočných požiadaviek), модель должна исправить ответ.
    """
    validation_prompt = (
        f"Otázka: '{query}'\n"
        f"Odpoveď: '{answer}'\n\n"
        "Analyzuj prosím túto odpoveď. Ak odpoveď neobsahuje všetky dodatočné informácie, na ktoré sa pýtal používateľ, "
        "alebo ak odporúčania liekov nie sú úplné (napr. chýba dávkovanie alebo čas užívania, ak boli takéto požiadavky v otázke), "
        "vytvor opravenú odpoveď, ktorá je logicky konzistentná s otázkou. "
        "Odpovedz v slovenčine a iba čistou, konečnou odpoveďou bez ďalších komentárov."
    )
    try:
        validated_answer = llm_small.generate_text(prompt=validation_prompt, max_tokens=500, temperature=0.5)
        logger.info(f"Validated answer: {validated_answer}")
        return validated_answer
    except Exception as e:
        logger.error(f"Error during answer validation: {e}")
        return answer

###############################################################################
#           Main function: process_query_with_mistral (Slovak prompt)         #
###############################################################################
def process_query_with_mistral(query, k=10):
    logger.info("Processing query started.")
    try:
        # --- Vector search ---
        vector_results = vectorstore.similarity_search(query, k=k)
        vector_documents = [hit.metadata.get('text', '') for hit in vector_results]
        max_docs = 5
        max_doc_length = 1000
        vector_documents = [doc[:max_doc_length] for doc in vector_documents[:max_docs]]
        if vector_documents:
            # Формируем промт для генерации ответа
            vector_prompt = build_dynamic_prompt(query, vector_documents)
            summary_small_vector = llm_small.generate_text(prompt=vector_prompt, max_tokens=700, temperature=0.7)
            summary_large_vector = llm_large.generate_text(prompt=vector_prompt, max_tokens=700, temperature=0.7)
            splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
            split_summary_small_vector = splitter.split_text(summary_small_vector)
            split_summary_large_vector = splitter.split_text(summary_large_vector)
            eval_small_vector = evaluate_complete_answer(query, summary_small_vector)
            eval_large_vector = evaluate_complete_answer(query, summary_large_vector)
        else:
            eval_small_vector = {"rating": 0, "explanation": "No results"}
            eval_large_vector = {"rating": 0, "explanation": "No results"}
            summary_small_vector = ""
            summary_large_vector = ""

        # --- Text search ---
        es_results = vectorstore.client.search(
            index=index_name,
            body={"size": k, "query": {"match": {"text": query}}}
        )
        text_documents = [hit['_source'].get('text', '') for hit in es_results['hits']['hits']]
        text_documents = [doc[:max_doc_length] for doc in text_documents[:max_docs]]
        if text_documents:
            text_prompt = build_dynamic_prompt(query, text_documents)
            summary_small_text = llm_small.generate_text(prompt=text_prompt, max_tokens=700, temperature=0.7)
            summary_large_text = llm_large.generate_text(prompt=text_prompt, max_tokens=700, temperature=0.7)
            splitter_text = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
            split_summary_small_text = splitter_text.split_text(summary_small_text)
            split_summary_large_text = splitter_text.split_text(summary_large_text)
            eval_small_text = evaluate_complete_answer(query, summary_small_text)
            eval_large_text = evaluate_complete_answer(query, summary_large_text)
        else:
            eval_small_text = {"rating": 0, "explanation": "No results"}
            eval_large_text = {"rating": 0, "explanation": "No results"}
            summary_small_text = ""
            summary_large_text = ""

        # Сравнение результатов и выбор лучшего варианта
        all_results = [
            {"eval": eval_small_vector, "summary": summary_small_vector, "model": "Mistral Small Vector"},
            {"eval": eval_large_vector, "summary": summary_large_vector, "model": "Mistral Large Vector"},
            {"eval": eval_small_text, "summary": summary_small_text, "model": "Mistral Small Text"},
            {"eval": eval_large_text, "summary": summary_large_text, "model": "Mistral Large Text"},
        ]
        best_result = max(all_results, key=lambda x: x["eval"]["rating"])
        logger.info(f"Best result from model {best_result['model']} with score {best_result['eval']['rating']}.")

        # Дополнительная проверка логики ответа
        validated_answer = validate_answer_logic(query, best_result["summary"])

        polished_answer = translate_preserving_medicine_names(validated_answer)
        return {
            "best_answer": polished_answer,
            "model": best_result["model"],
            "rating": best_result["eval"]["rating"],
            "explanation": best_result["eval"]["explanation"]
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            "best_answer": "An error occurred during query processing.",
            "error": str(e)
        }
