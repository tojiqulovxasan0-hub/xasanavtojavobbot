# =============================================================
#  user_bot.py  —  Oddiy foydalanuvchilar uchun panel
#  Ular o'z target userlarini, guruhlarini boshqaradilar.
#  Admin ma'lumotlari ularga ko'rinmaydi.
# =============================================================
import asyncio, logging
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import config, storage
import keyboards as kb
from helpers import user_only, safe_send, safe_edit, safe_answer, fmt_list
from control_bot import dp

log = logging.getLogger(__name__)


class US(StatesGroup):
    add_target  = State()
    del_target  = State()
    add_group   = State()
    del_group   = State()
    send_text   = State()
    edit_ar     = State()


# ── /start — ro'yxatdan o'tish ──────────────────────────────
@dp.message(Command("start"))
async def user_start(msg: Message, state: FSMContext):
    uid  = msg.from_user.id
    name = f"{msg.from_user.first_name or ''} {msg.from_user.last_name or ''}".strip()
    un   = msg.from_user.username or ""

    # Admin va sub-adminlar control_bot.py da handle qilingan — bu yerda skip
    if uid == config.ADMIN_ID or uid in storage.get_allowed_users():
        return

    # Yangi foydalanuvchi
    if not storage.user_exists(uid):
        storage.create_user(uid, name, un)
        await safe_answer(msg,
            f"👋 Xush kelibsiz, <b>{name}</b>!\n\n"
            "Bu bot orqali siz:\n"
            "• Guruh va kanallaringizga broadcast yuborasiz\n"
            "• Userlar ro'yxatiga DM yuborasiz\n"
            "• Auto-reply o'rnatasiz\n\n"
            "Boshlash uchun quyidagi tugmalardan foydalaning:",
            reply_markup=_user_menu(), parse_mode="HTML")
    else:
        await safe_answer(msg, f"👋 Qayta xush kelibsiz, <b>{name}</b>!",
                          reply_markup=_user_menu(), parse_mode="HTML")


def _user_menu():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as B
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="👤 Target Userlar",   callback_data="u_targets"),
         B(text="👥 Guruhlarim",       callback_data="u_groups")],
        [B(text="📤 DM Yuborish",      callback_data="u_send_dm"),
         B(text="📡 Broadcast",        callback_data="u_broadcast")],
        [B(text="🔄 Auto-reply",       callback_data="u_autoreply"),
         B(text="📊 Statistika",       callback_data="u_stats")],
    ])

def _user_back():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as B
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🔙 Orqaga", callback_data="u_back")]
    ])

def _u_cancel():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as B
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="❌ Bekor", callback_data="u_back")]
    ])


@dp.callback_query(F.data == "u_back")
@user_only
async def u_back(call: CallbackQuery, state: FSMContext):
    await state.clear()
    uid  = call.from_user.id
    u    = storage.get_user(uid)
    name = u["name"] if u else "Foydalanuvchi"
    await safe_edit(call.message, f"👋 <b>{name}</b>, bosh menyu:",
                    reply_markup=_user_menu(), parse_mode="HTML")


# ── TARGET USERLAR ───────────────────────────────────────────
@dp.callback_query(F.data == "u_targets")
@user_only
async def u_targets(call: CallbackQuery):
    uid = call.from_user.id
    targets = storage.user_get_targets(uid)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as B
    kb_user = InlineKeyboardMarkup(inline_keyboard=[
        [B(text="➕ Qo'shish",  callback_data="u_add_target"),
         B(text="➖ O'chirish", callback_data="u_del_target")],
        [B(text="📋 Ro'yxat",   callback_data="u_list_targets")],
        [B(text="🔙 Orqaga",    callback_data="u_back")],
    ])
    await safe_edit(call.message,
        f"👤 <b>Sizning Target Userlaringiz ({len(targets)})</b>",
        reply_markup=kb_user, parse_mode="HTML")

