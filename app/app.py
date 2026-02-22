#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from flask import Flask, request, render_template, jsonify, url_for
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
        logging.FileHandler('app.log', encoding='utf-8')  # Запись в файл
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'notesdb'),
    'user': os.getenv('POSTGRES_USER', 'notesuser'),
    'password': os.getenv('POSTGRES_PASSWORD', 'notespassword'),
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Успешное подключение к бд")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Ошибка подключения к бд: {e}")
        return None

def init_database():
    conn = get_db_connection()
    if conn is None:
        logger.critical("Не удалось подключиться к бд при инициализации")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("Таблица notes успешно создана или уже существует")
            
            cur.execute("SELECT COUNT(*) FROM notes")
            count = cur.fetchone()[0]
            logger.info(f"В бд {count} заметок")
            
        conn.close()
        return True
    except psycopg2.Error as e:
        logger.error(f"Ошибка при инициализации бд: {e}")
        if conn:
            conn.close()
        return False

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM notes")
                count = cur.fetchone()[0]
            conn.close()
        else:
            count = 0
            logger.warning("Не удалось подключиться к БД для получения количества заметок")
    except Exception as e:
        logger.error(f"Ошибка при загрузке главной страницы: {e}")
        count = 0
    
    return render_template('index.html', notes_count=count)

@app.route('/add/<text>')
def add_note(text):
    if not text or len(text.strip()) == 0:
        logger.warning("Попытка добавить пустую заметку")
        return jsonify({
            'status': 'error',
            'message': 'Текст заметки не может быть пустым'
        }), 400
    
    conn = get_db_connection()
    if conn is None:
        logger.error("Не удалось подключиться к БД для добавления заметки")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка подключения к бд'
        }), 500
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO notes (text) VALUES (%s) RETURNING id",
                (text.strip(),)
            )
            note_id = cur.fetchone()[0]
            conn.commit()
            
            logger.info(f"Заметка добавлена успешно. ID: {note_id}, Текст: {text[:50]}...")
            
            return jsonify({
                'status': 'success',
                'message': 'Заметка успешно добавлена',
                'note_id': note_id,
                'text': text
            })
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Ошибка при добавлении заметки: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка при сохранении заметки в бд'
        }), 500
    finally:
        if conn:
            conn.close()

@app.route('/count')
def get_count():
    conn = get_db_connection()
    if conn is None:
        logger.error("Не удалось подключиться к БД для получения количества")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка подключения к бд',
            'count': 0
        }), 500
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM notes")
            count = cur.fetchone()[0]
            
            logger.info(f"Запрошено количество заметок: {count}")
            
            return jsonify({
                'status': 'success',
                'count': count,
                'message': f'Всего заметок: {count}'
            })
    except psycopg2.Error as e:
        logger.error(f"Ошибка при получении количества заметок: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Ошибка при чтении из бд',
            'count': 0
        }), 500
    finally:
        if conn:
            conn.close()

@app.route('/list')
def list_notes():
    format_type = request.args.get('format', 'json')
    
    conn = get_db_connection()
    if conn is None:
        logger.error("Не удалось подключиться к БД для получения списка заметок")
        if format_type == 'html':
            return "Ошибка подключения к бд", 500
        return jsonify({
            'status': 'error',
            'message': 'Ошибка подключения к бд',
            'notes': []
        }), 500
    
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT id, text, 
                       TO_CHAR(created_at, 'DD.MM.YYYY HH24:MI:SS') as created_at 
                FROM notes 
                ORDER BY created_at DESC
            """)
            notes = [dict(row) for row in cur.fetchall()]
            
            logger.info(f"Запрошен список заметок. Найдено: {len(notes)}")
            
            if format_type == 'html':
                html_response = "<h1>Список заметок</h1><ul>"
                for note in notes:
                    html_response += f"<li><b>{note['id']}:</b> {note['text']} <i>({note['created_at']})</i></li>"
                html_response += "</ul>"
                return html_response
            else:
                return jsonify({
                    'status': 'success',
                    'count': len(notes),
                    'notes': notes
                })
    except psycopg2.Error as e:
        logger.error(f"Ошибка при получении списка заметок: {e}")
        if format_type == 'html':
            return "Ошибка при чтении из бд", 500
        return jsonify({
            'status': 'error',
            'message': 'Ошибка при чтении из бд',
            'notes': []
        }), 500
    finally:
        if conn:
            conn.close()

@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"Страница не найдена: {request.path}")
    return jsonify({
        'status': 'error',
        'message': 'Страница не найдена'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Внутренняя ошибка сервера: {error}")
    return jsonify({
        'status': 'error',
        'message': 'Внутренняя ошибка сервера'
    }), 500

if __name__ == '__main__':
    if init_database():
        logger.info("Приложение успешно запущено")
        app.run(
            host=os.getenv('FLASK_RUN_HOST', '0.0.0.0'),
            port=int(os.getenv('FLASK_RUN_PORT', 5000)),
            debug=os.getenv('FLASK_ENV') == 'development'
        )
    else:
        logger.critical("Не удалось инициализировать бд. Приложение остановлено")
        exit(1)