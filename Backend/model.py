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
        "Na základe nasledujúcich informácií o liekoch:\n"
        f"{documents_str}\n\n"
        "Analyzuj uvedenú otázku a zisti, či obsahuje dodatočné požiadavky okrem odporúčania liekov. "
        "Ak áno, v odpovedi najprv uveď odporúčané lieky – pre každý liek uveď jeho názov, stručné vysvetlenie a, ak je to relevantné, "
        "odporúčané dávkovanie alebo čas užívania, a potom v ďalšej časti poskytn ú odpoveď na dodatočné požiadavky. "
        "Odpovedaj priamo a ľudským, priateľským tónom v číslovanom zozname, bez zbytočných úvodných fráz. "
        "Odpoveď musí byť v slovenčine. "
        "Prosím, odpovedaj v priateľskom, zdvorilom a profesionálnom tóne, bez akýchkoľvek agresívnych či drzých výrazov."
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
# Класс для работы с Mistral LLM через API (единственная версия)
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
# Инициализация LLM small & large
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
# Функция классификации запроса: vyhladavanie vs. upresnenie
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
    if "vyhládzanie" in classification or "vyhľadávanie" in classification:
        return "vyhladavanie"
    elif "upresnenie" in classification:
        return "upresnenie"
    return "vyhladavanie"


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
# Класс агента для хранения данных: vek, anamneza, predpis, user_data, search_query
###############################################################################
class ConversationalAgent:
    def __init__(self):
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
            missing_info["anamnéza"] = "Má pacient nejaké chronické ochorenia alebo alergie?"
        if not self.get_memory("predpis"):
            missing_info["predpis"] = "Ide o liek na predpis alebo voľnopredajný liek?"
        return missing_info

    def ask_follow_up(self, missing_info: dict) -> str:
        return " ".join(missing_info.values())


###############################################################################
# Главная функция process_query_with_mistral с обновленной логикой и логированием
###############################################################################
CHAT_HISTORY_ENDPOINT = "http://localhost:5000/api/chat_history_detail"


