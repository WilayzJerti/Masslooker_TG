import subprocess
import sys
import os

# Создаем необходимые директории, если они не существуют
os.makedirs("data", exist_ok=True)
os.makedirs("sessions", exist_ok=True)
os.makedirs("web_admin/templates", exist_ok=True)

def main():
    """
    Запускает два процесса: веб-сервер Flask и основной воркер для масслукинга.
    """
    print("Запуск проекта Masslooker...")
    print("Убедитесь, что вы установили все зависимости из requirements.txt: pip install -r requirements.txt")

    # Пути к скриптам
    worker_script = os.path.join('core', 'main.py')
    webapp_script = os.path.join('web_admin', 'app.py')

    # Запускаем основной воркер в отдельном процессе
    print("Запуск основного воркера...")
    worker_process = subprocess.Popen([sys.executable, worker_script])

    # Запускаем веб-панель в отдельном процессе
    print("Запуск веб-панели управления... Откройте http://127.0.0.1:5000 в браузере.")
    web_process = subprocess.Popen([sys.executable, webapp_script])

    try:
        # Ожидаем завершения процессов
        worker_process.wait()
        web_process.wait()
    except KeyboardInterrupt:
        print("\nОстановка всех процессов...")
        worker_process.terminate()
        web_process.terminate()
        print("Процессы успешно завершены.")

if __name__ == "__main__":
    main()