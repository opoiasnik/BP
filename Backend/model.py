import json
import requests
import logging
import time
import re
from requests.exceptions import HTTPError
from elasticsearch import Elasticsearch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
config_file_path = "config.json"
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)

# Загрузка API ключа Mistral
mistral_api_key = "hXDC4RBJk1qy5pOlrgr01GtOlmyCBaNs"
if not mistral_api_key:
    raise ValueError("Mistral API key not found in configuration.")

###############################################################################
# Функции для перевода (заглушки)
###############################################################################
def translate_to_slovak(text: str) -> str:
    return text

def translate_preserving_medicine_names(text: str) -> str:
    return text

###############################################################################
# Функция для генерации подробного описания оценки через Mistral
###############################################################################
def generate_detailed_description(query: str, answer: str, rating: float) -> str:
    prompt = (
        f"Podrobne opíš, prečo odpoveď: '{answer}' na otázku: '{query}' dosiahla hodnotenie {rating} zo 10. "
        "Uveď relevantné aspekty, ktoré ovplyvnili toto hodnotenie, vrátane úplnosti, presnosti a kvality vysvetlenia."
    )
    try:
        description = llm_small.generate_text(prompt=prompt, max_tokens=150, temperature=0.5)
        return description.strip()
    except Exception as e:
        logger.error(f"Error generating detailed description: {e}")
        return "Nie je dostupný podrobný popis."

###############################################################################
# Функция для оценки полноty ответа
###############################################################################
def evaluate_complete_answer(query: str, answer: str) -> dict:
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
# Функция для валидации логики ответа
###############################################################################
def validate_answer_logic(query: str, answer: str) -> str:
    validation_prompt = (
        f"Otázka: '{query}'\n"
        f"Odpoveď: '{answer}'\n\n"
        "Analyzuj prosím túto odpoveď. Ak odpoveď neobsahuje všetky dodatočné informácie, na ktoré sa pýtal používateľ, "
        "alebo ak odporúčania liekov nie sú úplné (napr. chýba dávkovanie alebo čas užívania, ak boli takéto požiadavky v otázke), "
        "vytvor opravenú odpoveď, ktorá je logicky konzistentná s otázkou. "
        "Odpovedz v slovenčine a iba čistou, konečnou odpoveďou bez ďalších komentárov."
    )
    try:
        validated_answer = llm_small.generate_text(prompt=validation_prompt, max_tokens=800, temperature=0.5)
        logger.info(f"Validated answer: {validated_answer}")
        return validated_answer
    except Exception as e:
        logger.error(f"Error during answer validation: {e}")
        return answer

###############################################################################
# Функция для логирования результатов оценки в файл
###############################################################################
def log_evaluation_to_file(model: str, search_type: str, rating: float, detailed_desc: str, answer: str):
    safe_model = model.replace(" ", "_")
    file_name = f"{safe_model}_{search_type}.txt"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_entry = (
        f"Timestamp: {timestamp}\n"
        f"Rating: {rating}/10\n"
        f"Detailed description:\n{detailed_desc}\n"
        f"Answer:\n{answer}\n"
        + "=" * 80 + "\n\n"
    )
    try:
        with open(file_name, "a", encoding="utf-8") as f:
            f.write(log_entry)
        logger.info(f"Hodnotenie bolo zapísané do súboru {file_name}.")
    except Exception as e:
        logger.error(f"Error writing evaluation to file {file_name}: {e}")

###############################################################################
# Функция для создания динамического prompt-а с информацией из документов
###############################################################################
def build_dynamic_prompt(query: str, documents: list) -> str:
    documents_str = "\n".join(documents)
    prompt = (
        f"Otázka: '{query}'.\n"
        "Na základe nasledujúcich informácií o liekoch (použi tieto údaje pri generovaní odpovede):\n"
        f"{documents_str}\n\n"
        "Prosím, v odpovedi zahrň konkrétne informácie z týchto dokumentov a uveď odporúčania liekov s dávkovaním, "
        "ak sú takéto údaje dostupné. Odpoveď musí byť v slovenčine."
    )
    return prompt

###############################################################################
# Функция для получения user_data из БД через endpoint /api/get_user_data
###############################################################################
def get_user_data_from_db(chat_id: str) -> str:
    try:
        response = requests.get("http://localhost:5000/api/get_user_data", params={"chatId": chat_id})
        if response.status_code == 200:
            data = response.json()
            return data.get("user_data", "")
        else:
            logger.warning(f"Nezískané user_data, status: {response.status_code}")
    except Exception as e:
        logger.error(f"Error retrieving user_data from DB: {e}", exc_info=True)
    return ""

