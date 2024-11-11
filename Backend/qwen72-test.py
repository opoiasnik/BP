import torch
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer
from elasticsearch import Elasticsearch

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подключение к Elasticsearch
es = Elasticsearch(
    ["https://localhost:9200"],
    basic_auth=("elastic", "S7DoO3ma=G=9USBPbqq3"),  # Ваш пароль
    verify_certs=False
)
index_name = 'drug_docs'

# Загрузка токенизатора и модели
model_name = "Qwen/Qwen2.5-7B-Instruct"
device = "cuda:0" if torch.cuda.is_available() else "cpu"

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Проверка наличия pad_token
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

def text_search(query, k=10, max_doc_length=300, max_docs=3):
    try:
        es_results = es.search(
            index=index_name,
            body={"size": k, "query": {"match": {"text": query}}}
        )
        text_documents = [hit['_source'].get('text', '') for hit in es_results['hits']['hits']]
        text_documents = [doc[:max_doc_length] for doc in text_documents[:max_docs]]
        return text_documents
    except Exception as e:
        logger.error(f"Ошибка поиска: {str(e)}")
        return []

# Пример запроса для поиска
query = "čo piť pri horúčke"
text_documents = text_search(query)

# Обрезаем текст, если он превышает предел токенов модели
max_tokens_per_input = 1024  # Установим более низкое значение для max_tokens
context_text = ' '.join(text_documents)
input_text = (
    f"Informácie o liekoch: {context_text[:max_tokens_per_input]}\n"
    "Uveďte tri konkrétne lieky alebo riešenia s veľmi krátkym vysvetlením pre každý z nich.\n"
    "Odpoveď v slovenčine:"
)

# Токенизация входного текста
inputs = tokenizer(input_text, return_tensors="pt", max_length=max_tokens_per_input, truncation=True).to(device)

try:
    generated_ids = model.generate(
        inputs.input_ids,
        attention_mask=inputs.attention_mask,
        max_new_tokens=300,  # Снижено значение
        temperature=0.7,
        top_k=50,
        top_p=0.9,
        do_sample=False,  # Отключено семплирование для детерминированного вывода
        pad_token_id=tokenizer.pad_token_id
    )
    response = tokenizer.decode(generated_ids[0], skip_special_tokens=True, errors='ignore')
    print("Сгенерированный текст:", response)
except RuntimeError as e:
    print(f"Произошла ошибка во время генерации: {e}")

