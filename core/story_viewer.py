import asyncio
import random
import time
from telethon.tl.functions.stories import ReadStoriesRequest, GetUserStoriesRequest
from telethon.tl.types import InputUser
from telethon.errors.rpcerrorlist import FloodWaitError, UserIsBlockedError, PeerIdInvalidError

async def view_stories_for_targets(client, targets):
    """
    Основная функция для просмотра историй.

    :param client: Экземпляр TelegramClient.
    :param targets: Список юзернеймов или ID для просмотра.
    """
    print(f"Загружено {len(targets)} целей для просмотра историй.")
    viewed_count = 0
    
    for i, target_username in enumerate(targets, 1):
        print("-" * 20)
        print(f"Обработка цели {i}/{len(targets)}: {target_username}")
        
        try:
            # Получаем сущность пользователя (полную информацию о нем)
            entity = await client.get_entity(target_username)
            
            # Запрашиваем активные истории пользователя
            user_stories = await client(GetUserStoriesRequest(user_id=entity.id))
            
            # Получаем ID только непросмотренных историй
            story_ids = [
                story.id for story in user_stories.stories 
                if not story.close_friends and not story.viewed
            ]

            if not story_ids:
                print(f"У пользователя {target_username} нет новых историй для просмотра.")
                continue

            print(f"Найдено {len(story_ids)} новых историй. Просматриваем...")

            # Отмечаем все найденные истории как просмотренные
            # max_id - это последняя история, которую нужно просмотреть.
            await client(ReadStoriesRequest(
                user_id=entity.id,
                max_id=max(story_ids)
            ))
            
            viewed_count += 1
            print(f"✅ Успешно просмотрены истории для {target_username}")

        except (ValueError, PeerIdInvalidError):
            print(f"❌ Не удалось найти пользователя: {target_username}. Пропускаем.")
        except UserIsBlockedError:
            print(f"❌ Вы заблокированы пользователем: {target_username}. Пропускаем.")
        except FloodWaitError as e:
            # Если Telegram просит подождать, мы ждем указанное время
            print(f"❗️ Получен FloodWaitError. Ждем {e.seconds} секунд...")
            time.sleep(e.seconds + 5) # Добавляем 5 секунд на всякий случай
        except Exception as e:
            # Ловим все остальные возможные ошибки
            print(f"❗️ Произошла непредвиденная ошибка для {target_username}: {e}")
        
        finally:
            # Делаем случайную задержку между запросами, чтобы имитировать поведение человека
            # и снизить риск блокировки
            delay = random.uniform(10, 25)
            print(f"Пауза на {delay:.2f} секунд...")
            await asyncio.sleep(delay)
            
    print("-" * 20)
    print(f"Завершено. Успешно просмотрены истории у {viewed_count} пользователей.")