###############################################################################
# Класс для работы с Mistral LLM через API
###############################################################################
class CustomMistralLLM:
    def __init__(self, api_key: str, endpoint_url: str, model_name: str):
        self.api_key = api_key
        self.endpoint_url = endpoint_url
        self.model_name = model_name

    def generate_text(self, prompt: str, max_tokens=812, temperature=0.7, retries=3, delay=2):
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
            except Exception as ex:
                logger.error(f"Error: {str(ex)}")
                raise ex
        raise Exception("Reached maximum number of retries for API request")

###############################################################################
# Инициализация эмбеддингов и Elasticsearch
###############################################################################
logger.info("Loading HuggingFaceEmbeddings model...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

index_name = "drug_docs"
if config.get("useCloud", False):
    logger.info("Using cloud Elasticsearch.")
    cloud_id = "tt:dXMtZWFzdC0yLmF3cy5lbGFzdGljLWNsb3VkLmNvbTo0NDMkOGM3ODQ0ZWVhZTEyNGY3NmFjNjQyNDFhNjI4NmVhYzMkZTI3YjlkNTQ0ODdhNGViNmEyMTcxMjMxNmJhMWI0ZGU="
    vectorstore = ElasticsearchStore(
        es_cloud_id=cloud_id,
        index_name=index_name,
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
logger.info("Connected to Elasticsearch.")

###############################################################################
# Инициализация моделей Mistral Small & Large
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
# Функция классификации запроса
###############################################################################
def classify_query(query: str, chat_history: str = "") -> str:
    if not chat_history.strip():
        return "vyhladavanie"
    prompt = (
        "Ty si zdravotnícky expert, ktorý analyzuje otázky používateľov. "
        "Analyzuj nasledujúci dopyt a urči, či ide o dopyt na vyhľadanie liekov alebo "
        "o upresnenie/doplnenie už poskytnutej odpovede.\n"
        "Ak dopyt obsahuje výrazy ako 'čo pit', 'aké lieky', 'odporuč liek', 'hľadám liek', "
        "odpovedaj slovom 'vyhľadávanie'.\n"
        "Ak dopyt slúži na upresnenie, napríklad obsahuje výrazy ako 'a nie na predpis', "
        "'upresni', 'este raz', odpovedaj slovom 'upresnenie'.\n"
        f"Dopyt: \"{query}\""
    )
    classification = llm_small.generate_text(prompt=prompt, max_tokens=20, temperature=0.3)
    classification = classification.strip().lower()
    logger.info(f"Klasifikácia dopytu: {classification}")
    return classification

###############################################################################
# Шаблон prompt-а для уточнения запроса (без истории)
###############################################################################
def build_upresnenie_prompt_no_history(chat_history: str, user_query: str) -> str:
    prompt = f"""
Ty si zdravotnícky expert. Máš k dispozícii históriu chatu a novú upresňujúcu otázku.

Ak v histórii chatu už existuje jasná odpoveď na túto upresňujúcu otázku, napíš:
"FOUND_IN_HISTORY: <ľudský vysvetľajúci text>"

Ak však v histórii chatu nie je dostatok informácií, napíš:
"NO_ANSWER_IN_HISTORY: <krátky vyhľadávací dotaz do Elasticsearch>"

V časti <krátky vyhľadávací dotaz> zahrň kľúčové slová z pôvodnej otázky aj z upresnenia.

=== ZAČIATOK HISTÓRIE CHatu ===
{chat_history}
=== KONIEC HISTÓRIE CHatu ===

Upresňujúca otázka od používateľa:
"{user_query}"
"""
    return prompt

###############################################################################
# Функция для извлечения последнего vyhladavacieho запроса из истории
###############################################################################
def extract_last_vyhladavacie_query(chat_history: str) -> str:
    lines = chat_history.splitlines()
    last_query = ""
    for line in reversed(lines):
        if line.startswith("User:"):
            last_query = line[len("User:"):].strip()
            break
    return last_query

###############################################################################
# Класс агента для хранения данных
###############################################################################
class ConversationalAgent:
    def __init__(self):
        # Используем единообразно ключ "anamneza" (без ударения)
        self.long_term_memory = {
            "vek": None,
            "anamneza": None,
            "predpis": None,
            "user_data": None,
            "search_query": None
        }

    def update_memory(self, key, value):
        self.long_term_memory[key] = value

    def get_memory(self, key):
        return self.long_term_memory.get(key, None)

    def load_memory_from_history(self, chat_history: str):
        memory_match = re.search(r"\[MEMORY\](.*?)\[/MEMORY\]", chat_history, re.DOTALL)
        if memory_match:
            try:
                memory_data = json.loads(memory_match.group(1))
                self.long_term_memory.update(memory_data)
                logger.info(f"Nahraná pamäť z histórie: {self.long_term_memory}")
            except Exception as e:
                logger.error(f"Chyba pri načítaní pamäte: {e}")

    def parse_user_info(self, query: str):
        text_lower = query.lower()
        if re.search(r"\d+\s*(rok(ov|y)?|years?)", text_lower):
            self.update_memory("user_data", query)
        age_match = re.search(r"(\d{1,3})\s*(rok(ov|y)?|years?)", text_lower)
        if age_match:
            self.update_memory("vek", age_match.group(1))
        # Здесь проверяем ключевые слова без ударения
        if ("nemá" in text_lower or "nema" in text_lower) and ("chronické" in text_lower or "alerg" in text_lower):
            self.update_memory("anamneza", "Žiadne chronické ochorenia ani alergie")
        elif (("chronické" in text_lower or "alerg" in text_lower) and ("má" in text_lower or "ma" in text_lower)):
            self.update_memory("anamneza", "Má chronické ochorenie alebo alergie (nespecifikované)")
        if "voľnopredajný" in text_lower:
            self.update_memory("predpis", "volnopredajny")
        elif "na predpis" in text_lower:
            self.update_memory("predpis", "na predpis")

    def analyze_input(self, query: str) -> dict:
        self.parse_user_info(query)
        missing_info = {}
        if not self.get_memory("vek"):
            missing_info["vek"] = "Prosím, uveďte vek pacienta."
        if not self.get_memory("anamneza"):
            missing_info["anamneza"] = "Má pacient nejaké chronické ochorenia alebo alergie?"
        if not self.get_memory("predpis"):
            missing_info["predpis"] = "Ide o liek na predpis alebo voľnopredajný liek?"
        return missing_info

    def ask_follow_up(self, missing_info: dict) -> str:
        return " ".join(missing_info.values())

###############################################################################
# Главная функция process_query_with_mistral с объединенным поиском (векторным и текстовым)
###############################################################################
CHAT_HISTORY_ENDPOINT = "http://localhost:5000/api/chat_history_detail"

def process_query_with_mistral(query: str, chat_id: str, chat_context: str, k=10):
    logger.info("Processing query started.")

    # Загрузка истории чата, если она имеется
    chat_history = ""
    if chat_context:
        chat_history = chat_context
    elif chat_id:
        try:
            params = {"id": chat_id}
            r = requests.get(CHAT_HISTORY_ENDPOINT, params=params)
            if r.status_code == 200:
                data = r.json()
                chat_data = data.get("chat", "")
                if isinstance(chat_data, dict):
                    chat_history = chat_data.get("chat", "")
                else:
                    chat_history = chat_data or ""
                logger.info(f"História chatu načítaná pre chatId: {chat_id}")
            else:
                logger.warning(f"Nepodarilo sa načítať históriu (status {r.status_code}) pre chatId: {chat_id}")
        except Exception as e:
            logger.error(f"Chyba pri načítaní histórie: {e}")

    agent = ConversationalAgent()
    if chat_history:
        agent.load_memory_from_history(chat_history)

    existing_user_data = ""
    if chat_id:
        existing_user_data = get_user_data_from_db(chat_id)

    agent.parse_user_info(query)
    missing_info = agent.analyze_input(query)

    if missing_info:
        logger.info(f"Chýbajúce informácie: {missing_info}")
        combined_missing_text = " ".join(missing_info.values())
        if query.strip() not in combined_missing_text:
            if chat_id:
                update_payload = {"chatId": chat_id, "userData": query}
                try:
                    update_response = requests.post("http://localhost:5000/api/save_user_data", json=update_payload)
                    if update_response.status_code == 200:
                        logger.info("User data successfully updated via /api/save_user_data.")
                    else:
                        logger.warning(f"Failed to update user data: {update_response.text}")
                except Exception as e:
                    logger.error(f"Error when updating user_data: {e}")
        return {
            "best_answer": combined_missing_text,
            "model": "FollowUp (new chat)",
            "rating": 0,
            "explanation": "Additional data is required.",
            "patient_data": query
        }

    # Выполняем оба вида поиска (векторный и текстовый) независимо от типа запроса

    ### Векторный поиск
    vector_results = vectorstore.similarity_search(query, k=k)
    # Используем getattr для получения page_content, если оно есть, или metadata['text']
    vector_documents = [getattr(hit, 'page_content', None) or hit.metadata.get('text', '') for hit in vector_results]
    logger.info(f"Vector search in Elasticsearch: Najdených {len(vector_results)} dokumentov pre dopyt: '{query}'")
    for i, doc in enumerate(vector_documents, start=1):
        logger.info(f"Vector document {i}: {doc[:200]}")
    max_docs = 5
    # Без обрезания текста – используем весь найденный текст
    vector_docs = vector_documents[:max_docs]
    if vector_docs:
        vector_docs_joined = "\n".join(vector_docs)
        vector_prompt = (
            f"Na základe otázky: '{query}' a nasledujúcich informácií z dokumentov (použi tieto údaje pri generovaní odpovede):\n"
            f"{vector_docs_joined}\n\n"
            "Prosím, v odpovedi zahrň konkrétne informácie z týchto dokumentov a uveď odporúčania liekov s dávkovaním, "
            "ak sú takéto údaje dostupné. Odpoveď musí byť v slovenčine."
        )
        summary_small_vector = llm_small.generate_text(prompt=vector_prompt, max_tokens=700, temperature=0.7)
        summary_large_vector = llm_large.generate_text(prompt=vector_prompt, max_tokens=700, temperature=0.7)
        splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
        split_summary_small_vector = splitter.split_text(summary_small_vector)
        split_summary_large_vector = splitter.split_text(summary_large_vector)
        small_vector_eval = evaluate_complete_answer(query, " ".join(split_summary_small_vector))
        large_vector_eval = evaluate_complete_answer(query, " ".join(split_summary_large_vector))
    else:
        small_vector_eval = {"rating": 0, "explanation": "No results"}
        large_vector_eval = {"rating": 0, "explanation": "No results"}

    ### Текстовый поиск
    es_results = vectorstore.client.search(
        index=index_name,
        body={"size": k, "query": {"match": {"text": query}}}
    )
    text_documents = [hit['_source'].get('text', '') for hit in es_results['hits']['hits']]
    logger.info(f"Text search in Elasticsearch: Najdených {len(es_results['hits']['hits'])} dokumentov pre dopyt: '{query}'")
    for i, doc in enumerate(text_documents, start=1):
        logger.info(f"Text document {i}: {doc[:200]}")
    text_docs = text_documents[:max_docs]
    if text_docs:
        text_docs_joined = "\n".join(text_docs)
        text_prompt = (
            f"Na základe otázky: '{query}' a nasledujúcich informácií z dokumentov (použi tieto údaje pri generovaní odpovede):\n"
            f"{text_docs_joined}\n\n"
            "Prosím, v odpovedi zahrň konkrétne informácie z týchto dokumentov a uveď odporúčania liekov s dávkovaním, "
            "ak sú takéto údaje dostupné. Odpoveď musí byť v slovenčine."
        )
        summary_small_text = llm_small.generate_text(prompt=text_prompt, max_tokens=700, temperature=0.7)
        summary_large_text = llm_large.generate_text(prompt=text_prompt, max_tokens=700, temperature=0.7)
        split_summary_small_text = splitter.split_text(summary_small_text)
        split_summary_large_text = splitter.split_text(summary_large_text)
        small_text_eval = evaluate_complete_answer(query, " ".join(split_summary_small_text))
        large_text_eval = evaluate_complete_answer(query, " ".join(split_summary_large_text))
    else:
        small_text_eval = {"rating": 0, "explanation": "No results"}
        large_text_eval = {"rating": 0, "explanation": "No results"}

    ### Объединение результатов обоих поисков
    candidates = [
        {"eval": small_vector_eval, "summary": summary_small_vector, "model": "Mistral Small Vector"},
        {"eval": large_vector_eval, "summary": summary_large_vector, "model": "Mistral Large Vector"},
        {"eval": small_text_eval, "summary": summary_small_text, "model": "Mistral Small Text"},
        {"eval": large_text_eval, "summary": summary_large_text, "model": "Mistral Large Text"},
    ]
    best_result = max(candidates, key=lambda x: x["eval"]["rating"])
    logger.info(f"Best result from model {best_result['model']} with rating: {best_result['eval']['rating']}/10")

    # Выбор контекста для сохранения – предпочтительно текстовый, если он есть, иначе векторный
    if text_documents:
        best_context = text_documents[0]
    elif vector_documents:
        best_context = vector_documents[0]
    else:
        best_context = ""
    final_answer = translate_preserving_medicine_names(best_result["summary"])
    memory_json = json.dumps(agent.long_term_memory)
    memory_block = f"[MEMORY]{memory_json}[/MEMORY]"
    final_answer_with_memory = final_answer + "\n\n" + memory_block

    return {
        "best_answer": final_answer_with_memory,
        "model": best_result["model"],
        "rating": best_result["eval"]["rating"],
        "explanation": best_result["eval"]["explanation"],
        "retrieved_context": best_context
    }
