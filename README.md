# Masslooking Telegram Stories (Masslooking App)

**Русская версия - [RU](https://github.com/WilayzJerti/Masslooker_TG/blob/main/README.ru.md)**

This is a Python program for masslooking with a multi-account function, proxy connection, and a web admin panel.

![изображение](https://github.com/user-attachments/assets/77efc520-7fd9-43de-80c9-144f455f8619)


## 🚀 How does it work?

*The program uses the Telethon library to log in under a Telegram account. The admin panel is implemented using Flask*

First, the program searches for your target audience by your keywords, saves users with stories in `targets.txt `, and then in an endless loop, it will start viewing their stories **at a preset speed** using the accounts you added. You can monitor the process in the Logs section and **add new accounts without stopping the program.**.

## 📦 Project structure
```
masslooker/
├── core/                   # Here is the core of logic. 
│   ├── __init__.py
│   ├── main.py             # The main script that controls the entire process.
│   ├── target_manager.py   # A module for searching for the target audience (group search, participant parsing, checking for stories).
│   ├── telegram_worker.py  # A class for interacting with a single Telegram account (connecting, viewing stories).
│   └── utils.py            # Auxiliary functions such as logging settings and speed control.
├── data/                   # A folder for storing data.
│   ├── app.db              # SQLite database for storing accounts, settings, and job status. (It will be created automatically)
│   ├── masslooker.log      # A file with job logs. (It will be created automatically)
│   └── targets.txt         # A file with a list of user IDs for viewing stories. (It will be created automatically)
├── sessions/               # Folder for session files (will be created automatically)
├── web_admin/              # Everything related to the web dashboard
│   ├── __init__.py
│   ├── app.py              # Flash application for the admin panel.
│   └── templates/
│       └── index.html      # HTML template for the interface
├── run.py                  # A simple script for running a worker and a web server.
└── requirements.txt        # A list of required libraries for installation.
```

## ⚙️ Installation and configuration

**1. Clone the repository:**
``` bash
git clone https://github.com/WilayzJerti/Masslooker_TG
```
**2. Install the dependencies:**
``` bash
pip install -r requirements.txt
```
**3. Run the script to run the program:** 
``` bash
python run.py
```
**4. Configure it via the web dashboard:**

- Open the address in the browser http://127.0.0.1:5000.
- Add your first Telegram account using the received `api_id` and `api_hash'. **If you are using a proxy, specify it in the appropriate field.**
- After adding the account, return to the console where it is running run.py . Upon first authorization, Telethon will ask you to enter a confirmation code, and then, possibly, a password for two-factor authentication. **This only needs to be done once, then the session will be saved.**
- In the web dashboard, set keywords to search for an audience. (*for example, marketing, cryptocurrencies, design*).
- Click the "Запустить" button.   

## ⚠️ Attention!

- Use is at **your own** risk. Excessive activity may lead to *temporary* or **permanent** restrictions on the part of Telegram.

- Do not share **your**`API_ID`, `API_HASH` and the `.session` **file with anyone**.

## 📑 TODO

1. Make anti-ban protection, imitation of a human.
2. Expand the logger, make it more detailed
3. Add analytics to the admin panel (how many stories were viewed, how many groups were found, etc.)
