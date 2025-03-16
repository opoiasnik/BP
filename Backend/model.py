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

# Načítanie konfiguračného súboru
config_file_path = "config.json"
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)

mistral_api_key = "hXDC4RBJk1qy5pOlrgr01GtOlmyCBaNs"
if not mistral_api_key:
    raise ValueError("Mistral API key not found in configuration.")


###############################################################################
#            Preklad celej odpovede do slovenčiny (dočasne zavreté)           #
###############################################################################
def translate_to_slovak(text: str) -> str:
    return text


###############################################################################
#   Funkcia pre preklad popisu lieku so zachovaním názvu (do dvojbodky)      #
###############################################################################
def translate_preserving_medicine_names(text: str) -> str:
    return text


###############################################################################
#        Formovanie dynamického promptu pre generovanie odpovede              #
###############################################################################
def build_dynamic_prompt(query: str, documents: list) -> str:
    documents_str = "\n".join(documents)
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
# Funkcia pre klasifikáciu dopytu (vyhľadávanie vs. upresnenie) – na slovenčine
###############################################################################
def classify_query(query: str) -> str:
    prompt = (
        "Ty si zdravotnícky expert, ktorý analyzuje otázky používateľov. "
        "Analyzuj nasledujúci dopyt a urči, či ide o dopyt na vyhľadanie liekov alebo o upresnenie/doplnenie už poskytnutej odpovede.\n"
        "Ak dopyt obsahuje výrazy ako 'čo pit', 'aké lieky', 'odporuč liek', 'hľadám liek', odpovedaj slovom 'vyhľadávanie'.\n"
        "Ak dopyt slúži na upresnenie, napríklad obsahuje výrazy ako 'a nie na predpis', 'upresni', 'este raz', odpovedaj slovom 'upresnenie'.\n"
        f"Dopyt: \"{query}\""
    )
    classification = llm_small.generate_text(prompt=prompt, max_tokens=20, temperature=0.3)
    classification = classification.strip().lower()
    logger.info(f"Klasifikácia dopytu: {classification}")
    if "vyhľadávanie" in classification:
        return "vyhľadávanie"
    elif "upresnenie" in classification:
        return "upresnenie"
    return "vyhľadávanie"  # Predvolená možnosť


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
#         Implementácia agenta s dlhodobou pamäťou a analýzou vstupu          #
###############################################################################
class ConversationalAgent:
    def __init__(self):
        # Základná dlhodobá pamäť – kľúče nastavíme podľa potrieb
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
        """
        Ak v histórii chatu existuje blok s uloženou pamäťou vo formáte:
        [MEMORY]{"vek": "25", "anamneza": "...", "predpis": "..."}[/MEMORY]
        tak sa táto pamäť načíta.
        """
        memory_match = re.search(r"\[MEMORY\](.*?)\[/MEMORY\]", chat_history, re.DOTALL)
        if memory_match:
            try:
                memory_data = json.loads(memory_match.group(1))
                self.long_term_memory.update(memory_data)
                logger.info(f"Nahraná pamäť z histórie: {self.long_term_memory}")
            except Exception as e:
                logger.error(f"Chyba pri načítaní pamäte z histórie: {e}")

    def parse_user_info(self, query: str):
        """
        Dynamický parsing informácií z dopytu – hľadáme základné informácie:
        vek, anamnézu a informáciu o predpise.
        """
        text_lower = query.lower()
        # 1) Vek – hľadáme číslo (napr. "20 rokov")
        age_match = re.search(r"(\d{1,3})\s*(rok(ov|y)?|years?)?", text_lower)
        if age_match and not self.get_memory("vek"):
            self.update_memory("vek", age_match.group(1))
        # 2) Anamnéza – zisťujeme informácie o chronických ochoreniach či alergiách
        if (("nemá" in text_lower or "nema" in text_lower) and ("chronické" in text_lower or "alerg" in text_lower)):
            if not self.get_memory("anamneza"):
                self.update_memory("anamneza", "Žiadne chronické ochorenia ani alergie")
        elif (("chronické" in text_lower or "alerg" in text_lower) and ("má" in text_lower or "ma" in text_lower)):
            if not self.get_memory("anamneza"):
                self.update_memory("anamneza", "Má chronické ochorenie alebo alergie (nespecifikované)")
        # 3) Predpis – zisťujeme, či je liek na predpis alebo voľnopredajný
        if "voľnopredajný" in text_lower:
            if not self.get_memory("predpis"):
                self.update_memory("predpis", "volnopredajny")
        elif "na predpis" in text_lower:
            if not self.get_memory("predpis"):
                self.update_memory("predpis", "na predpis")
        else:
            if "predpis" in text_lower:
                if ("nie" in text_lower or "nemam" in text_lower or "nemám" in text_lower) and not self.get_memory(
                        "predpis"):
                    self.update_memory("predpis", "volnopredajny")
                elif not self.get_memory("predpis"):
                    self.update_memory("predpis", "na predpis")

    def analyze_input(self, query: str) -> dict:
        # Extrahujeme informácie z aktuálneho dopytu
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
        questions = list(missing_info.values())
        return " ".join(questions)


###############################################################################
#           Hlavná funkcia: process_query_with_mistral (Slovak prompt)       #
###############################################################################

# URL nášho endpointu pre získanie detailov chatu
CHAT_HISTORY_ENDPOINT = "http://localhost:5000/api/chat_history_detail"


