"""Настройки WAIP SHOP. Измени значения и сохрани файл."""

# 1. Токен от @BotFather
BOT_TOKEN = "8878110137:AAFZFjXNJMjRNe6uSVKU7gOrAwT4WgEFWo0"
OWNER_ID = "9292798672"  # Telegram ID владельца бота

# 2. Реквизиты / username для подарков Stars
PAYMENT_DETAILS = "@mukhammad_im"
STARS_GIFT_USERNAME = "mukhammad_im"  # без @

# 3. CryptoBot API Token (от @CryptoBot → Crypto Pay → Create App)
CRYPTOBOT_TOKEN = "680189:AA5RlEvQTW9TRoOxdUjtmJhIpBNUBW53ZqY"

# 4. Канал для обязательной подписки (без @)
CHANNEL_USERNAME = "@waiprussia"
CHANNEL_ID = -1004323576792

# 5. Web App — HTTPS URL (обязательно для Mini App)
WEBAPP_URL = "https://waip.onrender.com"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = 8080

# 6. APK игры (GitHub Release direct link на .apk)
# Пример: "https://github.com/USER/REPO/releases/download/v1.0/game.apk"
# Или страница релизов: бот/webapp откроют ссылку для скачивания
APK_DOWNLOAD_URL = "https://github.com/mehrona201103-jpg/waip/commits/waip"
APK_BUTTON_TITLE = "📥 Скачать игру (APK)"

# 7. Показывать премиум-эмодзи Telegram
PREMIUM_EMOJI = True

# 8. MySQL игрового сервера
GAME_DB_HOST = "178.130.53.37"
GAME_DB_PORT = 3306
GAME_DB_USER = "gs365018"
GAME_DB_PASSWORD = "Zy1HZ8OiIVca"
GAME_DB_NAME = "gs365018"

GAME_ACCOUNT_TABLE = "accounts"
GAME_NICK_COLUMN = "name"
GAME_LEVEL_COLUMN = "level"
GAME_ADMIN_COLUMN = "admin"
GAME_MONEY_COLUMN = "money"
GAME_SKIN_COLUMN = "skin"
GAME_PASSWORD_COLUMN = "password"

# 9. Прайс-лист
CATALOG = {
    "level": {
        "title": "⭐ Приобрести ЛВЛ",
        "icon": "star",
        "products": [
            {"id": "lvl1",  "title": "+1 уровень",   "kind": "level", "units": 1,  "price": 50},
            {"id": "lvl5",  "title": "+5 уровней",   "kind": "level", "units": 5,  "price": 200},
            {"id": "lvl10", "title": "+10 уровней",  "kind": "level", "units": 10, "price": 350},
        ],
    },
    "admin": {
        "title": "🛡 Приобрести админку",
        "icon": "lock",
        "products": [
            {"id": "adm1", "title": "Админка 1 уровня", "kind": "admin", "units": 1, "price": 100},
            {"id": "adm2", "title": "Админка 2 уровня", "kind": "admin", "units": 2, "price": 250},
            {"id": "adm3", "title": "Админка 3 уровня", "kind": "admin", "units": 3, "price": 500},
        ],
    },
    "skin": {
        "title": "🧍 Скины",
        "icon": "user",
        "products": [
            {"id": "skin_admin", "title": "Скин админа (ID 122)", "kind": "skin", "units": 122, "price": 500},
        ],
    },
    "money": {
        "title": "💰 Приобрести валюту",
        "icon": "money",
        "products": [
            {"id": "cash100k", "title": "100 000 игровой валюты", "kind": "money", "units": 100000,  "price": 100},
            {"id": "cash500k", "title": "500 000 игровой валюты", "kind": "money", "units": 500000,  "price": 400},
            {"id": "cash1m",   "title": "1 000 000 игровой валюты", "kind": "money", "units": 1000000, "price": 700},
        ],
    },
    "password": {
        "title": "🔑 Сброс пароля",
        "icon": "lock",
        "products": [
            {"id": "pwd_reset", "title": "Сброс пароля аккаунта", "kind": "password", "units": 1, "price": 50},
        ],
    },
}
