import asyncio
import os
from core.telegram_client import create_client
from core.story_viewer import view_stories_for_targets

TARGETS_FILE = os.path.join('data', 'targets.txt')

def load_targets():
    """
    Загружает список целевых аккаунтов из файла data/targets.txt.
    Игнорирует пустые строки и строки, начинающиеся с '#'.
    """
    print(f"Загрузка целей из файла: {TARGETS_FILE}")
    if not os.path.exists(TARGETS_FILE):
        print(f"❌ Ошибка: Файл {TARGETS_FILE} не найден.")
        print("Пожалуйста, создайте его и добавьте юзернеймы для просмотра.")
        return []
        
    with open(TARGETS_FILE, 'r', encoding='utf-8') as f:
        targets = [
            line.strip() for line in f 
            if line.strip() and not line.strip().startswith('#')
        ]
    
    if not targets:
        print("⚠️ Предупреждение: Файл с целями пуст или не содержит валидных строк.")
    
    return targets

async def main():
    """
    Главная асинхронная функция приложения.
    """
    print("--- Запуск приложения для масслукинга историй ---")
    
    # 1. Загружаем список целей
    targets = load_targets()
    if not targets:
        return # Завершаем работу, если целей нет

    # 2. Создаем и настраиваем клиент
    client = create_client()

    # 3. Запускаем клиент и основную логику
    try:
        # Используем 'async with' для корректного подключения и отключения клиента
        async with client:
            print("✅ Клиент успешно подключен.")
            await view_stories_for_targets(client, targets)
    except Exception as e:
        print(f"❌ Критическая ошибка в работе приложения: {e}")
    finally:
        print("--- Работа приложения завершена ---")


if __name__ == "__main__":
    # Запускаем асинхронную функцию main
    asyncio.run(main())
