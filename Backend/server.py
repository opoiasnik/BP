import time
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

# Параметры подключения
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

# Эндпоинт для регистрации пользователя
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')  # Рекомендуется хэшировать пароль

    if not all([name, email, password]):
        return jsonify({'error': 'All fields are required'}), 400

    try:
        # Проверка, существует ли пользователь с таким email
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409

        # Сохранение пользователя в базу данных
        save_user_to_db(name=name, email=email, password=password)

        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Эндпоинт для логина пользователя (см. предыдущий пример)
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

        return jsonify({
            'message': 'Login successful',
            'user': {
                'name': user.get('name'),
                'email': user.get('email')
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Эндпоинт для обработки запросов от фронтенда
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    response = process_query_with_mistral(query)
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
