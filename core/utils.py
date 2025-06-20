import logging
import time
import asyncio
import sqlite3
from pathlib import Path

# --- Пути к файлам данных ---
DATA_DIR = Path(__file__).parent.parent / "data"
LOG_FILE = DATA_DIR / "masslooker.log"
DB_FILE = DATA_DIR / "app.db"
TARGETS_FILE = DATA_DIR / "targets.txt"
SESSIONS_DIR = Path(__file__).parent.parent / "sessions"

def setup_logging():
    """Настраивает систему логирования для записи в файл и вывода в консоль."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def initialize_database():
    """
    Инициализирует базу данных SQLite, создавая таблицы, если они не существуют.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Таблица для хранения аккаунтов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL UNIQUE,
            api_id INTEGER NOT NULL,
            api_hash TEXT NOT NULL,
            proxy TEXT, -- Формат: socks5://user:pass@host:port или http://host:port
            is_active BOOLEAN DEFAULT TRUE,
            status TEXT DEFAULT 'OK' -- Статус аккаунта: OK, BANNED, NEEDS_AUTH
        )
        ''')
        
        # Таблица для настроек
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        ''')
        
        # Устанавливаем значения по умолчанию
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('worker_status', 'stopped'))
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('rate_limit_per_hour', '300'))
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('search_keywords', 'новости, бизнес, технологии'))

        conn.commit()

class RateLimiter:
    """
    Простой класс для ограничения скорости выполнения асинхронных операций.
    """
    def __init__(self, rate_limit_per_hour: int):
        if rate_limit_per_hour <= 0:
            self.delay = 0
        else:
            self.delay = 3600.0 / rate_limit_per_hour
        self.last_call_time = 0
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Ограничитель скорости установлен: {rate_limit_per_hour} оп./час (задержка: {self.delay:.2f} сек.)")


    async def wait(self):
        """
        Ожидает необходимое время для соблюдения установленного лимита скорости.
        """
        if self.delay == 0:
            return

        while True:
            now = time.monotonic()
            elapsed = now - self.last_call_time
            if elapsed >= self.delay:
                self.last_call_time = now
                break
            
            sleep_time = self.delay - elapsed
            await asyncio.sleep(sleep_time)
