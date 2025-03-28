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

mistral_api_key = "hXDC4RBJk1qy5pOlrgr01GtOlmyCBaNs"
if not mistral_api_key:
    raise ValueError("Mistral API key not found in configuration.")

###############################################################################
# Простейшие заглушки для перевода
###############################################################################
def translate_to_slovak(text: str) -> str:
    return text

def translate_preserving_medicine_names(text: str) -> str:
    return text

###############################################################################
#       Funkcia pre vyhodnotenie úplnosti odpovede podľa kritérií              #
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
#             Validácia logiky odpovede voči pôvodnej otázke                #
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
        validated_answer = llm_small.generate_text(prompt=validation_prompt, max_tokens=500, temperature=0.5)
        logger.info(f"Validated answer: {validated_answer}")
        return validated_answer
    except Exception as e:
        logger.error(f"Error during answer validation: {e}")
        return answer



###############################################################################
# Функция формирования динамического промпта с учётом истории
###############################################################################
def build_dynamic_prompt(query: str, documents: list) -> str:
    # Spojí dokumenty do jedného textu
    documents_str = "\n".join(documents)
    # Vytvorí prompt, ktorý obsahuje otázku a inštrukcie pre generovanie odpovede
    prompt = (
        f"Otázka: '{query}'.\n"
        "Na základe nasledujúcich informácií o liekoch:\n"
        f"{documents_str}\n\n"
        "Analyzuj uvedenú otázku a zisti, či obsahuje dodatočné požiadavky okrem odporúčania liekov. "
        "Ak áno, v odpovedi najprv uveď odporúčané lieky – pre každý liek uveď jeho názov, stručné vysvetlenie a, ak je to relevantné, "
        "odporúčané dávkovanie alebo čas užívania, a potom v ďalšej časti poskytnú odpoveď na dodatočné požiadavky. "
        "Ak dodatočné požiadavky nie sú prítomné, uveď len odporúčanie liekov. "
        "Odpovedaj priamo a ľudským, priateľským tónom v číslovanom zozname, bez zbytočných úvodných fráz. "
        "Odpoveď musí byť v slovenčine. "
        "Prosím, odpovedaj v priateľskom, zdvorilom a profesionálnom tóne, bez akýchkoľvek agresívnych či drzých výrazov."
    )
    return prompt

###############################################################################
# Класс для вызова Mistral LLM
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
            except Exception as ex:
                logger.error(f"Error: {str(ex)}")
                raise ex
        raise Exception("Reached maximum number of retries for API request")

###############################################################################
# Инициализация Embeddings и Elasticsearch
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
# Функция классификации: vyhľadávanie vs. upresnenie
###############################################################################
def classify_query(query: str) -> str:
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
    if "vyhľadávanie" in classification:
        return "vyhľadávanie"
    elif "upresnenie" in classification:
        return "upresnenie"
    return "vyhľadávanie"  # fallback

