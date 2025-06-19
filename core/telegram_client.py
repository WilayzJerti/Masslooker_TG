import os
from telethon import TelegramClient
import config

# Название файла сессии
SESSION_NAME = 'masslooker_session'
SESSION_PATH = os.path.join('sessions', SESSION_NAME)

def create_client():
    """
    Создает и возвращает экземпляр TelegramClient.
    Сессия сохраняется в папку /sessions, чтобы не проходить авторизацию каждый раз.
    """
    # Убедимся, что директория для сессий существует
    os.makedirs('sessions', exist_ok=True)
    
    print("Инициализация клиента Telegram...")
    client = TelegramClient(
        SESSION_PATH,
        config.API_ID,
        config.API_HASH,
        system_version="4.16.30-vxCUSTOM" # Параметр для совместимости
    )
    return client