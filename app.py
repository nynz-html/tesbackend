# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime
import sqlite3
import os
import uuid

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
                  session_id TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('messages.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    # Generate a unique session ID if not exists
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/messages', methods=['GET'])
def get_messages():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, author, content, date_created FROM messages ORDER BY date_created DESC")
    messages = []
    for row in c.fetchall():
        messages.append({
            'id': row['id'],
            'author': row['author'],
            'content': row['content'],
            'date': datetime.strptime(row['date_created'], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y'),
            'can_delete': 'user_id' in session and row['session_id'] == session['user_id']
        })
    conn.close()
    return jsonify(messages)

@app.route('/messages', methods=['POST'])
def add_message():
    author = request.json.get('author')
    content = request.json.get('content')
    
    if not author or not content:
        return jsonify({'error': 'Author and content are required'}), 400
    
    # Get session ID
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO messages (author, content, session_id) VALUES (?, ?, ?)",
              (author, content, session['user_id']))
    conn.commit()
    message_id = c.lastrowid
    
    # Get the newly created message
    c.execute("SELECT id, author, content, date_created FROM messages WHERE id = ?", (message_id,))
    row = c.fetchone()
    message = {
        'id': row['id'],
        'author': row['author'],
        'content': row['content'],
        'date': datetime.strptime(row['date_created'], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y'),
        'can_delete': True  # Since the user just created it
    }
    conn.close()
    
    return jsonify(message)

@app.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 403
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if the message belongs to the current user
    c.execute("SELECT session_id FROM messages WHERE id = ?", (message_id,))
    result = c.fetchone()
    
    if not result:
        return jsonify({'error': 'Message not found'}), 404
    
    if result['session_id'] != session['user_id']:
        return jsonify({'error': 'Not authorized to delete this message'}), 403
    
    c.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/admin')
def admin():
    # In a real application, you would add authentication here
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, author, content, date_created, session_id FROM messages ORDER BY date_created DESC")
    messages = []
    for row in c.fetchall():
        messages.append({
            'id': row['id'],
            'author': row['author'],
            'content': row['content'],
            'date': datetime.strptime(row['date_created'], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y at %H:%M'),
            'session_id': row['session_id']
        })
    conn.close()
    return render_template('admin.html', messages=messages)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
