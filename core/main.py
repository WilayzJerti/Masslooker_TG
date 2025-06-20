import asyncio
import sqlite3
import random
import time

from utils import setup_logging, initialize_database, RateLimiter, DB_FILE, TARGETS_FILE
from telegram_worker import TelegramWorker
from target_manager import find_and_save_targets

logger = setup_logging()

class MainController:
    def __init__(self):
        self.workers = {}
        self.rate_limiter = None
        self.running = True
        self.last_target_search_time = 0

    def get_settings(self):
        """Загружает настройки из базы данных."""
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            settings = {row[0]: row[1] for row in cursor.execute("SELECT key, value FROM settings")}
            return settings

    def get_active_accounts(self):
        """Получает список активных аккаунтов из БД."""
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            accounts = cursor.execute("SELECT * FROM accounts WHERE is_active = TRUE").fetchall()
            return [dict(row) for row in accounts]

    async def run_target_search(self, connected_workers):
        """Запускает поиск новых целей, если пришло время."""
        # Искать новые цели раз в 6 часов
        if time.time() - self.last_target_search_time < 21600:
            return

        logger.info("Пришло время для поиска новых целей.")
        settings = self.get_settings()
        keywords = [kw.strip() for kw in settings.get('search_keywords', '').split(',')]
        
        if not keywords or not any(keywords):
            logger.warning("Ключевые слова для поиска не заданы в настройках.")
            return

        # Используем случайный рабочий аккаунт для поиска
        if connected_workers:
            searcher_worker = random.choice(list(connected_workers.values()))
            if searcher_worker.client and searcher_worker.client.is_connected():
                await find_and_save_targets(searcher_worker.client, keywords)
                self.last_target_search_time = time.time()
            else:
                logger.warning("Не удалось выбрать подключенный аккаунт для поиска целей.")
        else:
            logger.warning("Нет активных аккаунтов для запуска поиска целей.")

    async def main_loop(self):
        """Основной цикл работы программы."""
        initialize_database()
        logger.info("Инициализация основного контроллера.")

        while self.running:
            try:
                settings = self.get_settings()
                
                # Проверяем статус воркера в БД
                if settings.get('worker_status') != 'running':
                    if self.workers:
                        logger.info("Получена команда на остановку. Отключаем все аккаунты...")
                        for worker in self.workers.values():
                            await worker.disconnect()
                        self.workers.clear()
                    # logger.info("Воркер остановлен. Ожидание команды на запуск...")
                    await asyncio.sleep(5)
                    continue

                # Обновляем/инициализируем аккаунты
                accounts = self.get_active_accounts()
                if not accounts:
                    logger.warning("В базе данных нет активных аккаунтов. Добавьте аккаунты через веб-панель.")
                    await asyncio.sleep(15)
                    continue

                # Создаем и подключаем воркеры для новых аккаунтов
                for acc in accounts:
                    if acc['phone'] not in self.workers:
                        logger.info(f"Обнаружен новый аккаунт: {acc['phone']}. Создание воркера...")
                        self.workers[acc['phone']] = TelegramWorker(acc)
                        await self.workers[acc['phone']].connect()
                
                connected_workers = {p: w for p, w in self.workers.items() if w.status == "CONNECTED"}

                if not connected_workers:
                    logger.warning("Нет подключенных аккаунтов для работы. Проверьте логи на ошибки.")
                    await asyncio.sleep(15)
                    continue

                # Обновляем ограничитель скорости
                rate_limit = int(settings.get('rate_limit_per_hour', 300))
                if not self.rate_limiter or self.rate_limiter.delay != 3600.0 / rate_limit:
                     self.rate_limiter = RateLimiter(rate_limit)
                
                # Периодически запускаем поиск целей
                await self.run_target_search(connected_workers)

                # Читаем цели
                if not TARGETS_FILE.exists() or TARGETS_FILE.stat().st_size == 0:
                    logger.info("Файл с целями пуст. Ожидание результатов поиска...")
                    await asyncio.sleep(30)
                    continue

                with open(TARGETS_FILE, 'r') as f:
                    targets = [line.strip() for line in f if line.strip()]

                if not targets:
                    logger.info("Список целей пуст.")
                    await asyncio.sleep(30)
                    continue

                logger.info(f"Начинаем цикл просмотра историй. Целей в файле: {len(targets)}")

                # Бесконечно проходим по списку целей
                for target_id_str in targets:
                    # Повторно проверяем статус, чтобы можно было остановить в середине цикла
                    if self.get_settings().get('worker_status') != 'running':
                        logger.info("Процесс остановлен во время цикла просмотра.")
                        break

                    try:
                        target_id = int(target_id_str)
                    except ValueError:
                        logger.warning(f"Некорректный ID в файле targets.txt: '{target_id_str}'")
                        continue
                    
                    # Выбираем случайный аккаунт для просмотра
                    worker = random.choice(list(connected_workers.values()))

                    await self.rate_limiter.wait()
                    await worker.view_stories(target_id)
                
                logger.info("Полный цикл по файлу целей завершен. Начинаем заново через 10 секунд.")
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Критическая ошибка в основном цикле: {e}", exc_info=True)
                await asyncio.sleep(60) # Пауза перед следующей попыткой

if __name__ == "__main__":
    controller = MainController()
    try:
        asyncio.run(controller.main_loop())
    except KeyboardInterrupt:
        logger.info("Программа остановлена вручную.")
        controller.running = False