@dp.callback_query(F.data == "u_list_targets")
@user_only
async def u_list_targets(call: CallbackQuery):
    targets = storage.user_get_targets(call.from_user.id)
    text = fmt_list(targets[:50], "Hech narsa yo'q")
    if len(targets) > 50: text += f"\n<i>...va yana {len(targets)-50} ta</i>"
    await safe_edit(call.message,
        f"📋 <b>Target Userlar ({len(targets)}):</b>\n\n{text}",
        reply_markup=_user_back(), parse_mode="HTML")

@dp.callback_query(F.data == "u_add_target")
@user_only
async def u_ask_add_target(call: CallbackQuery, state: FSMContext):
    await state.set_state(US.add_target)
    await safe_edit(call.message,
        "➕ Username yoki ID kiriting:\n• <code>username</code>\n• <code>123456789</code>",
        reply_markup=_u_cancel(), parse_mode="HTML")

@dp.message(US.add_target)
@user_only
async def u_do_add_target(msg: Message, state: FSMContext):
    await state.clear()
    val = msg.text.strip().lstrip("@")
    if storage.user_add_target(msg.from_user.id, val):
        await safe_answer(msg, f"✅ Qo'shildi: <code>{val}</code>",
                          reply_markup=_user_back(), parse_mode="HTML")
    else:
        await safe_answer(msg, f"⚠️ Allaqachon bor: <code>{val}</code>",
                          reply_markup=_user_back(), parse_mode="HTML")

@dp.callback_query(F.data == "u_del_target")
@user_only
async def u_ask_del_target(call: CallbackQuery, state: FSMContext):
    await state.set_state(US.del_target)
    await safe_edit(call.message, "➖ O'chirish uchun username/ID:", reply_markup=_u_cancel())

@dp.message(US.del_target)
@user_only
async def u_do_del_target(msg: Message, state: FSMContext):
    await state.clear()
    val = msg.text.strip().lstrip("@")
    if storage.user_remove_target(msg.from_user.id, val):
        await safe_answer(msg, f"🗑 O'chirildi: <code>{val}</code>",
                          reply_markup=_user_back(), parse_mode="HTML")
    else:
        await safe_answer(msg, f"❌ Topilmadi: <code>{val}</code>",
                          reply_markup=_user_back(), parse_mode="HTML")


# ── GURUHLAR ─────────────────────────────────────────────────
@dp.callback_query(F.data == "u_groups")
@user_only
async def u_groups(call: CallbackQuery):
    uid = call.from_user.id
    groups = storage.user_get_groups(uid)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as B
    kb_grp = InlineKeyboardMarkup(inline_keyboard=[
        [B(text="➕ Qo'shish",  callback_data="u_add_group"),
         B(text="➖ O'chirish", callback_data="u_del_group")],
        [B(text="📋 Ro'yxat",   callback_data="u_list_groups")],
        [B(text="🔙 Orqaga",    callback_data="u_back")],
    ])
    await safe_edit(call.message,
        f"👥 <b>Sizning Guruhlaringiz ({len(groups)})</b>",
        reply_markup=kb_grp, parse_mode="HTML")

@dp.callback_query(F.data == "u_list_groups")
@user_only
async def u_list_groups(call: CallbackQuery):
    groups = storage.user_get_groups(call.from_user.id)
    await safe_edit(call.message,
        f"📋 <b>Guruhlar ({len(groups)}):</b>\n\n{fmt_list(groups, 'Hech narsa yo\'q')}",
        reply_markup=_user_back(), parse_mode="HTML")

@dp.callback_query(F.data == "u_add_group")
@user_only
async def u_ask_add_group(call: CallbackQuery, state: FSMContext):
    await state.set_state(US.add_group)
    await safe_edit(call.message,
        "➕ Guruh/kanal ID yoki username:\n• <code>-1001234567890</code>\n• <code>mychannel</code>",
        reply_markup=_u_cancel(), parse_mode="HTML")

@dp.message(US.add_group)
@user_only
async def u_do_add_group(msg: Message, state: FSMContext):
    await state.clear()
    val = msg.text.strip()
    if storage.user_add_group(msg.from_user.id, val):
        await safe_answer(msg, f"✅ Qo'shildi: <code>{val}</code>",
                          reply_markup=_user_back(), parse_mode="HTML")
    else:
        await safe_answer(msg, f"⚠️ Allaqachon bor: <code>{val}</code>",
                          reply_markup=_user_back(), parse_mode="HTML")

