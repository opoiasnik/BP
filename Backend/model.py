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
#            translate all answer to slovak(temporary closed :) )         #
###############################################################################
# translator = Translator()
def translate_to_slovak(text: str) -> str:
    """
    Переводит весь текст на словацкий с логированием изменений.
    Сейчас функция является заглушкой и возвращает исходный текст без изменений.
    """
    # if not text.strip():
    #     return text
    #
    # logger.info("Translation - Before: " + text)
    # try:
    #     mid_result = translator.translate(text, src='auto', dest='en').text
    #     final_result = translator.translate(mid_result, src='en', dest='sk').text
    #     logger.info("Translation - After: " + final_result)
    #     before_words = text.split()
    #     after_words = final_result.split()
    #     diff = list(difflib.ndiff(before_words, after_words))
    #     changed_words = [word[2:] for word in diff if word.startswith('+ ')]
    #     if changed_words:
    #         logger.info("Changed words: " + ", ".join(changed_words))
    #     else:
    #         logger.info("No changed words detected.")
    #     return final_result
    # except Exception as e:
    #     logger.error(f"Translation error: {e}")
    #     return text
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
    # pattern = re.compile(r'^(\d+\.\s*[^:]+:\s*)(.*)$', re.MULTILINE)
    #
    # def replacer(match):
    #     prefix = match.group(1)
    #     description = match.group(2)
    #     logger.info("Translating description: " + description)
    #     translated_description = translate_to_slovak(description)
    #     logger.info("Translated description: " + translated_description)
    #     diff = list(difflib.ndiff(description.split(), translated_description.split()))
    #     changed_words = [word[2:] for word in diff if word.startswith('+ ')]
    #     if changed_words:
    #         logger.info("Changed words in description: " + ", ".join(changed_words))
    #     else:
    #         logger.info("No changed words in description detected.")
    #     return prefix + translated_description
    #
    # if pattern.search(text):
    #     return pattern.sub(replacer, text)
    # else:
    #     return translate_to_slovak(text)
    return text

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
#                  Helper function to evaluate model output                   #
###############################################################################
def evaluate_results(query, summaries, model_name):
    query_keywords = query.split()
    total_score = 0
    explanation = []
    for i, summary in enumerate(summaries):
        length_score = min(len(summary) / 100, 10)
        total_score += length_score
        explanation.append(f"Document {i+1}: Length score - {length_score}")
        keyword_matches = sum(1 for word in query_keywords if word.lower() in summary.lower())
        keyword_score = min(keyword_matches * 2, 10)
        total_score += keyword_score
        explanation.append(f"Document {i+1}: Keyword match score - {keyword_score}")
    final_score = total_score / len(summaries) if summaries else 0
    explanation_summary = "\n".join(explanation)
    logger.info(f"Evaluation for model {model_name}: {final_score}/10")
    logger.info(f"Explanation:\n{explanation_summary}")
    return {"rating": round(final_score, 2), "explanation": explanation_summary}

###############################################################################
#             validation of recieved answer is it correct for user question                    #
###############################################################################
def validate_answer_logic(query: str, answer: str) -> str:
    """
    Проверяет, соответствует ли ответ логике вопроса.
    Если, например, вопрос относится к ľudským liekom a obsahuje otázku na dávkovanie,
    odpoveď musí obsahovať iba lieky vhodné pre ľudí s uvedením správneho dávkovania.
    """
    validation_prompt = (
        f"Otázka: '{query}'\n"
        f"Odpoveď: '{answer}'\n\n"
        "Analyzuj prosím túto odpoveď. Ak odpoveď obsahuje odporúčania liekov, ktoré nie sú vhodné pre ľudí, "
        "alebo ak neobsahuje správne informácie o dávkovaní, oprav ju tak, aby bola logicky konzistentná s otázkou. "
        "Odpoveď musí obsahovať iba lieky určené pre ľudí a pri potrebe aj presné informácie o dávkovaní (napr. v gramoch). "
        "Ak je odpoveď logická a korektná, vráť pôvodnú odpoveď bez zmien. "
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
            vector_prompt = (
                f"Otázka: '{query}'.\n"
                "Na základe nasledujúcich informácií o liekoch:\n"
                f"{vector_documents}\n\n"
                "Prosím, uveďte tri najvhodnejšie lieky alebo riešenia pre daný problém. "
                "Pre každý liek uveďte jeho názov, stručné a jasné vysvetlenie, prečo je vhodný, a ak je to relevantné, "
                "aj odporúčané dávkovanie (napr. v gramoch alebo v iných vhodných jednotkách). "
                "Odpovedajte priamo a ľudským, priateľským tónom v číslovanom zozname, bez nepotrebných úvodných fráz. "
                "Odpoveď musí byť v slovenčine."
            )
            summary_small_vector = llm_small.generate_text(prompt=vector_prompt, max_tokens=700, temperature=0.7)
            summary_large_vector = llm_large.generate_text(prompt=vector_prompt, max_tokens=700, temperature=0.7)
            splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
            split_summary_small_vector = splitter.split_text(summary_small_vector)
            split_summary_large_vector = splitter.split_text(summary_large_vector)
            small_vector_eval = evaluate_results(query, split_summary_small_vector, 'Mistral Small')
            large_vector_eval = evaluate_results(query, split_summary_large_vector, 'Mistral Large')
        else:
            small_vector_eval = {"rating": 0, "explanation": "No results"}
            large_vector_eval = {"rating": 0, "explanation": "No results"}
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
            text_prompt = (
                f"Otázka: '{query}'.\n"
                "Na základe nasledujúcich informácií o liekoch:\n"
                f"{text_documents}\n\n"
                "Prosím, uveďte tri najvhodnejšie lieky alebo riešenia pre daný problém. "
                "Pre každý liek uveďte jeho názov, stručné a jasné vysvetlenie, prečo je vhodný, a ak je to relevantné, "
                "aj odporúčané dávkovanie (napr. v gramoch alebo v iných vhodných jednotkách). "
                "Odpovedajte priamo a ľudským, priateľským tónom v číslovanom zozname, bez nepotrebných úvodných fráz. "
                "Odpoveď musí byť v slovenčine."
            )
            summary_small_text = llm_small.generate_text(prompt=text_prompt, max_tokens=700, temperature=0.7)
            summary_large_text = llm_large.generate_text(prompt=text_prompt, max_tokens=700, temperature=0.7)
            splitter_text = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
            split_summary_small_text = splitter_text.split_text(summary_small_text)
            split_summary_large_text = splitter_text.split_text(summary_large_text)
            small_text_eval = evaluate_results(query, split_summary_small_text, 'Mistral Small')
            large_text_eval = evaluate_results(query, split_summary_large_text, 'Mistral Large')
        else:
            small_text_eval = {"rating": 0, "explanation": "No results"}
            large_text_eval = {"rating": 0, "explanation": "No results"}
            summary_small_text = ""
            summary_large_text = ""

        # Porovnanie výsledkov a výber najlepšieho
        all_results = [
            {"eval": small_vector_eval, "summary": summary_small_vector, "model": "Mistral Small Vector"},
            {"eval": large_vector_eval, "summary": summary_large_vector, "model": "Mistral Large Vector"},
            {"eval": small_text_eval, "summary": summary_small_text, "model": "Mistral Small Text"},
            {"eval": large_text_eval, "summary": summary_large_text, "model": "Mistral Large Text"},
        ]
        best_result = max(all_results, key=lambda x: x["eval"]["rating"])
        logger.info(f"Best result from model {best_result['model']} with score {best_result['eval']['rating']}.")

        # Dodatočná kontrola logiky odpovede
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

