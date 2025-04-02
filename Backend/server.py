import time
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from model import process_query_with_mistral

_real_time = time.time
time.time = lambda: _real_time() - 1

# Database connection parameters
DATABASE_CONFIG = {
    "dbname": "HealthAIDB",
    "user": "postgres",
    "password": "Oleg2005",
    "host": "postgres",
    "port": 5432,
}

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    conn = psycopg2.connect(**DATABASE_CONFIG)
    logger.info("Database connection established successfully")
except Exception as e:
    logger.error(f"Error connecting to database: {e}", exc_info=True)
    conn = None

def init_db():
    create_users_query = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        google_id TEXT,
        password TEXT
    );
    """
    create_chat_history_query = """
    CREATE TABLE IF NOT EXISTS chat_history (
        id SERIAL PRIMARY KEY,
        user_email TEXT NOT NULL,
        chat TEXT NOT NULL,
        user_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cur:
            cur.execute(create_users_query)
            cur.execute(create_chat_history_query)
            conn.commit()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}", exc_info=True)
        conn.rollback()

if conn:
    init_db()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

CLIENT_ID = "532143017111-4eqtlp0oejqaovj6rf5l1ergvhrp4vao.apps.googleusercontent.com"

def save_user_to_db(name, email, google_id=None, password=None):
    logger.info(f"Saving user {name} with email: {email} to the database")
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
        logger.info(f"User {name} ({email}) saved successfully")
    except Exception as e:
        logger.error(f"Error saving user {name} ({email}) to database: {e}", exc_info=True)

@app.route('/api/verify', methods=['POST'])
def verify_token():
    logger.info("Received token verification request")
    data = request.get_json()
    token = data.get('token')
    if not token:
        logger.warning("Token not provided in request")
        return jsonify({'error': 'No token provided'}), 400
    try:
        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), CLIENT_ID)
        user_email = id_info.get('email')
        user_name = id_info.get('name')
        google_id = id_info.get('sub')
        logger.info(f"Token verified for user: {user_name} ({user_email})")
        save_user_to_db(name=user_name, email=user_email, google_id=google_id)
        return jsonify({'message': 'Authentication successful', 'user': {'email': user_email, 'name': user_name}}), 200
    except ValueError as e:
        logger.error(f"Token verification error: {e}", exc_info=True)
        return jsonify({'error': 'Invalid token'}), 400

@app.route('/api/register', methods=['POST'])
def register():
    logger.info("Received new user registration request")
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if not all([name, email, password]):
        logger.warning("Not all required fields provided for registration")
        return jsonify({'error': 'All fields are required'}), 400
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cur.fetchone()
            if existing_user:
                logger.warning(f"User with email {email} already exists")
                return jsonify({'error': 'User already exists'}), 409
        save_user_to_db(name=name, email=email, password=password)
        logger.info(f"User {name} ({email}) registered successfully")
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        logger.error(f"Error during user registration: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    logger.info("Received login request")
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not all([email, password]):
        logger.warning("Email or password not provided")
        return jsonify({'error': 'Email and password are required'}), 400
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user or user.get('password') != password:
                logger.warning(f"Invalid credentials for email: {email}")
                return jsonify({'error': 'Invalid credentials'}), 401
        logger.info(f"User {user.get('name')} ({email}) logged in successfully")
        return jsonify({'message': 'Login successful', 'user': {'name': user.get('name'), 'email': user.get('email')}}), 200
    except Exception as e:
        logger.error(f"Error during user login: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    logger.info("Received chat request")
    data = request.get_json()
    query = data.get('query', '')
    user_email = data.get('email')
    chat_id = data.get('chatId')

    if not query:
        logger.warning("No query provided")
        return jsonify({'error': 'No query provided'}), 400

    logger.info(f"Processing request for chatId: {chat_id if chat_id else 'new chat'} | Query: {query}")

    # Retrieve chat context from the database
    chat_context = ""
    if chat_id:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT chat, user_data FROM chat_history WHERE id = %s", (chat_id,))
                result = cur.fetchone()
                if result:
                    chat_context = result.get("chat", "")
                    logger.info(f"Loaded chat context for chatId {chat_id}: {chat_context}")
                else:
                    logger.info(f"No chat context found for chatId {chat_id}")
        except Exception as e:
            logger.error(f"Error loading chat context from DB: {e}", exc_info=True)

    logger.info("Calling process_query_with_mistral function")
    response_obj = process_query_with_mistral(query, chat_id=chat_id, chat_context=chat_context)
    best_answer = response_obj.get("best_answer", "") if isinstance(response_obj, dict) else str(response_obj)
    logger.info(f"Response from process_query_with_mistral: {best_answer}")

    best_answer = re.sub(r'[*#]', '', best_answer)
    best_answer = re.sub(r'(\d\.\s)', r'\n\n\1', best_answer)
    best_answer = re.sub(r':\s-', r':\n-', best_answer)

    # Update or create chat_history record including user_data if available
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
                    logger.info(f"Chat history for chatId {chat_id} updated successfully")
                else:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur2:
                        cur2.execute(
                            "INSERT INTO chat_history (user_email, chat) VALUES (%s, %s) RETURNING id",
                            (user_email, f"User: {query}\nBot: {best_answer}")
                        )
                        new_chat_id = cur2.fetchone()['id']
                        conn.commit()
                        chat_id = new_chat_id
                        logger.info(f"New chat created with chatId: {chat_id}")
        except Exception as e:
            logger.error(f"Error updating/creating chat history: {e}", exc_info=True)
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
                logger.info(f"New chat created with chatId: {chat_id}")
        except Exception as e:
            logger.error(f"Error creating new chat: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    return jsonify({'response': {'best_answer': best_answer, 'model': response_obj.get("model", ""), 'chatId': chat_id}}), 200

@app.route('/api/save_user_data', methods=['POST'])
def save_user_data():
    logger.info("Received request to save user data")
    data = request.get_json()
    chat_id = data.get('chatId')
    user_data = data.get('userData')
    if not chat_id or not user_data:
        return jsonify({'error': 'chatId and userData are required'}), 400
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("UPDATE chat_history SET user_data = %s WHERE id = %s", (user_data, chat_id))
            conn.commit()
        logger.info(f"User data for chatId {chat_id} updated successfully")
        return jsonify({'message': 'User data updated successfully'}), 200
    except Exception as e:
        logger.error(f"Error updating user data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat_history', methods=['GET'])
def get_chat_history():
    logger.info("Received request to get chat history")
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
        logger.error(f"Error getting chat history for {user_email}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat_history', methods=['DELETE'])
def delete_chat():
    logger.info("Received request to delete chat")
    chat_id = request.args.get('id')
    if not chat_id:
        return jsonify({'error': 'Chat id is required'}), 400
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_history WHERE id = %s", (chat_id,))
            conn.commit()
        return jsonify({'message': 'Chat deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting chat with chatId {chat_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_user_data', methods=['GET'])
def get_user_data():
    chat_id = request.args.get('chatId')
    if not chat_id:
        return jsonify({'error': 'Chat id is required'}), 400
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT user_data FROM chat_history WHERE id = %s", (chat_id,))
            result = cur.fetchone()
        if result and result.get("user_data"):
            return jsonify({'user_data': result.get("user_data")}), 200
        else:
            return jsonify({'user_data': None}), 200
    except Exception as e:
        logger.error(f"Error retrieving user data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat_history_detail', methods=['GET'])
def chat_history_detail():
    logger.info("Received request to get chat details")
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
        logger.error(f"Error getting chat details for chatId {chat_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(host='0.0.0.0', port=5000, debug=True)
