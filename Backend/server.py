from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Импортируем функцию обработки из model.py
from model import process_query_with_mistral

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# Маршрут для обработки запросов от фронтенда
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
