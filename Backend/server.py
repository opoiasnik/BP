from flask import Flask, request, jsonify
from flask_cors import CORS  # Импортируем CORS
from model import process_query_with_mistral

# Инициализация приложения Flask
app = Flask(__name__)
CORS(app)  # Разрешаем все запросы CORS для всех маршрутов


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data.get('query', '')

    # Обработка запроса с использованием функции модели
    response = process_query_with_mistral(query)

    # Возвращаем результат в формате JSON
    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
