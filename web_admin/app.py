import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Определение путей относительно текущего файла
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, '..', 'data', 'app.db')
LOG_FILE = os.path.join(BASE_DIR, '..', 'data', 'masslooker.log')
TARGETS_FILE = os.path.join(BASE_DIR, '..', 'data', 'targets.txt')

app = Flask(__name__)
app.secret_key = os.urandom(24)

def get_db_connection():
    """Создает соединение с базой данных."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Главная страница панели управления."""
    conn = get_db_connection()
    accounts = conn.execute('SELECT * FROM accounts').fetchall()
    settings_raw = conn.execute('SELECT * FROM settings').fetchall()
    conn.close()

    settings = {item['key']: item['value'] for item in settings_raw}

    # Чтение лог-файла
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = f.readlines()[-50:] # Показываем последние 50 строк
    except FileNotFoundError:
        logs = ["Лог-файл пока не создан."]

    # Чтение файла целей
    try:
        with open(TARGETS_FILE, 'r', encoding='utf-8') as f:
            targets_count = len(f.readlines())
    except FileNotFoundError:
        targets_count = 0

    return render_template('index.html', accounts=accounts, settings=settings, logs=logs, targets_count=targets_count)

@app.route('/add_account', methods=['POST'])
def add_account():
    """Добавляет новый аккаунт в БД."""
    phone = request.form['phone']
    api_id = request.form['api_id']
    api_hash = request.form['api_hash']
    proxy = request.form['proxy']

    if not phone or not api_id or not api_hash:
        flash('Поля "Телефон", "API ID" и "API Hash" обязательны!', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO accounts (phone, api_id, api_hash, proxy) VALUES (?, ?, ?, ?)',
                     (phone, int(api_id), api_hash, proxy))
        conn.commit()
        flash('Аккаунт успешно добавлен!', 'success')
    except sqlite3.IntegrityError:
        flash(f'Аккаунт с номером {phone} уже существует.', 'error')
    except ValueError:
        flash('API ID должен быть числом.', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete_account/<int:id>', methods=['POST'])
def delete_account(id):
    """Удаляет аккаунт из БД."""
    conn = get_db_connection()
    conn.execute('DELETE FROM accounts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Аккаунт удален.', 'success')
    return redirect(url_for('index'))

@app.route('/toggle_worker', methods=['POST'])
def toggle_worker():
    """Переключает статус воркера (запущен/остановлен)."""
    conn = get_db_connection()
    current_status = conn.execute("SELECT value FROM settings WHERE key = 'worker_status'").fetchone()['value']
    new_status = 'stopped' if current_status == 'running' else 'running'
    conn.execute("UPDATE settings SET value = ? WHERE key = 'worker_status'", (new_status,))
    conn.commit()
    conn.close()
    flash(f'Статус воркера изменен на "{new_status}"', 'success')
    return redirect(url_for('index'))

@app.route('/save_settings', methods=['POST'])
def save_settings():
    """Сохраняет общие настройки."""
    rate_limit = request.form['rate_limit']
    keywords = request.form['keywords']
    
    conn = get_db_connection()
    try:
        conn.execute("UPDATE settings SET value = ? WHERE key = 'rate_limit_per_hour'", (int(rate_limit),))
        conn.execute("UPDATE settings SET value = ? WHERE key = 'search_keywords'", (keywords,))
        conn.commit()
        flash('Настройки успешно сохранены!', 'success')
    except ValueError:
        flash('Лимит скорости должен быть числом.', 'error')
    finally:
        conn.close()
        
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Перед первым запуском создаем БД
    if not os.path.exists(DB_FILE):
        print("База данных не найдена, инициализация...")
        from core.utils import initialize_database
        initialize_database()
        print("База данных создана.")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
