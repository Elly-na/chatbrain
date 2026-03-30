"""
app.py — Upgraded Cisco Chatbot with Generative AI
Supports: file uploads, image analysis, IP validation, natural language
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import ChatDatabase
from ai_handler import ask_groq
from file_handler import save_uploaded_file, process_uploaded_file, cleanup_file, allowed_file
from validator import validate_ip, validate_subnet, validate_cisco_config, format_config_validation, extract_and_validate_ips
from functools import wraps
import os
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-in-production-please")

# File upload config
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# Initialize database
db = ChatDatabase()

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('login.html', error='Please enter username and password')

        user_id = db.verify_user(username, password)
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Wrong username or password')

    return render_template('login.html')


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not username or not password or not email:
        return render_template('login.html', reg_error='Please fill all fields')

    new_user_id = db.create_user(username, password, email)
    if new_user_id:
        session['user_id'] = new_user_id
        session['username'] = username
        return redirect(url_for('home'))
    else:
        return render_template('login.html', reg_error='Username already exists')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def home():
    return render_template('index.html', username=session.get('username'))


# ─────────────────────────────────────────────
#  MAIN CHAT ENDPOINT
# ─────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        if request.content_type and 'multipart/form-data' in request.content_type:
            message = request.form.get('message', '').strip()
            chat_id = request.form.get('chat_id')
            file = request.files.get('file')
        else:
            data = request.json or {}
            message = data.get('message', '').strip()
            chat_id = data.get('chat_id')
            file = None

        if not message and not file:
            return jsonify({'error': 'No message or file provided'}), 400

        file_content = None
        image_data = None
        image_type = "image/jpeg"
        file_info = None

        # Process uploaded file
        if file and file.filename:
            filepath, result = save_uploaded_file(file, UPLOAD_FOLDER)

            if filepath is None:
                return jsonify({'error': result}), 400

            filename = result
            file_content, image_data, img_type = process_uploaded_file(filepath, filename)

            if img_type and img_type.startswith("image/"):
                image_type = img_type

            if filename.endswith(('.txt', '.cfg')) and file_content:
                validation = validate_cisco_config(file_content)
                validation_text = format_config_validation(validation)
                file_content = f"AUTOMATIC VALIDATION RESULTS:\n{validation_text}\n\n---\nCONFIG FILE CONTENT:\n{file_content}"

            file_info = filename
            cleanup_file(filepath)

        # Default message if only file uploaded
        if not message and file_info:
            ext = file_info.rsplit('.', 1)[-1].lower() if '.' in file_info else ''
            if ext in ('png', 'jpg', 'jpeg'):
                message = "Please analyze this network diagram. Identify any issues, check the topology, and suggest improvements."
            elif ext in ('txt', 'cfg'):
                message = "Please review this Cisco configuration file, validate all IPs and commands, and fix any issues you find."
            elif ext == 'pdf':
                message = "Please summarize this document and explain the key networking concepts."
            else:
                message = "Please analyze this uploaded file and provide feedback."

        # Quick local validation — no API needed
        quick_response = try_quick_validation(message)
        if quick_response:
            if chat_id:
                db.add_message(int(chat_id), 'user', message)
                db.add_message(int(chat_id), 'assistant', quick_response)
            return jsonify({'type': 'bot', 'text': quick_response})

        # Get chat history
        history = []
        if chat_id:
            try:
                messages = db.get_chat_messages(int(chat_id))
                for msg in messages[-10:]:
                    role = 'assistant' if msg['type'] in ('bot', 'assistant') else 'user'
                    history.append({"role": role, "content": msg['text']})
            except Exception:
                history = []

        # Call AI
        response_text = ask_groq(
            user_message=message,
            chat_history=history,
            file_content=file_content,
            image_data=image_data,
            image_type=image_type
        )

        # Save to database
        if chat_id:
            try:
                db.add_message(int(chat_id), 'user', message)
                db.add_message(int(chat_id), 'assistant', response_text)
            except Exception:
                pass

        return jsonify({
            'type': 'bot',
            'text': response_text,
            'file_processed': file_info is not None
        })

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


# ─────────────────────────────────────────────
#  QUICK LOCAL VALIDATION
# ─────────────────────────────────────────────

def try_quick_validation(message):
    msg_lower = message.lower().strip()

    if any(word in msg_lower for word in ['valid ip', 'validate ip', 'check ip', 'is this ip']):
        ip_match = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', message)
        if ip_match:
            result = validate_ip(ip_match.group(1))
            if result['valid']:
                resp = f"✅ **{result['ip']}** is a valid {result['version']} address ({result['type']})"
                if result.get('suggestions'):
                    resp += "\n" + "\n".join(result['suggestions'])
                if result.get('issues'):
                    resp += "\n⚠️ Note: " + "; ".join(result['issues'])
                return resp
            else:
                resp = f"❌ **{ip_match.group(1)}** is NOT a valid IP address\n{result['error']}"
                if result.get('suggestions'):
                    resp += "\n💡 " + "\n".join(result['suggestions'])
                return resp

    if any(word in msg_lower for word in ['subnet', 'network info', 'cidr', '/24', '/30', '/8', '/16']):
        cidr_match = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})\b', message)
        if cidr_match:
            result = validate_subnet(cidr_match.group(1))
            if result['valid']:
                resp = f"📊 **Subnet Info: {cidr_match.group(1)}**\n"
                resp += f"• Network: {result['network']}\n"
                resp += f"• Broadcast: {result['broadcast']}\n"
                resp += f"• Subnet Mask: {result['netmask']}\n"
                resp += f"• Usable Hosts: {result['usable_hosts']}\n"
                if result.get('first_host'):
                    resp += f"• Host Range: {result['first_host']} → {result['last_host']}\n"
                if result.get('tip'):
                    resp += f"\n{result['tip']}"
                return resp

    return None


# ─────────────────────────────────────────────
#  CHAT MANAGEMENT
# ─────────────────────────────────────────────

@app.route('/api/chats', methods=['GET'])
@login_required
def get_chats():
    user_id = session.get('user_id')
    chats = db.get_user_chats(user_id)
    return jsonify(chats)


@app.route('/api/chats', methods=['POST'])
@login_required
def create_chat():
    user_id = session.get('user_id')
    data = request.json or {}
    name = data.get('name', 'New Chat')
    chat_id = db.create_chat(user_id, name)
    return jsonify({'id': chat_id, 'name': name})


@app.route('/api/chats/<int:chat_id>', methods=['GET'])
@login_required
def get_chat_messages(chat_id):
    messages = db.get_chat_messages(chat_id)
    return jsonify(messages)


@app.route('/api/chats/<int:chat_id>', methods=['PUT'])
@login_required
def rename_chat(chat_id):
    data = request.json or {}
    new_name = data.get('name')
    if new_name:
        db.rename_chat(chat_id, new_name)
        return jsonify({'success': True})
    return jsonify({'error': 'No name provided'}), 400


@app.route('/api/chats/<int:chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    db.delete_chat(chat_id)
    return jsonify({'success': True})


# ─────────────────────────────────────────────
#  VALIDATION ENDPOINT
# ─────────────────────────────────────────────

@app.route('/api/validate', methods=['POST'])
@login_required
def validate():
    data = request.json or {}
    validate_type = data.get('type')

    if validate_type == 'ip':
        result = validate_ip(data.get('value', ''))
        return jsonify(result)
    elif validate_type == 'subnet':
        result = validate_subnet(data.get('value', ''))
        return jsonify(result)
    elif validate_type == 'config':
        config_text = data.get('value', '')
        result = validate_cisco_config(config_text)
        result['formatted'] = format_config_validation(result)
        return jsonify(result)

    return jsonify({'error': 'Unknown validation type'}), 400


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  CISCO AI CHATBOT — GENERATIVE VERSION")
    print("="*60)
    print("\n  🌐 Open your browser: http://127.0.0.1:5000")
    print("\n" + "="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)