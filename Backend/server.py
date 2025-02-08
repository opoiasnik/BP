from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests
import logging

# Импортируем функцию обработки из model.py
from model import process_query_with_mistral

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# Ваш Google Client ID
CLIENT_ID = "532143017111-4eqtlp0oejqaovj6rf5l1ergvhrp4vao.apps.googleusercontent.com"


# Маршрут для верификации токенов Google OAuth
@app.route('/api/verify', methods=['POST'])
def verify_token():
    data = request.get_json()
    token = data.get('token')

    if not token:
        return jsonify({'error': 'No token provided'}), 400

    try:
        # Проверка токена с использованием Google API
        id_info = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

        # Получение данных пользователя
        user_email = id_info.get('email')
        user_name = id_info.get('name')

        logger.info(f"User authenticated: {user_name} ({user_email})")
        return jsonify({'message': 'Authentication successful', 'user': {'email': user_email, 'name': user_name}}), 200

    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        return jsonify({'error': 'Invalid token'}), 400


# Маршрут для обработки запросов от фронтенда
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    # Вызов вашей функции для обработки запроса
    response = process_query_with_mistral(query)
    return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