@dp.callback_query(F.data == "u_del_group")
@user_only
async def u_ask_del_group(call: CallbackQuery, state: FSMContext):
    await state.set_state(US.del_group)
    await safe_edit(call.message, "➖ O'chirish uchun ID:", reply_markup=_u_cancel())

@dp.message(US.del_group)
@user_only
async def u_do_del_group(msg: Message, state: FSMContext):
    await state.clear()
    val = msg.text.strip()
    if storage.user_remove_group(msg.from_user.id, val):
        await safe_answer(msg, f"🗑 O'chirildi: <code>{val}</code>",
                          reply_markup=_user_back(), parse_mode="HTML")
    else:
        await safe_answer(msg, f"❌ Topilmadi: <code>{val}</code>",
                          reply_markup=_user_back(), parse_mode="HTML")


# ── DM YUBORISH ──────────────────────────────────────────────
@dp.callback_query(F.data == "u_send_dm")
@user_only
async def u_send_dm(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    targets = storage.user_get_targets(uid)
    if not targets:
        await call.answer("Avval target userlar qo'shing!", show_alert=True); return
    await state.set_state(US.send_text)
    await state.update_data(mode="dm")
    await safe_edit(call.message,
        f"📤 <b>{len(targets)} ta userlarga DM</b>\n\nYuboriladigan matnni yozing:",
        reply_markup=_u_cancel(), parse_mode="HTML")

@dp.callback_query(F.data == "u_broadcast")
@user_only
async def u_broadcast(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    groups = storage.user_get_groups(uid)
    if not groups:
        await call.answer("Avval guruhlar qo'shing!", show_alert=True); return
    await state.set_state(US.send_text)
    await state.update_data(mode="broadcast")
    await safe_edit(call.message,
        f"📡 <b>{len(groups)} ta guruhga broadcast</b>\n\nYuboriladigan matnni yozing:",
        reply_markup=_u_cancel(), parse_mode="HTML")

@dp.message(US.send_text)
@user_only
async def u_do_send(msg: Message, state: FSMContext):
    data = await state.get_data()
    mode = data.get("mode", "dm")
    uid  = msg.from_user.id
    await state.clear()

    if mode == "dm":
        targets = storage.user_get_targets(uid)
        ok_lim, rem = storage.user_check_dm_limit(uid, config.DAILY_DM_LIMIT)
        if not ok_lim:
            await safe_answer(msg, f"⚠️ Kunlik DM limit ({config.DAILY_DM_LIMIT}) to'ldi!",
                              reply_markup=_user_back()); return
        send_list = targets[:rem]
        prog = await msg.answer(f"🎯 DM boshlandi... 0/{len(send_list)}")
        ok = fail = 0
        for i, t in enumerate(send_list):
            if storage.user_is_blacklisted(uid, t): fail += 1; continue
            sent = await safe_send(t, text=msg.text)
            if sent: ok += 1
            else: fail += 1
            if (i+1) % 10 == 0:
                try: await prog.edit_text(f"🎯 {i+1}/{len(send_list)} ✔{ok} ✘{fail}")
                except: pass
            await asyncio.sleep(config.DM_DELAY)
        storage.user_inc_dm(uid, ok)
        storage.user_inc_stat(uid, "sent", ok)
        storage.user_inc_stat(uid, "failed", fail)
        await safe_edit(prog,
            f"✅ <b>DM tugadi!</b>\n✔ {ok}\n✘ {fail}",
            reply_markup=_user_back(), parse_mode="HTML")

    else:  # broadcast
        groups = storage.user_get_groups(uid)
        prog = await msg.answer(f"📡 Broadcast... 0/{len(groups)}")
        ok, fail = await do_broadcast(groups, msg.text, prog)
        storage.user_inc_stat(uid, "sent", ok)
        storage.user_inc_stat(uid, "failed", fail)
        await safe_edit(prog,
            f"✅ <b>Broadcast tugadi!</b>\n✔ {ok}\n✘ {fail}",
            reply_markup=_user_back(), parse_mode="HTML")


# ── AUTO-REPLY ───────────────────────────────────────────────
@dp.callback_query(F.data == "u_autoreply")
@user_only
async def u_autoreply(call: CallbackQuery):
    uid = call.from_user.id
    u   = storage.get_user(uid)
    ar  = u.get("auto_reply_on", False) if u else False
    txt = u.get("auto_reply_text", "—") if u else "—"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as B
    kb_ar = InlineKeyboardMarkup(inline_keyboard=[
        [B(text=f"{'❌ O\'chir' if ar else '✅ Yoq'}",  callback_data="u_toggle_ar"),
         B(text="✏️ Matnni o'zgartir",                  callback_data="u_edit_ar")],
        [B(text="🔙 Orqaga", callback_data="u_back")],
    ])
    await safe_edit(call.message,
        f"🔄 <b>Auto-reply</b>\n\n"
        f"Holat: <b>{'✅ Yoqilgan' if ar else '❌ O\'chirilgan'}</b>\n"
        f"Matn: <i>{txt[:100]}</i>",
        reply_markup=kb_ar, parse_mode="HTML")

@dp.callback_query(F.data == "u_toggle_ar")
@user_only
async def u_toggle_ar(call: CallbackQuery):
    uid = call.from_user.id
    u   = storage.get_user(uid)
    cur = u.get("auto_reply_on", False) if u else False
    storage.update_user(uid, auto_reply_on=not cur)
    await call.answer(f"Auto-reply: {'✅ Yoqildi' if not cur else '❌ O\'chirildi'}", show_alert=True)
    await u_autoreply(call)

@dp.callback_query(F.data == "u_edit_ar")
@user_only
async def u_ask_edit_ar(call: CallbackQuery, state: FSMContext):
    await state.set_state(US.edit_ar)
    await safe_edit(call.message, "✏️ Yangi auto-reply matni yozing:", reply_markup=_u_cancel())

@dp.message(US.edit_ar)
@user_only
async def u_do_edit_ar(msg: Message, state: FSMContext):
    await state.clear()
    storage.update_user(msg.from_user.id, auto_reply_text=msg.text)
    await safe_answer(msg, f"✅ Yangilandi:\n<i>{msg.text}</i>",
                      reply_markup=_user_back(), parse_mode="HTML")


# ── STATISTIKA ───────────────────────────────────────────────
@dp.callback_query(F.data == "u_stats")
@user_only
async def u_stats(call: CallbackQuery):
    uid = call.from_user.id
    u   = storage.get_user(uid)
    if not u:
        await call.answer("Ma'lumot topilmadi.", show_alert=True); return
    st  = u.get("stats", {})
    _, rem = storage.user_check_dm_limit(uid, config.DAILY_DM_LIMIT)
    await safe_edit(call.message,
        f"📊 <b>Sizning statistikangiz</b>\n{'─'*24}\n"
        f"👤 Ism: <b>{u['name']}</b>\n"
        f"🆔 ID: <code>{u['id']}</code>\n"
        f"📅 Qo'shilgan: <b>{u.get('joined','?')}</b>\n\n"
        f"📡 Guruhlar: <b>{len(u.get('broadcast_targets',[]))}</b>\n"
        f"👤 Target userlar: <b>{len(u.get('target_users',[]))}</b>\n\n"
        f"📤 Yuborildi: <b>{st.get('sent',0)}</b>\n"
        f"❌ Xato: <b>{st.get('failed',0)}</b>\n"
        f"📆 Bugungi DM qolgan: <b>{rem}/{config.DAILY_DM_LIMIT}</b>",
        reply_markup=_user_back(), parse_mode="HTML")


# do_broadcast import (circular import oldini olish uchun local)
async def do_broadcast(targets, text, prog_msg=None):
    from helpers import do_broadcast as _bc
    return await _bc(targets, text, prog_msg)
