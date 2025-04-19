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

# Získanie konfiguračného súboru
config_file_path = "config.json"
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)

# Získanie Mistral API kľúča
mistral_api_key = "hXDC4RBJk1qy5pOlrgr01GtOlmyCBaNs"
if not mistral_api_key:
    raise ValueError("Mistral API key not found in configuration.")


###############################################################################
# Funkcie pre preklad (stub verzie)
###############################################################################
def translate_to_slovak(text: str) -> str:
    return text


def translate_preserving_medicine_names(text: str) -> str:
    return text


###############################################################################
# Funkcia na generovanie podrobného opisu hodnotenia cez Mistral
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
# Funkcia na hodnotenie úplnosti odpovede
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
# Funkcia pre validáciu logiky odpovede (aktualizovaná verzia)
###############################################################################
def validate_answer_logic(query: str, answer: str) -> str:
    validation_prompt = (
        f"Otázka: '{query}'\n"
        f"Odpoveď: '{answer}'\n\n"
        "Vyhodnoť, či odpoveď jednoznačne reaguje na uvedenú otázku a obsahuje všetky dôležité informácie. "
        "Ak odpoveď nereaguje presne na otázku, vytvor novú odpoveď, ktorá jasne a logicky reaguje na tento dotaz. "
        "Ak je odpoveď správna, začni svoju odpoveď textom 'OK:'; následne uveď potvrdenú odpoveď. "
        "Odpovedz len finálnou odpoveďou bez ďalších komentárov."
    )
    try:
        validated_answer = llm_small.generate_text(prompt=validation_prompt, max_tokens=800, temperature=0.5)
        logger.info(f"Validated answer (first 200 chars): {validated_answer[:200]}")
        if validated_answer.strip().lower().startswith("ok:"):
            return validated_answer.split("OK:", 1)[1].strip()
        else:
            return validated_answer.strip()
    except Exception as e:
        logger.error(f"Error during answer validation: {e}")
        return answer


###############################################################################
# Funkcia pre logovanie hodnotení do súboru
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
# Funkcia pre vytvorenie dynamického prompt-u z informácií o dokumentoch
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
        "Odpoveď musí byť v slovenčine."
    )
    return prompt


