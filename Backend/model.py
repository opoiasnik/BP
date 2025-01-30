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
from googletrans import Translator  # Translator for final polishing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config_file_path = "config.json"
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)

# Load Mistral API key
mistral_api_key = "hXDC4RBJk1qy5pOlrgr01GtOlmyCBaNs"
if not mistral_api_key:
    raise ValueError("Mistral API key not found in configuration.")


###############################################################################
#                       Function to translate entire text to Slovak           #
###############################################################################
translator = Translator()

def translate_to_slovak(text: str) -> str:
    """
    Translates the entire text into Slovak.
    Logs the text before and after translation.
    """
    if not text.strip():
        return text

    try:
        # 1) Slovak (or any language) -> English
        mid_result = translator.translate(text, src='auto', dest='en').text

        # 2) English -> Slovak
        final_result = translator.translate(mid_result, src='en', dest='sk').text

        return final_result
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text  # fallback to the original text



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
                if response.status_code == 429:  # Too Many Requests
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

# Connect to Elasticsearch
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
    """
    Evaluates results by:
      - text length,
      - presence of query keywords, etc.
    Returns a rating and explanation.
    """
    query_keywords = query.split()
    total_score = 0
    explanation = []

    for i, summary in enumerate(summaries):
        # Length-based scoring
        length_score = min(len(summary) / 100, 10)
        total_score += length_score
        explanation.append(f"Document {i+1}: Length score - {length_score}")

        # Keyword-based scoring
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
            # Slovak prompt
            vector_prompt = (
                f"Na základe otázky: '{query}' a nasledujúcich informácií o liekoch: {vector_documents}. "
                "Uveďte tri vhodné lieky alebo riešenia s krátkym vysvetlením pre každý z nich. "
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
            # Slovak prompt
            text_prompt = (
                f"Na základe otázky: '{query}' a nasledujúcich informácií o liekoch: {text_documents}. "
                "Uveďte tri vhodné lieky alebo riešenia s krátkym vysvetlením pre každý z nich. "
                "Odpoveď musí byť v slovenčine."
            )
            summary_small_text = llm_small.generate_text(prompt=text_prompt, max_tokens=700, temperature=0.7)
            summary_large_text = llm_large.generate_text(prompt=text_prompt, max_tokens=700, temperature=0.7)

            split_summary_small_text = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20).split_text(summary_small_text)
            split_summary_large_text = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20).split_text(summary_large_text)

            small_text_eval = evaluate_results(query, split_summary_small_text, 'Mistral Small')
            large_text_eval = evaluate_results(query, split_summary_large_text, 'Mistral Large')
        else:
            small_text_eval = {"rating": 0, "explanation": "No results"}
            large_text_eval = {"rating": 0, "explanation": "No results"}
            summary_small_text = ""
            summary_large_text = ""

        # Combine all results and pick the best
        all_results = [
            {"eval": small_vector_eval, "summary": summary_small_vector, "model": "Mistral Small Vector"},
            {"eval": large_vector_eval, "summary": summary_large_vector, "model": "Mistral Large Vector"},
            {"eval": small_text_eval, "summary": summary_small_text, "model": "Mistral Small Text"},
            {"eval": large_text_eval, "summary": summary_large_text, "model": "Mistral Large Text"},
        ]

        best_result = max(all_results, key=lambda x: x["eval"]["rating"])
        logger.info(f"Best result from model {best_result['model']} with score {best_result['eval']['rating']}.")

        # Final translation to Slovak (with logs before/after)
        polished_answer = translate_to_slovak(best_result["summary"])

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
