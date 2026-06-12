# =============================================================
#  userbot.py  —  Telethon userbot
# =============================================================
import logging
import asyncio
import base64
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

import config
import storage

log = logging.getLogger(__name__)
replied_users: set[int] = set()

# Session yaratish: Railway da SESSION_STRING ishlatiladi, local da fayl
if config.SESSION_STRING:
    # Base64 dan decode qilib StringSession ga beramiz
    try:
        raw_bytes = base64.b64decode(config.SESSION_STRING)
        # SQLite session faylini vaqtinchalik yozamiz
        session_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            config.SESSION_NAME + ".session"
        )
        with open(session_path, "wb") as f:
            f.write(raw_bytes)
        log.info("Session fayl SESSION_STRING dan yaratildi.")
    except Exception as e:
        log.error(f"SESSION_STRING decode xato: {e}")

client = TelegramClient(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), config.SESSION_NAME),
    config.API_ID,
    config.API_HASH
)


@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def on_private(event):
    sender_id = event.sender_id
    if sender_id == config.ADMIN_ID:
        return
    if storage.is_blacklisted(sender_id):
        return

    text = (event.raw_text or "").lower().strip()

    # --- Admin filtrlari ---
    filters = storage.get_filters()
    for kw, reply in filters.items():
        if kw in text:
            try:
                await client.send_message(sender_id, reply)
                storage.inc_stat("filter_hits")
                log.info(f"Filter '{kw}': {sender_id}")
            except Exception as e:
                log.error(f"Filter xato: {e}")
            return

    # --- Admin auto-reply ---
    if storage.get_auto_reply() and sender_id not in replied_users:
        replied_users.add(sender_id)
        # Har 1000 ta bo'lganda eski yozuvlarni tozala
        if len(replied_users) > 1000:
            replied_users.clear()
        try:
            reply_text = storage.get_auto_reply_text()
            await client.send_message(sender_id, reply_text)
            storage.inc_stat("auto_replies")
            try:
                entity = await client.get_entity(sender_id)
                name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                username = entity.username or ""
            except Exception:
                name = str(sender_id); username = ""
            storage.add_auto_replied_user(sender_id, name, username)
            log.info(f"Auto-reply (admin): {sender_id} ({name})")
        except Exception as e:
            log.error(f"Auto-reply xato: {e}")
            replied_users.discard(sender_id)


@client.on(events.ChatAction())
async def on_chat_action(event):
    try:
        if event.user_joined or event.user_added:
            wl = storage.get_welcome()
            if not wl["on"]:
                return
            user = await event.get_user()
            if not user or user.bot:
                return
            name = f"{user.first_name or ''} {user.last_name or ''}".strip() or str(user.id)
            await event.reply(wl["text"].replace("{name}", name))

        elif event.user_left or event.user_kicked:
            gb = storage.get_goodbye()
            if not gb["on"]:
                return
            user = await event.get_user()
            if not user or user.bot:
                return
            name = f"{user.first_name or ''} {user.last_name or ''}".strip() or str(user.id)
            await event.reply(gb["text"].replace("{name}", name))
    except Exception as e:
        log.error(f"ChatAction xato: {e}")


async def start_userbot():
    await client.start(phone=config.PHONE)
    me = await client.get_me()
    log.info(f"Userbot: {me.first_name} (ID: {me.id})")
    print(f"✅ Userbot faol — {me.first_name} (@{me.username})")
