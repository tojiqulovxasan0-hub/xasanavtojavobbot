import asyncio, logging, functools
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
import config

log = logging.getLogger(__name__)
userbot_client = None   # main.py dan inject qilinadi


# ── Ruxsat tekshiruvi ────────────────────────────────────────
def _allowed(uid: int) -> bool:
    import storage
    return uid == config.ADMIN_ID or uid in storage.get_allowed_users()

def _is_registered(uid: int) -> bool:
    import storage
    return storage.user_exists(uid)

def admin_only(func):
    @functools.wraps(func)
    async def w(obj, *a, **kw):
        uid = obj.from_user.id if hasattr(obj, "from_user") else 0
        if not _allowed(uid):
            if isinstance(obj, Message): await obj.answer("⛔ Ruxsat yo'q.")
            elif isinstance(obj, CallbackQuery): await obj.answer("⛔ Ruxsat yo'q.", show_alert=True)
            return
        return await func(obj, *a, **kw)
    return w

def admin_strict(func):
    @functools.wraps(func)
    async def w(obj, *a, **kw):
        uid = obj.from_user.id if hasattr(obj, "from_user") else 0
        if uid != config.ADMIN_ID:
            if isinstance(obj, Message): await obj.answer("⛔ Faqat asosiy admin.")
            elif isinstance(obj, CallbackQuery): await obj.answer("⛔ Faqat asosiy admin.", show_alert=True)
            return
        return await func(obj, *a, **kw)
    return w

def user_only(func):
    """Ro'yxatdan o'tgan foydalanuvchilar uchun."""
    @functools.wraps(func)
    async def w(obj, *a, **kw):
        uid = obj.from_user.id if hasattr(obj, "from_user") else 0
        if not _is_registered(uid) and not _allowed(uid):
            if isinstance(obj, Message): await obj.answer("⛔ Siz ro'yxatdan o'tmagansiz.\n/start bosing.")
            elif isinstance(obj, CallbackQuery): await obj.answer("⛔ Avval /start bosing.", show_alert=True)
            return
        return await func(obj, *a, **kw)
    return w


# ── Xavfsiz Telegram chaqiruvlari ────────────────────────────
async def safe_edit(msg, text: str, **kw):
    try:
        await msg.edit_text(text, **kw)
    except TelegramBadRequest as e:
        if "not modified" not in str(e).lower():
            log.debug(f"safe_edit: {e}")
    except TelegramNetworkError:
        await asyncio.sleep(2)
        try: await msg.edit_text(text, **kw)
        except Exception: pass
    except Exception as e:
        log.debug(f"safe_edit: {e}")

async def safe_answer(msg, text: str, **kw):
    try:
        return await msg.answer(text, **kw)
    except TelegramNetworkError:
        await asyncio.sleep(2)
        try: return await msg.answer(text, **kw)
        except Exception: pass
    except Exception as e:
        log.debug(f"safe_answer: {e}")


# ── Telethon yuborish ────────────────────────────────────────
async def safe_send(target, text=None, photo=None, video=None,
                    audio=None, file=None, _retry=0) -> bool:
    """
    Telethon orqali xabar yuborish.
    photo/video/audio/file — Telethon file path yoki bytes bo'lishi kerak.
    Aiogram file_id ISHLAMAYDI — faqat matn broadcast uchun ishlatiladi.
    """
    if userbot_client is None:
        log.error("userbot_client inject qilinmagan!")
        return False
    if _retry > 3:
        return False

    from telethon.errors import (
        FloodWaitError, UserPrivacyRestrictedError, UserIsBlockedError,
        InputUserDeactivatedError, PeerFloodError, RPCError, ChatWriteForbiddenError,
    )
    try:
        if photo:   await userbot_client.send_file(target, photo, caption=text)
        elif video: await userbot_client.send_file(target, video, caption=text)
        elif audio: await userbot_client.send_file(target, audio, caption=text)
        elif file:  await userbot_client.send_file(target, file,  caption=text)
        elif text:  await userbot_client.send_message(target, text)
        return True
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 5)
        return await safe_send(target, text, photo, video, audio, file, _retry+1)
    except PeerFloodError:
        await asyncio.sleep(60*(_retry+1))
        return await safe_send(target, text, photo, video, audio, file, _retry+1)
    except (UserPrivacyRestrictedError, UserIsBlockedError,
            InputUserDeactivatedError, ChatWriteForbiddenError):
        return False
    except RPCError as e:
        if "too many" in str(e).lower() or "flood" in str(e).lower():
            await asyncio.sleep(30*(_retry+1))
            return await safe_send(target, text, photo, video, audio, file, _retry+1)
        log.error(f"[{target}] RPC: {e}")
        return False
    except Exception as e:
        log.error(f"[{target}] Xato: {e}")
        return False


async def do_broadcast(targets: list, text: str, prog_msg=None) -> tuple:
    """Faqat matn broadcast. ok, fail qaytaradi."""
    ok = fail = 0
    for i, t in enumerate(targets):
        sent = await safe_send(t, text=text)
        if sent: ok += 1
        else:    fail += 1
        if prog_msg and (i+1) % 5 == 0:
            try: await prog_msg.edit_text(f"⏳ {i+1}/{len(targets)} — ✔{ok} ✘{fail}")
            except Exception: pass
        await asyncio.sleep(config.BROADCAST_DELAY)
    return ok, fail


def fmt_list(items: list, empty="Bo'sh") -> str:
    if not items: return f"<i>{empty}</i>"
    return "\n".join(f"  <b>{i+1}.</b> <code>{x}</code>" for i, x in enumerate(items))
