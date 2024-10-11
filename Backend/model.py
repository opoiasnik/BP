import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from mistralai import Mistral
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка API ключа для Mistral
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    raise ValueError("API ключ не найден. Убедитесь, что переменная MISTRAL_API_KEY установлена.")

client = Mistral(api_key=api_key)

# Инициализация модели для векторных представлений
logger.info("Загрузка модели HuggingFaceEmbeddings...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Настройка подключения к Elasticsearch через LangChain
logger.info("Подключение к Elasticsearch через LangChain...")
vectorstore = ElasticsearchStore(
    es_url="http://localhost:9200",
    index_name='drug_docs',
    embedding=embeddings,
    es_user='elastic',
    es_password='sSz2BEGv56JRNjGFwoQ191RJ'
)

def process_query_with_mistral(query, k=10):
    logger.info("Обработка запроса началась.")

    try:
        response = vectorstore.similarity_search(query, k=k)
        if not response:
            logger.info("Ничего не найдено.")
            return {"summary": "Ничего не найдено", "links": [], "status_log": ["Ничего не найдено."]}

        logger.info("Поиск в Elasticsearch завершён.")

        documents = []
        links = []
        for hit in response:
            text = hit.metadata.get('text', None)
            if text:
                documents.append(text)
            link = hit.metadata.get('link', '-')
            links.append(link)

        structured_prompt = (
            f"Na základe otázky: '{query}' a nasledujúcich informácií: {documents}, "
            "poskytnite odpoveď, ktorá obsahает три lieky alebo riešenія с краткым vysvetленím pre každý з них. "
            "Odpoveď by mala byť poskytnutá в slovenčine."
        )

        if len(structured_prompt.split()) > 32000:
            logger.info("Запрос слишком большой для обработки моделью.")
            return {"summary": "Запрос слишком большой для обработки моделью.", "links": links,
                    "status_log": ["Запрос слишком большой для обработки моделью."]}

        logger.info("Запрос к модели Mistral отправлен.")

        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{
                "content": structured_prompt,
                "role": "user",
            }]
        )

        if response:
            summary = response.choices[0].message.content
            logger.info("Ответ получен от модели Mistral.")
            logger.info(f"Полученный ответ: {summary}")
        else:
            summary = "Ответ не был сгенерирован"
            logger.info("Модель Mistral не вернула ответ.")

        return {"summary": summary, "links": links, "status_log": ["Ответ получен от модели Mistral."]}

    except Exception as e:
        error_message = f"Ошибка: {str(e)}"
        logger.info(error_message)
        return {"summary": "Произошла ошибка", "links": [], "status_log": [error_message]}