def process_query_with_mistral(query, chat_id=None, k=10):
    logger.info("Processing query started.")

    # Najprv klasifikujeme dopyt
    query_type = classify_query(query)
    logger.info(f"Typ dopytu: {query_type}")

    chat_history = ""
    # Ak je chat_id zadané, vykonáme HTTP GET request na náš endpoint pre získanie detailov chatu
    if chat_id:
        try:
            params = {"id": chat_id}
            r = requests.get(CHAT_HISTORY_ENDPOINT, params=params)
            if r.status_code == 200:
                data = r.json()
                # Očakávame, že endpoint vráti slovník s kľúčom "chat".
                chat_data = data.get("chat", "")
                if isinstance(chat_data, dict):
                    chat_history = chat_data.get("chat", "")
                else:
                    chat_history = chat_data or ""
                logger.info(f"História chatu bola načítaná z endpointu pre chatId: {chat_id}")
            else:
                logger.warning(
                    f"Nepodarilo sa načítať históriu chatu (status code: {r.status_code}) pre chatId: {chat_id}")
        except Exception as e:
            logger.error(f"Chyba pri načítaní histórie chatu cez endpoint: {e}")

    # Inicializujeme agenta a ak máme históriu, obnovíme z nej pamäť
    agent = ConversationalAgent()
    if chat_history:
        agent.load_memory_from_history(chat_history)

    # Ak ide o upresnenie, analyzujeme históriu a vygenerujeme nový, doplnený odpoveď
    if query_type == "upresnenie" and chat_history:
        logger.info("Upresnenie dopytu – analyzujem históriu a generujem upresnenú odpoveď.")
        # Vytvoríme prompt, ktorý poskytne modelu kontext z histórie a nový dopyt
        upresnenie_prompt = (
            "Ty si zdravotnícky expert, ktorý odpovedá výlučne priateľským, zdvorilým a profesionálnym tónom bez akýchkoľvek pozdravov alebo zbytočných úvodných fráz. "
            "Na základe nasledujúcej histórie chatu a nového dopytu vytvor stručnú, ale ucelenú odpoveď, ktorá doplní alebo upresní už poskytnuté informácie.\n\n"
            "História chatu:\n"
            f"{chat_history}\n\n"
            "Nový dopyt:\n"
            f"{query}\n\n"
            "Vygeneruj odpoveď, ktorá obsahuje všetky relevantné informácie."
        )

        # Zvýšime max_tokens, aby sme získali rozsiahlejší text
        upresnená_odpoveď = llm_small.generate_text(prompt=upresnenie_prompt, max_tokens=1500, temperature=0.5)
        # Pripojíme blok pamäte

        final_answer = upresnená_odpoveď
        return {
            "best_answer": final_answer,
            "model": "Upresnenie based",
            "rating": 10,
            "explanation": "Odpoveď vygenerovaná na základe analýzy histórie a upresnenia dopytu."
        }

    # Pokračujeme v prípade vyhľadávania
    missing_info = agent.analyze_input(query)
    if missing_info:
        follow_up_question = agent.ask_follow_up(missing_info)
        logger.info(f"Chýbajúce informácie: {missing_info}")
        return {
            "best_answer": follow_up_question,
            "model": "Follow-up required",
            "rating": 0,
            "explanation": "Získajte doplňujúce informácie pre presnejšiu odpoveď."
        }

    try:
        # --- Vector search ---
        vector_results = vectorstore.similarity_search(query, k=k)
        vector_documents = [hit.metadata.get('text', '') for hit in vector_results]
        max_docs = 5
        max_doc_length = 1000
        vector_documents = [doc[:max_doc_length] for doc in vector_documents[:max_docs]]
        if vector_documents:
            vector_prompt = build_dynamic_prompt(query, vector_documents)
            summary_small_vector = llm_small.generate_text(prompt=vector_prompt, max_tokens=1200, temperature=0.7)
            summary_large_vector = llm_large.generate_text(prompt=vector_prompt, max_tokens=1200, temperature=0.7)
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
            eval_small_text = evaluate_complete_answer(query, summary_small_text)
            eval_large_text = evaluate_complete_answer(query, summary_large_text)
        else:
            eval_small_text = {"rating": 0, "explanation": "No results"}
            eval_large_text = {"rating": 0, "explanation": "No results"}
            summary_small_text = ""
            summary_large_text = ""

        # Výber najlepšieho výsledku
        all_results = [
            {"eval": eval_small_vector, "summary": summary_small_vector, "model": "Mistral Small Vector"},
            {"eval": eval_large_vector, "summary": summary_large_vector, "model": "Mistral Large Vector"},
            {"eval": eval_small_text, "summary": summary_small_text, "model": "Mistral Small Text"},
            {"eval": eval_large_text, "summary": summary_large_text, "model": "Mistral Large Text"},
        ]
        best_result = max(all_results, key=lambda x: x["eval"]["rating"])
        logger.info(f"Najlepší výsledok z modelu {best_result['model']} s hodnotením {best_result['eval']['rating']}.")

        # Validácia logiky odpovede
        validated_answer = validate_answer_logic(query, best_result["summary"])
        polished_answer = translate_preserving_medicine_names(validated_answer)

        # Pripojíme blok s pamäťou na konci odpovede pre ďalšie načítanie

        final_answer = polished_answer

        return {
            "best_answer": final_answer,
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
