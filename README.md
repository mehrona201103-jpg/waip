# WAIP SHOP

Telegram-бот + **Mini App (Web App)** для продажи привилегий SA:MP / CRMP.

## Возможности
- Категории: ЛВЛ, Админка, Скины, Валюта, Сброс пароля
- Оплата: Telegram Stars (подарок) и CryptoBot (авто)
- Промокоды, модераторы, цены через админку
- Онбординг: подписка на канал → привязка ника
- **Web App** — полноценный магазин внутри Telegram

## Web App (Mini App)

1. Подними HTTPS на сервере (nginx + certbot **или** Cloudflare Tunnel / ngrok).
2. В `config.py` укажи:
   ```python
   WEBAPP_URL = "https://твой-домен.com"   # без слэша в конце
   WEBAPP_HOST = "0.0.0.0"
   WEBAPP_PORT = 8080
   ```
3. Проксируй HTTPS → `http://127.0.0.1:8080`
4. После регистрации ника в меню появится кнопка **🛒 WAIP SHOP**

Без `WEBAPP_URL` обычное меню работает как раньше, HTTP-сервер всё равно слушает порт.

### Пример nginx
```nginx
server {
  listen 443 ssl;
  server_name shop.example.com;
  # ssl_certificate ...;
  location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto https;
  }
}
```

### Быстрый тест через cloudflared
```bash
cloudflared tunnel --url http://127.0.0.1:8080
# скопируй https://....trycloudflare.com в WEBAPP_URL
```

## Установка
```bash
pip install -r requirements.txt
# отредактируй config.py
python3 main.py
```

## Важно
- `BOT_TOKEN`, MySQL, `CHANNEL_USERNAME`, `GAME_*_COLUMN`
- Пароль пишется в колонку `password` как plain text — если у мода хеш, напиши какой
