from flask import Flask, request, jsonify
from flask_cors import CORS  # Для поддержки CORS
from model import process_query_with_mistral  # Импорт вашей функции обработки запроса

# Инициализация приложения Flask
app = Flask(__name__)

# Включение CORS для всех маршрутов
CORS(app)

@app.route('/api/chat', methods=['POST'])
def chat():
    # Получение данных из запроса
    data = request.get_json()
    query = data.get('query', '')

    if not query:
        return jsonify({'error': 'Вопрос не был предоставлен.'}), 400

    # Обработка запроса через Mistral и Elasticsearch
    try:
        summary, links = process_query_with_mistral(query)
        return jsonify({'summary': summary, 'links': links})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    # Запуск сервера на порту 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
