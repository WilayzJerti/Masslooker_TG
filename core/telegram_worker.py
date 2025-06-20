#import asyncio
import socks
from telethon import TelegramClient
from telethon.tl.functions.stories import ReadStoriesRequest
from telethon.errors import UserDeactivatedBanError, SessionPasswordNeededError
from urllib.parse import urlparse

from utils import SESSIONS_DIR, setup_logging

logger = setup_logging()

class TelegramWorker:
    """
    Класс для управления одним Telegram-аккаунтом.
    Включает подключение, отключение и просмотр историй.
    """
    def __init__(self, account_info: dict):
        self.phone = account_info['phone']
        self.api_id = account_info['api_id']
        self.api_hash = account_info['api_hash']
        self.proxy_str = account_info.get('proxy')
        self.session_path = str(SESSIONS_DIR / f"{self.phone}.session")
        self.client = None
        self.status = "DISCONNECTED"

    def _parse_proxy(self):
        """Парсит строку прокси в формат, понятный Telethon."""
        if not self.proxy_str:
            return None
        
        try:
            parsed = urlparse(self.proxy_str)
            proxy_type_map = {
                'socks5': socks.SOCKS5,
                'socks4': socks.SOCKS4,
                'http': socks.HTTP,
            }
            proxy_type = proxy_type_map.get(parsed.scheme.lower())
            if not proxy_type:
                logger.error(f"[{self.phone}] Неподдерживаемый тип прокси: {parsed.scheme}")
                return None

            return (proxy_type, parsed.hostname, parsed.port, True, parsed.username, parsed.password)
        except Exception as e:
            logger.error(f"[{self.phone}] Ошибка парсинга прокси '{self.proxy_str}': {e}")
            return None

    async def connect(self):
        """Устанавливает соединение с Telegram."""
        if self.client and self.client.is_connected():
            logger.info(f"[{self.phone}] Аккаунт уже подключен.")
            return True

        proxy = self._parse_proxy()
        
        self.client = TelegramClient(self.session_path, self.api_id, self.api_hash, proxy=proxy)
        
        try:
            logger.info(f"[{self.phone}] Попытка подключения...")
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.warning(f"[{self.phone}] Аккаунт не авторизован. Требуется ручная авторизация.")
                # При первой авторизации Telethon запросит номер, код и пароль 2FA в консоли.
                await self.client.send_code_request(self.phone)
                try:
                    await self.client.sign_in(self.phone, input(f'Введите код для {self.phone}: '))
                except SessionPasswordNeededError:
                    await self.client.sign_in(password=input(f'Введите пароль 2FA для {self.phone}: '))
            
            me = await self.client.get_me()
            logger.info(f"[{self.phone}] Успешное подключение как {me.first_name} (@{me.username})")
            self.status = "CONNECTED"
            return True

        except UserDeactivatedBanError:
            logger.error(f"[{self.phone}] АККАУНТ ЗАБЛОКИРОВАН!")
            self.status = "BANNED"
            return False
        except Exception as e:
            logger.error(f"[{self.phone}] Ошибка подключения: {e}")
            self.status = f"ERROR: {e}"
            return False

    async def disconnect(self):
        """Отключает клиента."""
        if self.client and self.client.is_connected():
            await self.client.disconnect()
            logger.info(f"[{self.phone}] Аккаунт отключен.")
        self.status = "DISCONNECTED"

    async def view_stories(self, target_id: int):
        """
        Просматривает все доступные истории указанного пользователя.
        """
        if not self.client or not self.client.is_connected():
            logger.warning(f"[{self.phone}] Невозможно просмотреть истории, клиент не подключен.")
            return False
        
        try:
            # Получаем пользователя/канал, чтобы получить его story-объект
            peer = await self.client.get_entity(target_id)
            if not peer or not hasattr(peer, 'stories_max_id') or not peer.stories_max_id:
                # logger.info(f"[{self.phone}] У пользователя {target_id} нет активных историй.")
                return False
                
            # Читаем все истории до максимального ID
            await self.client(ReadStoriesRequest(
                user_id=peer,
                max_id=peer.stories_max_id
            ))
            logger.info(f"[{self.phone}] -> Просмотрены истории пользователя {target_id}")
            return True
        except ValueError:
            logger.warning(f"[{self.phone}] Не удалось найти пользователя с ID {target_id}. Возможно, неверный ID.")
            return False
        except Exception as e:
            logger.error(f"[{self.phone}] Ошибка при просмотре историй для {target_id}: {e}")
            return False
