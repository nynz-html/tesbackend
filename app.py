# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Database initialization
def init_db():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  author TEXT NOT NULL,
                  content TEXT NOT NULL,
                  date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  delete_token TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/messages', methods=['GET'])
def get_messages():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("SELECT id, author, content, date_created FROM messages ORDER BY date_created DESC")
    messages = []
    for row in c.fetchall():
        messages.append({
            'id': row[0],
            'author': row[1],
            'content': row[2],
            'date': datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y')
        })
    conn.close()
    return jsonify(messages)

@app.route('/messages', methods=['POST'])
def add_message():
    author = request.json.get('author')
    content = request.json.get('content')
    
    if not author or not content:
        return jsonify({'error': 'Author and content are required'}), 400
    
    # Generate a delete token (in a real app, use something more secure)
    import uuid
    delete_token = str(uuid.uuid4())
    
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (author, content, delete_token) VALUES (?, ?, ?)",
              (author, content, delete_token))
    conn.commit()
    message_id = c.lastrowid
    conn.close()
    
    return jsonify({
        'id': message_id,
        'author': author,
        'content': content,
        'date': datetime.now().strftime('%B %d, %Y'),
        'delete_token': delete_token
    })

@app.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    delete_token = request.json.get('delete_token')
    
    if not delete_token:
        return jsonify({'error': 'Delete token is required'}), 400
    
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("SELECT delete_token FROM messages WHERE id = ?", (message_id,))
    result = c.fetchone()
    
    if not result:
        return jsonify({'error': 'Message not found'}), 404
    
    if result[0] != delete_token:
        return jsonify({'error': 'Invalid delete token'}), 403
    
    c.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/admin')
def admin():
    # In a real application, you would add authentication here
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("SELECT id, author, content, date_created FROM messages ORDER BY date_created DESC")
    messages = []
    for row in c.fetchall():
        messages.append({
            'id': row[0],
            'author': row[1],
            'content': row[2],
            'date': datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y at %H:%M')
        })
    conn.close()
    return render_template('admin.html', messages=messages)

if __name__ == '__main__':
    app.run(debug=True)