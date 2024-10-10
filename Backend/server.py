from flask import Flask, request, jsonify
from flask_cors import CORS
from model import process_query_with_mistral 

app = Flask(__name__)

CORS(app)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data.get('query', '')

    if not query:
        return jsonify({'error': 'Вопрос не был предоставлен.'}), 400

    try:
        summary, links = process_query_with_mistral(query)
        return jsonify({'summary': summary, 'links': links})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
