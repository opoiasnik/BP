import time
import re  # Импортируем модуль для работы с регулярными выражениями

# Сохраняем оригинальную функцию time.time
_real_time = time.time
# Переопределяем time.time для смещения времени на 1 секунду назад
time.time = lambda: _real_time() - 1

from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests
import logging

# Импортируем функцию обработки из model.py
from model import process_query_with_mistral
import psycopg2
from psycopg2.extras import RealDictCursor

# Параметры подключения к базе данных
DATABASE_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "healthai!",
    "host": "health-ai-user-db.cxeum6cmct3r.eu-west-1.rds.amazonaws.com",
    "port": 5432,
}

# Подключение к базе данных
try:
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    print("Подключение к базе данных успешно установлено")
except Exception as e:
    print(f"Ошибка подключения к базе данных: {e}")
    conn = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# Ваш Google Client ID
CLIENT_ID = "532143017111-4eqtlp0oejqaovj6rf5l1ergvhrp4vao.apps.googleusercontent.com"

def save_user_to_db(name, email, google_id=None, password=None):
    try:
        cursor.execute(
            """
            INSERT INTO users (name, email, google_id, password)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            """,
            (name, email, google_id, password)
        )
        conn.commit()
        print(f"User {name} ({email}) saved successfully!")
    except Exception as e:
        print(f"Error saving user to database: {e}")

# Эндпоинт для верификации токенов Google OAuth
@app.route('/api/verify', methods=['POST'])
def verify_token():
    data = request.get_json()
    token = data.get('token')
    if not token:
        return jsonify({'error': 'No token provided'}), 400
    try:
        id_info = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        user_email = id_info.get('email')
        user_name = id_info.get('name')
        google_id = id_info.get('sub')  # Уникальный идентификатор пользователя Google
        save_user_to_db(name=user_name, email=user_email, google_id=google_id)
        logger.info(f"User authenticated and saved: {user_name} ({user_email})")
        return jsonify({'message': 'Authentication successful', 'user': {'email': user_email, 'name': user_name}}), 200
    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        return jsonify({'error': 'Invalid token'}), 400

# Эндпоинт для регистрации пользователя с проверкой на дублирование
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')  # Рекомендуется хэшировать пароль
    if not all([name, email, password]):
        return jsonify({'error': 'All fields are required'}), 400
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409
        save_user_to_db(name=name, email=email, password=password)
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Эндпоинт для логина пользователя
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not all([email, password]):
        return jsonify({'error': 'Email and password are required'}), 400
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        # Сравнение простым текстом — в production используйте хэширование!
        if user.get('password') != password:
            return jsonify({'error': 'Invalid credentials'}), 401
        return jsonify({'message': 'Login successful', 'user': {'name': user.get('name'), 'email': user.get('email')}}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Объединённый эндпоинт для обработки запроса чата
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data.get('query', '')
    user_email = data.get('email')  # email пользователя (если передается)
    chat_id = data.get('chatId')    # параметр для обновления существующего чата

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    # Вызов функции для обработки запроса (например, чат-бота)
    response_obj = process_query_with_mistral(query)
    best_answer = ""
    if isinstance(response_obj, dict):
        best_answer = response_obj.get("best_answer", "")
    else:
        best_answer = str(response_obj)

    # Форматирование ответа с использованием re.sub
    best_answer = re.sub(r'[*#]', '', best_answer)
    best_answer = re.sub(r'(\d\.\s)', r'\n\n\1', best_answer)
    best_answer = re.sub(r':\s-', r':\n-', best_answer)

    # Сохраняем в базу данных только текстовый ответ
    if chat_id:
        try:
            cursor.execute("SELECT chat FROM chat_history WHERE id = %s", (chat_id,))
            existing_chat = cursor.fetchone()
            if existing_chat:
                updated_chat = existing_chat['chat'] + f"\nUser: {query}\nBot: {best_answer}"
                cursor.execute("UPDATE chat_history SET chat = %s WHERE id = %s", (updated_chat, chat_id))
                conn.commit()
            else:
                cursor.execute("INSERT INTO chat_history (user_email, chat) VALUES (%s, %s)",
                               (user_email, f"User: {query}\nBot: {best_answer}"))
                conn.commit()
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        try:
            cursor.execute("INSERT INTO chat_history (user_email, chat) VALUES (%s, %s)",
                           (user_email, f"User: {query}\nBot: {best_answer}"))
            conn.commit()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Возвращаем только текстовый ответ (без дополнительных данных)
    return jsonify({'response': {'best_answer': best_answer, 'model': 'Mistral Small Vector'}}), 200

# Эндпоинт для получения истории чатов конкретного пользователя
@app.route('/api/chat_history', methods=['GET'])
def get_chat_history():
    user_email = request.args.get('email')
    if not user_email:
        return jsonify({'error': 'User email is required'}), 400
    try:
        cursor.execute(
            "SELECT id, chat, created_at FROM chat_history WHERE user_email = %s ORDER BY created_at DESC",
            (user_email,)
        )
        history = cursor.fetchall()
        return jsonify({'history': history}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Эндпоинт для получения деталей чата по ID
@app.route('/api/chat_history_detail', methods=['GET'])
def chat_history_detail():
    chat_id = request.args.get('id')
    if not chat_id:
        return jsonify({'error': 'Chat id is required'}), 400
    try:
        cursor.execute("SELECT id, chat, created_at FROM chat_history WHERE id = %s", (chat_id,))
        chat = cursor.fetchone()
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        return jsonify({'chat': chat}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
