import asyncio
import random
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel, User
from telethon.errors import FloodWaitError, ChannelsTooMuchError

from utils import TARGETS_FILE, setup_logging

logger = setup_logging()

async def find_and_save_targets(client, keywords: list[str]):
    """
    Ищет публичные группы по ключевым словам, парсит их участников
    и сохраняет тех, у кого есть истории, в файл targets.txt.
    
    :param client: Активный экземпляр TelegramClient.
    :param keywords: Список ключевых слов для поиска групп.
    """
    logger.info(f"Начинаем поиск новых целей по ключевым словам: {keywords}")
    
    try:
        # Загружаем существующих пользователей, чтобы не добавлять дубликаты
        existing_targets = set()
        if TARGETS_FILE.exists():
            with open(TARGETS_FILE, 'r') as f:
                existing_targets = {line.strip() for line in f}
        
        new_targets_found = 0

        for keyword in keywords:
            logger.info(f"Поиск групп по ключевому слову: '{keyword}'")
            try:
                result = await client(SearchRequest(q=keyword, limit=10))
                
                # Фильтруем только каналы и чаты
                groups = [chat for chat in result.chats if isinstance(chat, Channel)]
                
                if not groups:
                    logger.warning(f"По слову '{keyword}' не найдено публичных групп/каналов.")
                    continue

                # Выбираем одну случайную группу из найденных для парсинга
                group_to_parse = random.choice(groups)
                logger.info(f"Выбрана группа для парсинга: '{group_to_parse.title}' (ID: {group_to_parse.id})")

                async for user in client.iter_participants(group_to_parse, limit=500):
                    # Проверяем, что это пользователь, он не бот и у него есть истории
                    if isinstance(user, User) and not user.bot and user.stories_max_id:
                        if str(user.id) not in existing_targets:
                            with open(TARGETS_FILE, 'a') as f:
                                f.write(f"{user.id}\n")
                            existing_targets.add(str(user.id))
                            new_targets_found += 1
                            logger.info(f"Найдена новая цель: {user.first_name} (@{user.username}, ID: {user.id})")
                
                logger.info(f"Завершен парсинг группы '{group_to_parse.title}'.")
                # Задержка между обработкой ключевых слов, чтобы снизить риск FloodWait
                await asyncio.sleep(random.uniform(10, 20))

            except FloodWaitError as e:
                logger.warning(f"Слишком много запросов (FloodWaitError). Пауза на {e.seconds} секунд.")
                await asyncio.sleep(e.seconds)
            except ChannelsTooMuchError:
                logger.error("Аккаунт состоит в слишком большом количестве каналов и чатов. Невозможно выполнить поиск.")
                break
            except Exception as e:
                logger.error(f"Произошла ошибка при поиске по слову '{keyword}': {e}")
        
        logger.info(f"Поиск завершен. Найдено и добавлено новых целей: {new_targets_found}")

    except Exception as e:
        logger.error(f"Критическая ошибка в процессе поиска целей: {e}")
