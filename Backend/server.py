import time
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Импортujeme funkciu process_query_with_mistral z model.py
from model import process_query_with_mistral

# Pôvodné nastavenie času
_real_time = time.time
time.time = lambda: _real_time() - 1

# Parametre pripojenia k DB
DATABASE_CONFIG = {
    "dbname": "HealthAIDB",
    "user": "postgres",
    "password": "Oleg2005",  # alebo "" ak bez hesla
    "host": "localhost",
    "port": 5432,
}
# DATABASE_CONFIG = {
#     "dbname": "postgres",
#     "user": "postgres",
#     "password": "healthai!",
#     "host": "health-ai-user-db.cxeum6cmct3r.eu-west-1.rds.amazonaws.com",
#     "port": 5432,
# }

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    conn = psycopg2.connect(**DATABASE_CONFIG)
    logger.info("Подключение к базе данных успешно установлено")
except Exception as e:
    logger.error(f"Ошибка подключения к базе данных: {e}", exc_info=True)
    conn = None

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

CLIENT_ID = "532143017111-4eqtlp0oejqaovj6rf5l1ergvhrp4vao.apps.googleusercontent.com"

def save_user_to_db(name, email, google_id=None, password=None):
    logger.info(f"Сохранение пользователя {name} с email: {email} в БД")
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO users (name, email, google_id, password)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                """,
                (name, email, google_id, password)
            )
            conn.commit()
        logger.info(f"Пользователь {name} ({email}) успешно сохранен")
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя {name} ({email}) в БД: {e}", exc_info=True)

@app.route('/api/verify', methods=['POST'])
def verify_token():
    logger.info("Получен запрос на верификацию токена")
    data = request.get_json()
    token = data.get('token')
    if not token:
        logger.warning("Токен не предоставлен в запросе")
        return jsonify({'error': 'No token provided'}), 400
    try:
        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), CLIENT_ID)
        user_email = id_info.get('email')
        user_name = id_info.get('name')
        google_id = id_info.get('sub')
        logger.info(f"Токен верифицирован для пользователя: {user_name} ({user_email})")
        save_user_to_db(name=user_name, email=user_email, google_id=google_id)
        return jsonify({'message': 'Authentication successful', 'user': {'email': user_email, 'name': user_name}}), 200
    except ValueError as e:
        logger.error(f"Ошибка верификации токена: {e}", exc_info=True)
        return jsonify({'error': 'Invalid token'}), 400

@app.route('/api/register', methods=['POST'])
def register():
    logger.info("Получен запрос на регистрацию нового пользователя")
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if not all([name, email, password]):
        logger.warning("Не все поля предоставлены для регистрации")
        return jsonify({'error': 'All fields are required'}), 400
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cur.fetchone()
            if existing_user:
                logger.warning(f"Пользователь с email {email} уже существует")
                return jsonify({'error': 'User already exists'}), 409
        save_user_to_db(name=name, email=email, password=password)
        logger.info(f"Пользователь {name} ({email}) успешно зарегистрирован")
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    logger.info("Получен запрос на логин")
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not all([email, password]):
        logger.warning("Email или пароль не предоставлены")
        return jsonify({'error': 'Email and password are required'}), 400
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user or user.get('password') != password:
                logger.warning(f"Неверные учетные данные для email: {email}")
                return jsonify({'error': 'Invalid credentials'}), 401
        logger.info(f"Пользователь {user.get('name')} ({email}) успешно вошел в систему")
        return jsonify({'message': 'Login successful', 'user': {'name': user.get('name'), 'email': user.get('email')}}), 200
    except Exception as e:
        logger.error(f"Ошибка при логине пользователя: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    logger.info("Получен запрос на чат")
    data = request.get_json()
    query = data.get('query', '')
    user_email = data.get('email')
    chat_id = data.get('chatId')  # Если задан, идёт существующий чат

    if not query:
        logger.warning("Запрос не предоставлен")
        return jsonify({'error': 'No query provided'}), 400

    logger.info(f"Обработка запроса для chatId: {chat_id if chat_id else 'новый чат'} | Запрос: {query}")

    # Получение контекста чата из БД
    chat_context = ""
    if chat_id:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT chat, user_data FROM chat_history WHERE id = %s", (chat_id,))
                result = cur.fetchone()
                if result:
                    chat_context = result.get("chat", "")
                    logger.info(f"Загружен контекст чата из БД для chatId {chat_id}: {chat_context}")
                else:
                    logger.info(f"Для chatId {chat_id} контекст не найден")
        except Exception as e:
            logger.error(f"Ошибка при загрузке контекста чата из БД: {e}", exc_info=True)

    logger.info("Вызов функции process_query_with_mistral")
    response_obj = process_query_with_mistral(query, chat_id=chat_id, chat_context=chat_context)
    best_answer = response_obj.get("best_answer", "") if isinstance(response_obj, dict) else str(response_obj)
    logger.info(f"Ответ от process_query_with_mistral: {best_answer}")

    best_answer = re.sub(r'[*#]', '', best_answer)
    best_answer = re.sub(r'(\d\.\s)', r'\n\n\1', best_answer)
    best_answer = re.sub(r':\s-', r':\n-', best_answer)

    # Обновление или создание записи в chat_history, включая поле user_data, если есть
    if chat_id:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT chat FROM chat_history WHERE id = %s", (chat_id,))
                existing_chat = cur.fetchone()
                if existing_chat:
                    updated_chat = existing_chat['chat'] + f"\nUser: {query}\nBot: {best_answer}"
                    if "patient_data" in response_obj:
                        cur.execute("UPDATE chat_history SET chat = %s, user_data = %s WHERE id = %s",
                                    (updated_chat, response_obj["patient_data"], chat_id))
                    else:
                        cur.execute("UPDATE chat_history SET chat = %s WHERE id = %s", (updated_chat, chat_id))
                    conn.commit()
                    logger.info(f"История чата для chatId {chat_id} успешно обновлена")
                else:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur2:
                        cur2.execute(
                            "INSERT INTO chat_history (user_email, chat) VALUES (%s, %s) RETURNING id",
                            (user_email, f"User: {query}\nBot: {best_answer}")
                        )
                        new_chat_id = cur2.fetchone()['id']
                        conn.commit()
                        chat_id = new_chat_id
                        logger.info(f"Создан новый чат с chatId: {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении/создании истории чата: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    else:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "INSERT INTO chat_history (user_email, chat) VALUES (%s, %s) RETURNING id",
                    (user_email, f"User: {query}\nBot: {best_answer}")
                )
                new_chat_id = cur.fetchone()['id']
                conn.commit()
                chat_id = new_chat_id
                logger.info(f"Новый чат успешно создан с chatId: {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при создании нового чата: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    return jsonify({'response': {'best_answer': best_answer, 'model': response_obj.get("model", ""), 'chatId': chat_id}}), 200

@app.route('/api/save_user_data', methods=['POST'])
def save_user_data():
    logger.info("Получен запрос на сохранение данных пользователя")
    data = request.get_json()
    chat_id = data.get('chatId')
    user_data = data.get('userData')
    if not chat_id or not user_data:
        return jsonify({'error': 'chatId and userData are required'}), 400
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("UPDATE chat_history SET user_data = %s WHERE id = %s", (user_data, chat_id))
            conn.commit()
        logger.info(f"Данные пользователя для chatId {chat_id} успешно обновлены")
        return jsonify({'message': 'User data updated successfully'}), 200
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных пользователя: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat_history', methods=['GET'])
def get_chat_history():
    logger.info("Получен запрос на получение истории чата")
    user_email = request.args.get('email')
    if not user_email:
        return jsonify({'error': 'User email is required'}), 400
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, chat, user_data, created_at FROM chat_history WHERE user_email = %s ORDER BY created_at DESC",
                (user_email,)
            )
            history = cur.fetchall()
        return jsonify({'history': history}), 200
    except Exception as e:
        logger.error(f"Ошибка при получении истории чата для {user_email}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat_history', methods=['DELETE'])
def delete_chat():
    logger.info("Получен запрос на удаление чата")
    chat_id = request.args.get('id')
    if not chat_id:
        return jsonify({'error': 'Chat id is required'}), 400
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_history WHERE id = %s", (chat_id,))
            conn.commit()
        return jsonify({'message': 'Chat deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Ошибка при удалении чата с chatId {chat_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat_history_detail', methods=['GET'])
def chat_history_detail():
    logger.info("Получен запрос на получение деталей чата")
    chat_id = request.args.get('id')
    if not chat_id:
        return jsonify({'error': 'Chat id is required'}), 400
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, chat, user_data, created_at FROM chat_history WHERE id = %s", (chat_id,))
            chat = cur.fetchone()
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        return jsonify({'chat': chat}), 200
    except Exception as e:
        logger.error(f"Ошибка при получении деталей чата для chatId {chat_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Запуск Flask приложения")
    app.run(host='0.0.0.0', port=5000, debug=True)