###############################################################################
# Шаблон для upresnenia: модель возвращает либо FOUND_IN_HISTORY, либо NO_ANSWER_IN_HISTORY
###############################################################################
def build_upresnenie_prompt_no_history(chat_history: str, user_query: str) -> str:
    prompt = f"""
Ty si zdravotnícky expert. Máš k dispozícii históriu chatu a novú upresňujúcu otázku.

Ak v histórii chatu už existuje jasná odpoveď na túto upresňujúcu otázku, napíš:
"FOUND_IN_HISTORY: <ľudský vysvetľujúci text>"

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
# Функция извлечения последнего vyhľadávacieho dopytu из истории
###############################################################################
def extract_last_vyhladavacie_query(chat_history: str) -> str:
    lines = chat_history.splitlines()
    for line in reversed(lines):
        if line.startswith("User:"):
            return line[len("User:"):].strip()
    return ""

###############################################################################
# Класс агента для хранения údajov (vek, anamnéza, predpis)
###############################################################################
class ConversationalAgent:
    def __init__(self):
        self.long_term_memory = {
            "vek": None,
            "anamneza": None,
            "predpis": None
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
        age_match = re.search(r"(\d{1,3})\s*(rok(ov|y)?|years?)?", text_lower)
        if age_match and not self.get_memory("vek"):
            self.update_memory("vek", age_match.group(1))
        if (("nemá" in text_lower or "nema" in text_lower) and ("chronické" in text_lower or "alerg" in text_lower)):
            if not self.get_memory("anamneza"):
                self.update_memory("anamneza", "Žiadne chronické ochorenia ani alergie")
        elif (("chronické" in text_lower or "alerg" in text_lower) and ("má" in text_lower or "ma" in text_lower)):
            if not self.get_memory("anamneza"):
                self.update_memory("anamneza", "Má chronické ochorenie alebo alergie (nespecifikované)")
        if "voľnopredajný" in text_lower:
            if not self.get_memory("predpis"):
                self.update_memory("predpis", "volnopredajny")
        elif "na predpis" in text_lower:
            if not self.get_memory("predpis"):
                self.update_memory("predpis", "na predpis")
        else:
            if "predpis" in text_lower:
                if ("nie" in text_lower or "nemam" in text_lower or "nemám" in text_lower) and not self.get_memory("predpis"):
                    self.update_memory("predpis", "volnopredajny")
                elif not self.get_memory("predpis"):
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
# Основная функция process_query_with_mistral
###############################################################################
CHAT_HISTORY_ENDPOINT = "http://localhost:5000/api/chat_history_detail"

def process_query_with_mistral(query: str, chat_id: str, chat_context: str, k=10):
    logger.info("Processing query started.")

    # 1. Классификация
    qtype = classify_query(query)
    logger.info(f"Typ dopytu: {qtype}")
    logger.info(f"Chat context (snippet): {chat_context[:200]}...")

    # 2. Загрузка истории
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

    # 3. Инициализация агента и načítanie pamäti
    agent = ConversationalAgent()
    if chat_history:
        agent.load_memory_from_history(chat_history)

    # Если новый чат и недostatok údajov, požiadame o follow-up
    if not chat_history.strip():
        missing_info = agent.analyze_input(query)
        if missing_info:
            follow_up = agent.ask_follow_up(missing_info)
            logger.info(f"Chýbajúce informácie: {missing_info}")
            return {
                "best_answer": follow_up,
                "model": "FollowUp (nový chat)",
                "rating": 0,
                "explanation": "Získajte doplňujúce informácie."
            }

    # 4. Если upresnenie
    if qtype == "upresnenie":
        # Извлекаем последний vyhľadávací dopyt, если он есть
        last_query = extract_last_vyhladavacie_query(chat_history)
        combined_query = (last_query + " " + query).strip() if last_query else query

        # Формируем upresňujúci промпт
        upres_prompt = build_upresnenie_prompt_no_history(chat_history, combined_query)
        response_str = llm_small.generate_text(upres_prompt, max_tokens=800, temperature=0.5)
        normalized = response_str.strip()
        lower_norm = normalized.lower()
        logger.info(f"Upresnenie prompt response: {normalized}")

        # Если модель вернула FOUND_IN_HISTORY
        if re.match(r"(?i)^found_in_history:\s*", normalized):
            parts = re.split(r"(?i)^found_in_history:\s*", normalized, maxsplit=1)
            if len(parts) < 2:
                return {
                    "best_answer": normalized,
                    "model": "Upresnenie-ParseError",
                    "rating": 0,
                    "explanation": "Model nevrátil správny formát (FOUND_IN_HISTORY:)."
                }
            final_answer = parts[1].strip()
            return {
                "best_answer": final_answer,
                "model": "Upresnenie-FinalFromHistory",
                "rating": 10,
                "explanation": "Odpoveď bola nájdená v histórii."
            }
        # Если модель вернула NO_ANSWER_IN_HISTORY
        elif re.match(r"(?i)^no_answer_in_history:\s*", normalized):
            parts = re.split(r"(?i)^no_answer_in_history:\s*", normalized, maxsplit=1)
            if len(parts) < 2:
                return {
                    "best_answer": normalized,
                    "model": "Upresnenie-ParseError",
                    "rating": 0,
                    "explanation": "Model nevrátil správny formát (NO_ANSWER_IN_HISTORY:)."
                }
            search_query = parts[1].strip()
            logger.info(f"Vyhľadávací dopyt z upresnenia: {search_query}")

            # Выполняем поиск в Elasticsearch (как в obvyklom vyhľadávaní)
            es_res = vectorstore.client.search(
                index=index_name,
                body={
                    "size": k,
                    "query": {
                        "multi_match": {
                            "query": search_query,
                            "fields": ["text"]
                        }
                    }
                }
            )
            hits = es_res["hits"]["hits"]
            if not hits:
                return {
                    "best_answer": "Ľutujem, nenašli sa žiadne relevantné informácie.",
                    "model": "Upresnenie-NoResults",
                    "rating": 0,
                    "explanation": "No results from search."
                }
            docs_texts = [h["_source"]["text"] for h in hits[:5]]
            joined_docs = "\n".join(docs_texts)

            # Теперь генерируем итоговый ответ с использованием обеих model (small и large)
            final_prompt = (
                f"Otázka (upresnenie): {combined_query}\n\n"
                "Na základe týchto nájdených informácií:\n"
                f"{joined_docs}\n\n"
                "Vygeneruj odporúčanie liekov alebo vysvetlenie, ak je to relevantné."
            )
            # Генерируем ответы от small и large
            ans_small = llm_small.generate_text(final_prompt, max_tokens=800, temperature=0.7)
            ans_large = llm_large.generate_text(final_prompt, max_tokens=800, temperature=0.7)
            # Валидируем ответы
            val_small = validate_answer_logic(combined_query, ans_small)
            val_large = validate_answer_logic(combined_query, ans_large)
            # Оцениваем
            eval_small = evaluate_complete_answer(combined_query, val_small)
            eval_large = evaluate_complete_answer(combined_query, val_large)
            candidates = [
                {"summary": val_small, "eval": eval_small, "model": "Mistral Small"},
                {"summary": val_large, "eval": eval_large, "model": "Mistral Large"},
            ]
            best = max(candidates, key=lambda x: x["eval"]["rating"])
            logger.info(f"Odpoveď od modelu {best['model']} má rating: {best['eval']['rating']}/10")
            final_answer = translate_preserving_medicine_names(best["summary"])
            return {
                "best_answer": final_answer,
                "model": best["model"],
                "rating": best["eval"]["rating"],
                "explanation": best["eval"]["explanation"]
            }
        else:
            return {
                "best_answer": response_str,
                "model": "Upresnenie-ParseError",
                "rating": 0,
                "explanation": "Model nevrátil očakávaný formát (FOUND_IN_HISTORY alebo NO_ANSWER_IN_HISTORY)."
            }

    # 5. Если to je obyčajné vyhľadávanie
    vector_results = vectorstore.similarity_search(query, k=k)
    max_docs = 5
    max_len = 1000
    vector_docs = [hit.metadata.get("text", "")[:max_len] for hit in vector_results[:max_docs]]
    if not vector_docs:
        return {
            "best_answer": "Ľutujem, nenašli sa žiadne relevantné informácie.",
            "model": "Vyhladavanie-NoDocs",
            "rating": 0,
            "explanation": "No results"
        }
    joined_docs = "\n".join(vector_docs)
    final_prompt = (
        f"Otázka: {query}\n\n"
        "Na základe týchto informácií:\n"
        f"{joined_docs}\n\n"
        "Vygeneruj odporúčanie liekov alebo vysvetlenie, ak je to relevantné."
    )
    answer = llm_small.generate_text(final_prompt, max_tokens=800, temperature=0.7)
    return {
        "best_answer": answer,
        "model": "Vyhladavanie-Final",
        "rating": 9,
        "explanation": "Vyhľadávacia cesta"
    }