###############################################################################
# Funkcia pre získavanie user_data z databázy cez endpoint /api/get_user_data
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
# Trieda pre prácu s Mistral LLM cez API
###############################################################################
class CustomMistralLLM:
    def __init__(self, api_key: str, endpoint_url: str, model_name: str):
        self.api_key = api_key
        self.endpoint_url = endpoint_url
        self.model_name = model_name

    def generate_text(self, prompt: str, max_tokens=812, temperature=0.7, retries=3, delay=2):
        # Pre mistral-large, ak je prompt príliš dlhý, skracujeme ho (napr. na 4000 znakov)
        if self.model_name == "mistral-large-latest" and len(prompt) > 4000:
            logger.warning(f"Prompt dlhší ako 4000 znakov, skracujem ho.")
            prompt = prompt[:4000]
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
# Inicializácia embeddingov a Elasticsearch
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
# Inicializácia LLM small & large
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
# Funkcia na klasifikáciu dopytu: vyhladavanie vs. upresnenie alebo update informácií
###############################################################################
def classify_query(query: str, chat_history: str = "") -> str:
    # Ak v histórii sa nachádza výzva na zadanie údajov a query obsahuje číslice (napr. vek),
    # považujeme to za odpoveď na doplnenie informácií.
    if "Prosím, uveďte vek pacienta" in chat_history and re.search(r"\d+\s*(rok(ov|y)?|years?)", query.lower()):
        return "update"
    if not chat_history.strip():
        return "vyhladavanie"
    prompt = (
        "Ty si zdravotnícky expert, ktorý analyzuje otázky používateľov. "
        "Analyzuj nasledujúci dopyt a urči, či ide o dopyt na vyhľadanie liekov alebo "
        "o upresnenie/doplnenie už poskytnutej odpovede.\n"
        "Ak dopyt obsahuje výrazy ako 'čo pit', 'aké lieky', 'odporuč liek', 'hľadám liek', "
        "odpovedaj slovom 'vyhľadávanie'.\n"
        "Ak dopyt slúži na upresnenie, napríklad obsahuje výrazy ako 'a nie na predpis', 'upresni', 'este raz', "
        "odpovedaj slovom 'upresnenie'.\n"
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
# Šablóna prompt-u pre upresnenie (bez histórie)
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
# Funkcia pre extrakciu posledného vyhľadávacieho dopytu z histórie
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
# Trieda agenta pre ukladanie údajov: vek, anamneza, predpis, user_data, search_query
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
            missing_info["anamneza"] = "Má pacient nejaké chronické ochorenia alebo alergie?"
        if not self.get_memory("predpis"):
            missing_info["predpis"] = "Ide o liek na predpis alebo voľnopredajný liek?"
        return missing_info

    def ask_follow_up(self, missing_info: dict) -> str:
        return " ".join(missing_info.values())


###############################################################################
# Hlavná funkcia process_query_with_mistral, ktorá vykonáva obidva druhy vyhľadávania
###############################################################################
CHAT_HISTORY_ENDPOINT = "http://localhost:5000/api/chat_history_detail"


def process_query_with_mistral(query: str, chat_id: str, chat_context: str, k=10):
    """
    Processes a query by generating two separate responses with Mistral:
    1) A response without using Elasticsearch documents (docless)
    2) A response with context from Elasticsearch documents (doc-based)
    Returns both as a single combined answer.
    """
    logger.info("Processing query started.")

    # Load chat history
    chat_history = chat_context or ""
    if not chat_history and chat_id:
        try:
            r = requests.get(CHAT_HISTORY_ENDPOINT, params={"id": chat_id})
            if r.status_code == 200:
                chat_data = r.json().get("chat", "")
                chat_history = chat_data if isinstance(chat_data, str) else chat_data.get("chat", "")
                logger.info(f"Loaded chat history for chatId {chat_id}.")
        except Exception as e:
            logger.error(f"Error loading chat history: {e}")

    # Initialize agent and memory
    agent = ConversationalAgent()
    if chat_history:
        agent.load_memory_from_history(chat_history)
    if not chat_history.strip():
        agent.update_memory("search_query", query)

    # Parse user info and check for missing data
    agent.parse_user_info(query)
    missing_info = agent.analyze_input(query)
    if missing_info:
        combined_missing = " ".join(missing_info.values())
        return {
            "best_answer": combined_missing,
            "model": "FollowUp (new chat)",
            "rating": 0,
            "explanation": "Additional data required.",
            "patient_data": query
        }

    # Determine query string for LLM
    qtype = classify_query(query, chat_history)
    original_search = agent.long_term_memory.get("search_query")
    if qtype == "update":
        query_to_use = original_search or extract_last_vyhladavacie_query(chat_history)
    else:
        query_to_use = query

    # 1) Generate docless responses
    docless_prompt = (
        f"Otázka: {query_to_use}\n"
        "Generuj odpoveď bez využitia externých dokumentov."
    )
    # Small and large
    dless_small = llm_small.generate_text(docless_prompt, max_tokens=1200, temperature=0.7)
    dless_large = llm_large.generate_text(docless_prompt, max_tokens=1200, temperature=0.7)
    # Validate and evaluate
    vless_small = validate_answer_logic(query_to_use, dless_small)
    vless_large = validate_answer_logic(query_to_use, dless_large)
    oless_small = evaluate_complete_answer(query_to_use, vless_small)
    oless_large = evaluate_complete_answer(query_to_use, vless_large)
    # Choose best docless
    best_docless = max([
        {"model": "Docless Small", "summary": vless_small, "eval": oless_small},
        {"model": "Docless Large", "summary": vless_large, "eval": oless_large}
    ], key=lambda x: x["eval"]["rating"])

    # 2) Perform Elasticsearch searches (vector + text)
    vector_results = vectorstore.similarity_search(query_to_use, k=k)
    vector_docs = [getattr(hit, 'page_content', None) or hit.metadata.get('text', '') for hit in vector_results[:5]]
    es_hits = vectorstore.client.search(
        index=index_name,
        body={"size": k, "query": {"match": {"text": query_to_use}}}
    )
    text_docs = [h['_source'].get('text', '') for h in es_hits['hits']['hits'][:5]]

    # Build combined prompt with docs
    joined_vector = "\n".join(vector_docs)
    joined_text = "\n".join(text_docs)
    doc_prompt = (
        f"Otázka: {query_to_use}\n\n"
        "Informácie z vektorového vyhľadávania:\n"
        f"{joined_vector}\n\n"
        "Informácie z textového vyhľadávania:\n"
        f"{joined_text}\n\n"
        "Na základe týchto informácií vygeneruj odpoveď, ktorá jasne a logicky reaguje na uvedenú otázku."
    )
    if len(doc_prompt) > 4000:
        doc_prompt = doc_prompt[:4000]

    # Generate doc-based responses
    db_small = llm_small.generate_text(doc_prompt, max_tokens=1200, temperature=0.7)
    db_large = llm_large.generate_text(doc_prompt, max_tokens=1200, temperature=0.7)
    vdb_small = validate_answer_logic(query_to_use, db_small)
    vdb_large = validate_answer_logic(query_to_use, db_large)
    odb_small = evaluate_complete_answer(query_to_use, vdb_small)
    odb_large = evaluate_complete_answer(query_to_use, vdb_large)
    # Choose best doc-based
    best_docbased = max([
        {"model": "Doc-Based Small", "summary": vdb_small, "eval": odb_small},
        {"model": "Doc-Based Large", "summary": vdb_large, "eval": odb_large}
    ], key=lambda x: x["eval"]["rating"])

    # Combine both answers
    combined_answer = (
        f"**Odpoveď bez dokumentov ({best_docless['model']}):**\n{best_docless['summary']}\n\n"
        f"**Odpoveď s dokumentmi ({best_docbased['model']}):**\n{best_docbased['summary']}"
    )

    # Attach memory block
    memory_block = f"[MEMORY]{json.dumps(agent.long_term_memory)}[/MEMORY]"
    final = combined_answer + "\n\n" + memory_block

    # Return unified result
    return {
        "best_answer": final,
        "model": f"{best_docless['model']} + {best_docbased['model']}",
        "rating": max(best_docless['eval']["rating"], best_docbased['eval']["rating"]),
        "explanation": "Combined docless and doc-based responses"
    }

# Koniec kódu
