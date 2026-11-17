"""HTTP API + static WebApp for WAIP SHOP (Telegram Mini App)."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from pathlib import Path
from urllib.parse import parse_qsl

from aiohttp import web

WEBAPP_DIR = Path(__file__).resolve().parent / "webapp"


def validate_init_data(init_data: str, bot_token: str) -> dict:
    if not init_data or not bot_token:
        raise ValueError("Нет initData — открой через кнопку бота")
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("Нет hash")
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, received_hash):
        raise ValueError("Неверная подпись initData")
    user_raw = parsed.get("user")
    if not user_raw:
        raise ValueError("Нет user в initData")
    user = json.loads(user_raw)
    if "id" not in user:
        raise ValueError("Нет user.id")
    return user


def create_app(ctx: dict) -> web.Application:
    app = web.Application(client_max_size=12 * 1024 * 1024)
    store = ctx["store"]
    bot_token = ctx["bot_token"]

    def auth_user(request: web.Request) -> dict:
        init_data = request.headers.get("X-Telegram-Init-Data") or request.query.get("initData") or ""
        return validate_init_data(init_data, bot_token)

    def live_catalog():
        catalog = {}
        for cat, sec in ctx["catalog"].items():
            products = []
            for p in sec["products"]:
                products.append({
                    "id": p["id"],
                    "title": p["title"],
                    "kind": p["kind"],
                    "units": p["units"],
                    "price": store.get_price(p["id"]),
                })
            catalog[cat] = {"title": sec["title"], "products": products}
        return catalog

    async def player_block(nick: str):
        if not nick:
            return None
        try:
            cfg = ctx["get_game_config"]()
            row = await ctx["asyncio"].to_thread(ctx["fetch_player"], nick, cfg)
            if not row:
                return None
            def g(col):
                return row.get(col) or row.get(col.lower())
            return {
                "level": g(cfg.level_col),
                "admin": g(cfg.admin_col),
                "skin": g(cfg.skin_col),
                "money": g(cfg.money_col),
            }
        except Exception:
            logging.exception("player_block")
            return None

    async def check_subscribed(uid: int) -> bool:
        fn = ctx.get("is_subscribed")
        if not fn:
            return True
        bot = ctx.get("bot")
        if not bot:
            return True
        try:
            return await fn(bot, uid)
        except Exception:
            logging.exception("check_subscribed")
            return False

    def channel_url():
        un = ctx.get("channel_username") or ""
        if un:
            return f"https://t.me/{un.lstrip('@')}"
        return None

    async def bootstrap(request: web.Request):
        try:
            user = auth_user(request)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=401)
        uid = int(user["id"])
        nick = store.get_nickname(uid)
        registered = store.is_registered(uid)
        subscribed = await check_subscribed(uid)
        player = await player_block(nick) if nick else None
        return web.json_response({
            "me": {
                "telegram_id": uid,
                "username": user.get("username"),
                "nickname": nick,
                "registered": registered,
                "player": player,
            },
            "subscribed": subscribed,
            "channel_url": channel_url(),
            "catalog": live_catalog(),
            "crypto_enabled": bool(ctx.get("cryptobot_token")),
            "stars_user": ctx.get("stars_user") or "mukhammad_im",
            "apk_url": ctx.get("apk_url") or None,
        })

    async def check_sub(request: web.Request):
        try:
            user = auth_user(request)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=401)
        subscribed = await check_subscribed(int(user["id"]))
        return web.json_response({"subscribed": subscribed})

    async def register(request: web.Request):
        try:
            user = auth_user(request)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=401)
        uid = int(user["id"])
        if not await check_subscribed(uid):
            return web.json_response({"error": "Сначала подпишись на канал"}, status=403)
        body = await request.json()
        nick = (body.get("nickname") or "").strip()
        import re
        if not re.fullmatch(r"[A-Za-z0-9_\[\]-]{3,24}", nick):
            return web.json_response({"error": "Неверный формат ника"}, status=400)
        exists = await ctx["asyncio"].to_thread(ctx["account_exists"], nick, ctx["get_game_config"]())
        if not exists:
            return web.json_response(
                {"error": f"Аккаунт «{nick}» не найден в базе сервера"},
                status=404,
            )
        store.set_nickname(uid, nick, registered=True)
        player = await player_block(nick)
        return web.json_response({
            "ok": True,
            "me": {
                "telegram_id": uid,
                "username": user.get("username"),
                "nickname": nick,
                "registered": True,
                "player": player,
            },
        })

    async def orders(request: web.Request):
        try:
            user = auth_user(request)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=401)
        items = store.latest(int(user["id"]), 20)
        return web.json_response({
            "orders": [
                {
                    "id": o["id"],
                    "item_title": o["item_title"],
                    "price": o["price"],
                    "status": o["status"],
                    "payment_method": o.get("payment_method"),
                    "created_at": o.get("created_at"),
                }
                for o in items
            ]
        })

    async def promo(request: web.Request):
        try:
            auth_user(request)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=401)
        body = await request.json()
        code = (body.get("code") or "").strip()
        p = store.get_promo(code)
        if not p:
            return web.json_response({"error": "Промокод не найден"}, status=400)
        if p["max_uses"] > 0 and p["used_count"] >= p["max_uses"]:
            return web.json_response({"error": "Лимит исчерпан"}, status=400)
        return web.json_response({"code": p["code"], "percent": p["percent"]})

    async def order_create(request: web.Request):
        try:
            user = auth_user(request)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=401)
        uid = int(user["id"])
        if not store.is_registered(uid):
            return web.json_response({"error": "Сначала регистрация"}, status=403)
        nick = store.get_nickname(uid)
        if not nick:
            return web.json_response({"error": "Ник не привязан"}, status=400)
        body = await request.json()
        product_id = body.get("product_id")
        method = body.get("payment_method") or "stars"
        if method not in ("stars", "crypto"):
            return web.json_response({"error": "Неверный способ оплаты"}, status=400)
        if method == "crypto" and not ctx.get("cryptobot_token"):
            return web.json_response({"error": "CryptoBot не настроен"}, status=400)
        item = store.product(product_id)
        if not item:
            return web.json_response({"error": "Товар не найден"}, status=404)
        if store.active(uid):
            return web.json_response({"error": "Есть незавершённый заказ"}, status=409)

        promo_code = body.get("promo")
        discount = 0
        final_price = item["price"]
        if promo_code:
            promo = store.get_promo(promo_code)
            if promo and (promo["max_uses"] == 0 or promo["used_count"] < promo["max_uses"]):
                discount = int(promo["percent"])
                final_price = max(1, int(item["price"] * (100 - discount) / 100))
            else:
                promo_code = None

        try:
            order = store.create(
                uid, nick, product_id, item,
                payment_method=method,
                promo_code=promo_code,
                discount=discount,
                final_price=final_price,
            )
            if promo_code:
                store.use_promo(promo_code)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=409)

        pay_url = None
        if method == "crypto":
            try:
                inv = await ctx["asyncio"].to_thread(ctx["create_crypto_invoice"], order)
                invoice_id = str(inv.get("invoice_id") or inv.get("invoiceId"))
                pay_url = inv.get("bot_invoice_url") or inv.get("pay_url") or inv.get("payUrl")
                store.set_crypto_invoice(order["id"], invoice_id)
            except Exception as e:
                logging.exception("web crypto")
                store.cancel(order["id"], uid)
                return web.json_response({"error": f"CryptoBot: {e}"}, status=502)

        bot = ctx.get("bot")
        if bot and method == "stars":
            try:
                stars = ctx.get("stars_user") or "mukhammad_im"
                await bot.send_message(
                    uid,
                    f"🛒 <b>Заказ #{order['id']} из WAIP SHOP</b>\n"
                    f"{item['title']} — <b>{final_price} ₽</b>\n\n"
                    f"Оплата Stars: подарок <b>@{stars}</b>, затем загрузи скрин в приложении "
                    f"или пришли фото <b>сюда в чат</b>.",
                )
            except Exception:
                logging.exception("notify stars")

        return web.json_response({
            "order_id": order["id"],
            "price": final_price,
            "status": order["status"],
            "pay_url": pay_url,
        })

    async def receipt_upload(request: web.Request):
        try:
            user = auth_user(request)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=401)
        uid = int(user["id"])
        reader = await request.multipart()
        order_id = None
        file_bytes = None
        filename = "receipt.jpg"
        content_type = "image/jpeg"

        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == "order_id":
                order_id = int((await part.text()).strip())
            elif part.name == "file":
                filename = part.filename or filename
                content_type = part.headers.get("Content-Type", content_type)
                file_bytes = await part.read(decode=False)

        if not order_id or not file_bytes:
            return web.json_response({"error": "Нужны order_id и файл"}, status=400)
        if len(file_bytes) > 10 * 1024 * 1024:
            return web.json_response({"error": "Файл слишком большой"}, status=400)

        order = store.get(order_id)
        if not order or order["telegram_id"] != uid:
            return web.json_response({"error": "Заказ не найден"}, status=404)
        if order["status"] != "awaiting_receipt":
            return web.json_response({"error": "Заказ не ждёт чек"}, status=409)

        bot = ctx.get("bot")
        if not bot:
            return web.json_response({"error": "Бот недоступен"}, status=503)

        from aiogram.types import BufferedInputFile
        is_pdf = "pdf" in (content_type or "") or filename.lower().endswith(".pdf")
        bio = BufferedInputFile(file_bytes, filename=filename)

        # send to user chat first to get file_id, or send directly to reviewers
        try:
            if is_pdf:
                msg = await bot.send_document(uid, bio, caption=f"Чек к заказу #{order_id}")
                file_id = msg.document.file_id
                unique_id = msg.document.file_unique_id
                kind = "document"
            else:
                msg = await bot.send_photo(uid, bio, caption=f"Чек к заказу #{order_id}")
                file_id = msg.photo[-1].file_id
                unique_id = msg.photo[-1].file_unique_id
                kind = "photo"
        except Exception as e:
            logging.exception("upload receipt to tg")
            return web.json_response({"error": f"Не удалось загрузить в Telegram: {e}"}, status=502)

        try:
            ok = store.submit_receipt(order_id, uid, file_id, unique_id, kind)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=409)
        if not ok:
            return web.json_response({"error": "Заказ уже изменился"}, status=409)

        # notify owner + moderators in bot chat (not web)
        from html import escape as esc
        o = store.get(order_id)
        caption = (
            f"🧾 <b>Заказ #{o['id']}</b> (из WebApp)\n"
            f"Товар: <b>{esc(o['item_title'])}</b>\n"
            f"Ник: <code>{esc(o['nickname'])}</code>\n"
            f"TG ID: <code>{o['telegram_id']}</code>\n"
            f"Сумма: <b>{o['price']} ₽</b>\n"
            f"Оплата: ✨ Stars\n"
            f"Статус: <code>review</code>"
        )
        # build review keyboard via callback data same as bot
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить и выдать", callback_data=f"ok:{order_id}")],
            [InlineKeyboardButton(text="❌ Отклонить чек", callback_data=f"no:{order_id}")],
        ])
        targets = {ctx.get("owner_id")}
        for m in store.list_moderators():
            targets.add(m["telegram_id"])
        for tid in targets:
            if not tid:
                continue
            try:
                if kind == "photo":
                    await bot.send_photo(tid, file_id, caption=caption, reply_markup=markup)
                else:
                    await bot.send_document(tid, file_id, caption=caption, reply_markup=markup)
            except Exception:
                logging.exception("notify reviewer %s", tid)

        return web.json_response({"ok": True, "order_id": order_id, "status": "review"})

    async def index(_request: web.Request):
        return web.FileResponse(WEBAPP_DIR / "index.html")

    async def health(_request: web.Request):
        return web.json_response({"ok": True, "service": "waip-shop"})

    app.router.add_get("/", index)
    app.router.add_get("/webapp", index)
    app.router.add_get("/webapp/", index)
    app.router.add_static("/webapp/", WEBAPP_DIR, show_index=False)
    app.router.add_get("/api/bootstrap", bootstrap)
    app.router.add_post("/api/check_sub", check_sub)
    app.router.add_post("/api/register", register)
    app.router.add_get("/api/orders", orders)
    app.router.add_post("/api/promo", promo)
    app.router.add_post("/api/order", order_create)
    app.router.add_post("/api/receipt", receipt_upload)
    app.router.add_get("/health", health)
    return app


async def start_web_server(ctx: dict, host: str, port: int):
    app = create_app(ctx)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logging.info("WebApp server on http://%s:%s", host, port)
    return runner