def process_query_with_mistral(query: str, chat_id: str, chat_context: str, k=10):
    logger.info("Processing query started.")

    # Получение истории чата
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

    # Инициализация агента
    agent = ConversationalAgent()
    if chat_history:
        agent.load_memory_from_history(chat_history)

    existing_user_data = ""
    if chat_id:
        existing_user_data = get_user_data_from_db(chat_id)

    agent.parse_user_info(query)
    missing_info = agent.analyze_input(query)

    if not existing_user_data and missing_info:
        logger.info(f"Chýbajúce informácie: {missing_info}")
        combined_missing_text = " ".join(missing_info.values())
        if query.strip() not in combined_missing_text:
            if chat_id:
                update_payload = {"chatId": chat_id, "userData": query}
                try:
                    update_response = requests.post("http://localhost:5000/api/save_user_data", json=update_payload)
                    if update_response.status_code == 200:
                        logger.info("User data was successfully updated via endpoint /api/save_user_data.")
                    else:
                        logger.warning(f"Failed to update the data: {update_response.text}")
                except Exception as e:
                    logger.error(f"Error when updating user_data via endpoint: {e}")
        return {
            "best_answer": combined_missing_text,
            "model": "FollowUp (new chat)",
            "rating": 0,
            "explanation": "Additional data pre pokračovanie is required.",
            "patient_data": query
        }

    qtype = classify_query(query, chat_history)
    logger.info(f"Typ dopytu: {qtype}")
    logger.info(f"Chat context (snippet): {chat_history[:200]}...")

    # Если тип запроса "upresnenie", используем только векторный поиск с объединением запроса
    if qtype == "upresnenie":
        original_search = agent.long_term_memory.get("search_query")
        if not original_search:
            original_search = extract_last_vyhladavacie_query(chat_history)
        if original_search is None:
            original_search = ""
        combined_query = (original_search + " " + query).strip()
        user_data_db = get_user_data_from_db(chat_id)
        if user_data_db:
            combined_query += " Udaje cloveka: " + user_data_db
        logger.info(f"Combined query for search: {combined_query}")

        upres_prompt = build_upresnenie_prompt_no_history(chat_history, combined_query)
        response_str = llm_small.generate_text(upres_prompt, max_tokens=1200, temperature=0.5)
        normalized = response_str.strip()
        logger.info(f"Upresnenie prompt response: {normalized}")

        if re.match(r"(?i)^found_in_history:\s*", normalized):
            logger.info("Zistený FOUND_IN_HISTORY – vykonávame vyhľadávanie s kombinovaným dopytom.")
        elif re.match(r"(?i)^no_answer_in_history:\s*", normalized):
            parts = re.split(r"(?i)^no_answer_in_history:\s*", normalized, maxsplit=1)
            if len(parts) >= 2:
                combined_query = parts[1].strip()
                logger.info(f"Upravený vyhľadávací dopyт z NO_ANSWER_IN_HISTORY: {combined_query}")

        # Векторный поиск для upresnenia с использованием getattr для извлечения текста
        vector_results = vectorstore.similarity_search(combined_query, k=k)
        max_docs = 5
        max_len = 1000
        vector_docs = [
            getattr(hit, 'page_content', None) or hit.metadata.get('text', '')[:max_len]
            for hit in vector_results[:max_docs]
        ]
        if not vector_docs:
            return {
                "best_answer": "Ľutujem, nenašli sa žiadne relevantné informácie.",
                "model": "Upresnenie-NoResults",
                "rating": 0,
                "explanation": "No results from search."
            }
        joined_docs = "\n".join(vector_docs)
        final_prompt = (
            f"Otázka: {combined_query}\n\n"
            "Na základe týchto informácií:\n"
            f"{joined_docs}\n\n"
            "Vygeneruj odporúčanie liekov alebo vysvetlenie, ak je to relevantné.\n"
            "Prosím, odpovedaj stručne a dostatočne, bez nadmernej dĺžky."
        )
        ans_small = llm_small.generate_text(final_prompt, max_tokens=1200, temperature=0.7)
        ans_large = llm_large.generate_text(final_prompt, max_tokens=1200, temperature=0.7)
        val_small = validate_answer_logic(combined_query, ans_small)
        val_large = validate_answer_logic(combined_query, ans_large)
        eval_small = evaluate_complete_answer(combined_query, val_small)
        eval_large = evaluate_complete_answer(combined_query, val_large)
        candidates = [
            {"model": "Mistral Small", "summary": val_small, "eval": eval_small},
            {"model": "Mistral Large", "summary": val_large, "eval": eval_large},
        ]
        for candidate in candidates:
            detailed_desc = generate_detailed_description(combined_query, candidate["summary"],
                                                          candidate["eval"]["rating"])
            log_evaluation_to_file(candidate["model"], "vector", candidate["eval"]["rating"], detailed_desc,
                                   candidate["summary"])
        best = max(candidates, key=lambda x: x["eval"]["rating"])
        logger.info(f"Odpoveď od modelu {best['model']} má rating: {best['eval']['rating']}/10")
        final_answer = translate_preserving_medicine_names(best["summary"])
        memory_json = json.dumps(agent.long_term_memory)
        memory_block = f"[MEMORY]{memory_json}[/MEMORY]"
        final_answer_with_memory = final_answer + "\n\n"
        return {
            "best_answer": final_answer_with_memory,
            "model": best["model"],
            "rating": best["eval"]["rating"],
            "explanation": best["eval"]["explanation"]
        }

    # Для запроса типа "vyhladavanie" (текстовый запрос) выполняем оба поиска: векторный и текстовый
    # Векторный поиск:
    vector_results = vectorstore.similarity_search(query, k=k)
    max_docs = 5
    max_len = 1000
    vector_docs = [
        getattr(hit, 'page_content', None) or hit.metadata.get('text', '')[:max_len]
        for hit in vector_results[:max_docs]
    ]
    logger.info(f"Vector search in Elasticsearch: Найдено {len(vector_results)} документов для запроса: '{query}'")
    for i, doc in enumerate(vector_docs, start=1):
        logger.info(f"Векторный документ {i}: {doc[:200]}")  # выводим первые 200 символов

    # Текстовый поиск:
    es_results = vectorstore.client.search(
        index=index_name,
        body={"size": k, "query": {"match": {"text": query}}}
    )
    text_docs = [hit['_source'].get('text', "") for hit in es_results['hits']['hits']]
    text_docs = [doc[:max_len] for doc in text_docs[:max_docs]]
    num_found = len(es_results['hits']['hits'])
    logger.info(f"Text search in Elasticsearch: Найдено {num_found} документов для запроса: '{query}'")
    for i, doc in enumerate(text_docs, start=1):
        logger.info(f"Текстовый документ {i}: {doc[:200]}")

    if not vector_docs and not text_docs:
        return {
            "best_answer": "Ľutujem, nenašli sa žiadne relevantné informácie.",
            "model": "Vyhladavanie-NoDocs",
            "rating": 0,
            "explanation": "No results"
        }

    # Генерация ответов по обоим вариантам поиска
    # Для векторного поиска:
    joined_vector = "\n".join(vector_docs)
    final_prompt_vector = (
        f"Otázka: {query}\n\n"
        "Na základe týchto informácií (vector search):\n"
        f"{joined_vector}\n\n"
        "Vygeneruj odporúčanie liekov alebo vysvetlenie, ak je to relevantné.\n"
        "Prosím, odpovedaj stručne a dostatočne, bez nadmernej dĺžky."
    )
    ans_vector_small = llm_small.generate_text(final_prompt_vector, max_tokens=1200, temperature=0.7)
    ans_vector_large = llm_large.generate_text(final_prompt_vector, max_tokens=1200, temperature=0.7)
    val_vector_small = validate_answer_logic(query, ans_vector_small)
    val_vector_large = validate_answer_logic(query, ans_vector_large)
    eval_vector_small = evaluate_complete_answer(query, val_vector_small)
    eval_vector_large = evaluate_complete_answer(query, val_vector_large)
    candidate_vector_small = {"model": "Mistral Small Vector", "summary": val_vector_small, "eval": eval_vector_small}
    candidate_vector_large = {"model": "Mistral Large Vector", "summary": val_vector_large, "eval": eval_vector_large}

    # Для текстового поиска:
    joined_text = "\n".join(text_docs)
    final_prompt_text = (
        f"Otázka: {query}\n\n"
        "Na základe týchto informácií (text search):\n"
        f"{joined_text}\n\n"
        "Vygeneruj odporúčanie liekov alebo vysvetlenie, ak je to relevantné.\n"
        "Prosím, odpovedaj stručne a dostatočne, bez nadmernej dĺžky."
    )
    ans_text_small = llm_small.generate_text(final_prompt_text, max_tokens=1200, temperature=0.7)
    ans_text_large = llm_large.generate_text(final_prompt_text, max_tokens=1200, temperature=0.7)
    val_text_small = validate_answer_logic(query, ans_text_small)
    val_text_large = validate_answer_logic(query, ans_text_large)
    eval_text_small = evaluate_complete_answer(query, val_text_small)
    eval_text_large = evaluate_complete_answer(query, val_text_large)
    candidate_text_small = {"model": "Mistral Small Text", "summary": val_text_small, "eval": eval_text_small}
    candidate_text_large = {"model": "Mistral Large Text", "summary": val_text_large, "eval": eval_text_large}

    # Сравнение всех кандидатов (из векторного и текстового поиска)
    all_candidates = [
        candidate_vector_small,
        candidate_vector_large,
        candidate_text_small,
        candidate_text_large
    ]
    best_candidate = max(all_candidates, key=lambda x: x["eval"]["rating"])
    logger.info(f"Odpoveď od modelu {best_candidate['model']} má rating: {best_candidate['eval']['rating']}/10")
    final_answer = translate_preserving_medicine_names(best_candidate["summary"])

    # Выбор контекста для сохранения (первые найденные текстовые документы имеют приоритет)
    if text_docs:
        best_context = text_docs[0]
    elif vector_docs:
        best_context = vector_docs[0]
    else:
        best_context = ""

    memory_json = json.dumps(agent.long_term_memory)
    memory_block = f"[MEMORY]{memory_json}[/MEMORY]"
    final_answer_with_memory = final_answer + "\n\n"

    return {
        "best_answer": final_answer_with_memory,
        "model": best_candidate["model"],
        "rating": best_candidate["eval"]["rating"],
        "explanation": best_candidate["eval"]["explanation"],
        "retrieved_context": best_context
    }
