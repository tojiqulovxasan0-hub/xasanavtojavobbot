# =============================================================
#  control_bot.py
# =============================================================
import asyncio, logging, json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import config, storage, keyboards as kb
from helpers import admin_only, admin_strict, safe_send, do_broadcast
from helpers import fmt_list, safe_edit, safe_answer

log = logging.getLogger(__name__)
bot = Bot(token=config.BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())


class S(StatesGroup):
    add_group=State(); del_group=State()
    add_user=State();  del_user=State()
    import_group=State(); import_channel=State()
    bc_text=State();  bc_photo=State(); bc_video=State()
    bc_audio=State(); bc_file=State();  bc_link=State(); bc_confirm=State()
    tg_text=State();  tg_photo=State(); tg_video=State()
    tg_audio=State(); tg_file=State();  tg_confirm=State()
    edit_ar=State();  edit_welcome=State(); edit_goodbye=State()
    note_name=State(); note_text=State(); get_note=State(); del_note=State()
    flt_kw=State();   flt_reply=State(); del_flt=State()
    tag_uid=State();  tag_text=State();  del_tag=State()
    sch_target=State(); sch_time=State(); sch_text=State(); del_sch=State()
    add_bl=State();   del_bl=State()
    add_adm=State();  del_adm=State()
    dm_delay=State(); dm_limit=State(); bc_delay=State()
    t_user=State();   t_chat=State();   t_photo=State(); t_gstats=State()


# ── helpers ─────────────────────────────────────────────────
async def _home_text():
    g=storage.get_broadcast_targets(); u=storage.get_target_users()
    bl=storage.get_blacklist(); ad=storage.get_allowed_users()
    st=storage.get_stats(); ar=storage.get_auto_reply()
    wl=storage.get_welcome()["on"]
    _,rem=storage.check_dm_limit(config.DAILY_DM_LIMIT)
    arl=storage.get_auto_replied_users()
    return (
        f"🤖 <b>Userbot Boshqaruv Paneli</b>\n"
        f"{'─'*28}\n"
        f"📡 Guruhlar: <b>{len(g)}</b>   👤 Userlar: <b>{len(u)}</b>\n"
        f"🚫 Blacklist: <b>{len(bl)}</b>   👮 Adminlar: <b>{len(ad)}</b>\n"
        f"💬 AR log: <b>{len(arl)}</b> ta user\n"
        f"🔄 Auto-reply: {'✅' if ar else '❌'}   👋 Welcome: {'✅' if wl else '❌'}\n"
        f"📤 Yuborildi: <b>{st['sent']}</b>   ❌ Xato: <b>{st['failed']}</b>\n"
        f"🔄 AR: <b>{st['auto_replies']}</b>   🔍 Filter: <b>{st.get('filter_hits',0)}</b>\n"
        f"📆 Bugungi DM qolgan: <b>{rem}/{config.DAILY_DM_LIMIT}</b>"
    )


@dp.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    # Admin yoki sub-admin — to'liq panel
    if uid == config.ADMIN_ID or uid in storage.get_allowed_users():
        await state.clear()
        await safe_answer(msg, await _home_text(), reply_markup=kb.main_menu(), parse_mode="HTML")
    # Oddiy foydalanuvchi — user paneli (user_bot.py da handle qilinadi)
    # Bu yerda hech narsa qilmaymiz, user_bot.py o'z handlerida ishlaydi


@dp.callback_query(F.data == "back_main")
@admin_only
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(call.message, await _home_text(), reply_markup=kb.main_menu(), parse_mode="HTML")


# ── GURUHLAR ────────────────────────────────────────────────
@dp.callback_query(F.data == "menu_groups")
@admin_only
async def menu_groups(call: CallbackQuery):
    n=len(storage.get_broadcast_targets())
    await safe_edit(call.message, f"👥 <b>Broadcast Guruhlar ({n})</b>",
                    reply_markup=kb.groups_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "list_groups")
@admin_only
async def list_groups(call: CallbackQuery):
    g=storage.get_broadcast_targets()
    await safe_edit(call.message, f"📋 <b>Guruhlar ({len(g)}):</b>\n\n{fmt_list(g,'Hech narsa yo\'q')}",
                    reply_markup=kb.groups_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "add_group")
@admin_only
async def ask_add_group(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.add_group)
    await safe_edit(call.message,
        "➕ <b>Guruh/Kanal qo'shish</b>\n\n"
        "ID yoki username kiriting:\n"
        "• <code>-1001234567890</code>\n• <code>mychannel</code>",
        reply_markup=kb.cancel_btn(), parse_mode="HTML")

@dp.message(S.add_group)
@admin_only
async def do_add_group(msg: Message, state: FSMContext):
    await state.clear()
    val=msg.text.strip()
    if storage.add_broadcast_target(val):
        await safe_answer(msg, f"✅ Qo'shildi: <code>{val}</code>",
                          reply_markup=kb.groups_menu(), parse_mode="HTML")
    else:
        await safe_answer(msg, f"⚠️ Allaqachon bor: <code>{val}</code>",
                          reply_markup=kb.groups_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "del_group")
@admin_only
async def ask_del_group(call: CallbackQuery, state: FSMContext):
    g=storage.get_broadcast_targets()
    if not g: await call.answer("Ro'yxat bo'sh!", show_alert=True); return
    await state.set_state(S.del_group)
    await safe_edit(call.message, f"➖ O'chirish uchun ID:\n\n{fmt_list(g)}",
                    reply_markup=kb.cancel_btn(), parse_mode="HTML")

@dp.message(S.del_group)
@admin_only
async def do_del_group(msg: Message, state: FSMContext):
    await state.clear()
    val=msg.text.strip()
    if storage.remove_broadcast_target(val):
        await safe_answer(msg, f"🗑 O'chirildi: <code>{val}</code>",
                          reply_markup=kb.groups_menu(), parse_mode="HTML")
    else:
        await safe_answer(msg, f"❌ Topilmadi: <code>{val}</code>",
                          reply_markup=kb.groups_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "confirm_clear_groups")
@admin_strict
async def confirm_clear_groups(call: CallbackQuery):
    await safe_edit(call.message, "⚠️ Barcha guruhlarni o'chirishni istaysizmi?",
                    reply_markup=kb.confirm_action("clear_groups"))

@dp.callback_query(F.data == "yes_clear_groups")
@admin_strict
async def do_clear_groups(call: CallbackQuery):
    storage.clear_broadcast_targets()
    await call.answer("✅ Tozalandi", show_alert=True)
    await safe_edit(call.message, "🗑 Guruhlar tozalandi.", reply_markup=kb.groups_menu(), parse_mode="HTML")


# ── USERLAR ─────────────────────────────────────────────────
@dp.callback_query(F.data == "menu_users")
@admin_only
async def menu_users(call: CallbackQuery):
    n=len(storage.get_target_users())
    await safe_edit(call.message, f"👤 <b>Target Userlar ({n})</b>",
                    reply_markup=kb.users_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "list_users")
@admin_only
async def list_users(call: CallbackQuery):
    u=storage.get_target_users()
    text=fmt_list(u[:50],"Ro'yxat bo'sh")
    extra=f"\n\n<i>...va yana {len(u)-50} ta</i>" if len(u)>50 else ""
    await safe_edit(call.message, f"📋 <b>Target Userlar ({len(u)}):</b>\n\n{text}{extra}",
                    reply_markup=kb.users_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "add_user")
@admin_only
async def ask_add_user(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.add_user)
    await safe_edit(call.message,
        "➕ <b>User qo'shish</b>\n\nUsername, ID yoki +telefon:\n"
        "• <code>username</code>\n• <code>123456789</code>\n• <code>+998901234567</code>",
        reply_markup=kb.cancel_btn(), parse_mode="HTML")

@dp.message(S.add_user)
@admin_only
async def do_add_user(msg: Message, state: FSMContext):
    await state.clear()
    raw=msg.text.strip()
    if raw.startswith("+") or (raw.isdigit() and len(raw)>9):
        try:
            from helpers import userbot_client
            e=await userbot_client.get_entity(raw)
            val=e.username if e.username else e.id
            label=f"@{e.username}" if e.username else str(e.id)
        except Exception as ex:
            await safe_answer(msg, f"❌ Topilmadi: <code>{ex}</code>",
                              reply_markup=kb.users_menu(), parse_mode="HTML"); return
    else:
        val=raw.lstrip("@"); label=val

    if storage.add_target_user(val):
        await safe_answer(msg, f"✅ Qo'shildi: <code>{label}</code>",
                          reply_markup=kb.users_menu(), parse_mode="HTML")
    else:
        await safe_answer(msg, f"⚠️ Allaqachon bor: <code>{label}</code>",
                          reply_markup=kb.users_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "del_user")
@admin_only
async def ask_del_user(call: CallbackQuery, state: FSMContext):
    if not storage.get_target_users():
        await call.answer("Ro'yxat bo'sh!", show_alert=True); return
    await state.set_state(S.del_user)
    await safe_edit(call.message, "➖ O'chirish uchun username yoki ID:",
                    reply_markup=kb.cancel_btn())

@dp.message(S.del_user)
@admin_only
async def do_del_user(msg: Message, state: FSMContext):
    await state.clear()
    val=msg.text.strip().lstrip("@")
    if storage.remove_target_user(val):
        await safe_answer(msg, f"🗑 O'chirildi: <code>{val}</code>",
                          reply_markup=kb.users_menu(), parse_mode="HTML")
    else:
        await safe_answer(msg, f"❌ Topilmadi: <code>{val}</code>",
                          reply_markup=kb.users_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "confirm_clear_users")
@admin_strict
async def confirm_clear_users(call: CallbackQuery):
    await safe_edit(call.message, "⚠️ Barcha userlarni o'chirishni istaysizmi?",
                    reply_markup=kb.confirm_action("clear_users"))

@dp.callback_query(F.data == "yes_clear_users")
@admin_strict
async def do_clear_users(call: CallbackQuery):
    count=len(storage.get_target_users())
    storage.clear_target_users()
    await call.answer(f"🗑 {count} ta o'chirildi", show_alert=True)
    await safe_edit(call.message, f"🗑 <b>{count} ta user o'chirildi.</b>",
                    reply_markup=kb.users_menu(), parse_mode="HTML")

@dp.callback_query(F.data.in_({"import_from_group","import_from_channel"}))
@admin_only
async def ask_import(call: CallbackQuery, state: FSMContext):
    is_ch = call.data == "import_from_channel"
    await state.set_state(S.import_channel if is_ch else S.import_group)
    label = "Kanal" if is_ch else "Guruh"
    await safe_edit(call.message,
        f"📥 <b>{label} ID yoki username kiriting:</b>\n\nMisol: <code>-1001234567890</code>",
        reply_markup=kb.cancel_btn(), parse_mode="HTML")

@dp.message(S.import_group)
@dp.message(S.import_channel)
@admin_only
async def do_import(msg: Message, state: FSMContext):
    await state.clear()
    from helpers import userbot_client
    raw=msg.text.strip().lstrip("@")
    status=await msg.answer("⏳ A'zolar yuklanmoqda...")
    try: chat_id=int(raw)
    except: chat_id=raw
    added=skipped=bots=no_un=total=0
    try:
        async for p in userbot_client.iter_participants(chat_id):
            total+=1
            if p.bot: bots+=1; continue
            if storage.is_blacklisted(p.id): skipped+=1; continue
            val=p.username if p.username else p.id
            if storage.add_target_user(val): added+=1
            else: skipped+=1
            if not p.username: no_un+=1
            if total%100==0:
                try: await status.edit_text(f"⏳ {total} ta ko'rildi, {added} ta qo'shildi...")
                except: pass
        await status.edit_text(
            f"✅ <b>Import tugadi!</b>\n\n"
            f"👥 Jami: <b>{total}</b>  🤖 Botlar: <b>{bots}</b>\n"
            f"✔ Qo'shildi: <b>{added}</b>  ⏭ O'tkazildi: <b>{skipped}</b>\n"
            f"🔢 Username yo'q (ID bilan): <b>{no_un}</b>",
            reply_markup=kb.users_menu(), parse_mode="HTML")
    except Exception as e:
        await status.edit_text(
            f"❌ <b>Xato:</b> <code>{e}</code>\n\n• Userbot guruhda a'zo bo'lishi kerak",
            reply_markup=kb.users_menu(), parse_mode="HTML")


# ── BROADCAST ───────────────────────────────────────────────
@dp.callback_query(F.data == "menu_broadcast")
@admin_only
async def menu_broadcast(call: CallbackQuery):
    n=len(storage.get_broadcast_targets())
    await safe_edit(call.message,
        f"📡 <b>Broadcast</b> — {n} ta guruh/kanal\n\nNima yubormoqchisiz?",
        reply_markup=kb.broadcast_menu(), parse_mode="HTML")

_BC={"bc_text":(S.bc_text,"✏️ Matn yozing:"),"bc_photo":(S.bc_photo,"🖼 Rasm yuboring:"),
     "bc_video":(S.bc_video,"🎥 Video:"),"bc_audio":(S.bc_audio,"🎵 Audio:"),
     "bc_file":(S.bc_file,"📄 Fayl:"),"bc_link":(S.bc_link,"🔗 Havola/matn:")}

@dp.callback_query(F.data.in_(set(_BC)))
@admin_only
async def ask_bc(call: CallbackQuery, state: FSMContext):
    st,pr=_BC[call.data]
    await state.set_state(st); await state.update_data(bc_type=call.data[3:])
    await safe_edit(call.message, pr, reply_markup=kb.cancel_btn())

@dp.message(S.bc_text)
@dp.message(S.bc_link)
async def bc_text(msg: Message, state: FSMContext):
    await state.update_data(content=msg.text); await state.set_state(S.bc_confirm)
    n=len(storage.get_broadcast_targets())
    await safe_answer(msg,
        f"📡 Bu matnni <b>{n}</b> ta guruhga yuborasizmi?\n\n<i>{msg.text[:200]}</i>",
        reply_markup=kb.confirm_send("bc"), parse_mode="HTML")

@dp.message(S.bc_photo)
async def bc_photo(msg: Message, state: FSMContext):
    if not msg.photo: await safe_answer(msg,"❌ Rasm yuboring.",reply_markup=kb.cancel_btn()); return
    await state.update_data(content=msg.caption or "",file_id=msg.photo[-1].file_id,file_type="photo")
    await state.set_state(S.bc_confirm)
    await safe_answer(msg,f"📡 Rasmni <b>{len(storage.get_broadcast_targets())}</b> ta guruhga?",
                      reply_markup=kb.confirm_send("bc"),parse_mode="HTML")

@dp.message(S.bc_video)
async def bc_video(msg: Message, state: FSMContext):
    if not msg.video: await safe_answer(msg,"❌ Video yuboring.",reply_markup=kb.cancel_btn()); return
    await state.update_data(content=msg.caption or "",file_id=msg.video.file_id,file_type="video")
    await state.set_state(S.bc_confirm)
    await safe_answer(msg,f"📡 Videoni <b>{len(storage.get_broadcast_targets())}</b> ta guruhga?",
                      reply_markup=kb.confirm_send("bc"),parse_mode="HTML")

@dp.message(S.bc_audio)
async def bc_audio(msg: Message, state: FSMContext):
    if not msg.audio: await safe_answer(msg,"❌ Audio yuboring.",reply_markup=kb.cancel_btn()); return
    await state.update_data(content=msg.caption or "",file_id=msg.audio.file_id,file_type="audio")
    await state.set_state(S.bc_confirm)
    await safe_answer(msg,"📡 Audioni guruhlarga?",reply_markup=kb.confirm_send("bc"),parse_mode="HTML")

@dp.message(S.bc_file)
async def bc_file(msg: Message, state: FSMContext):
    if not msg.document: await safe_answer(msg,"❌ Fayl yuboring.",reply_markup=kb.cancel_btn()); return
    await state.update_data(content=msg.caption or "",file_id=msg.document.file_id,file_type="file")
    await state.set_state(S.bc_confirm)
    await safe_answer(msg,"📡 Faylni guruhlarga?",reply_markup=kb.confirm_send("bc"),parse_mode="HTML")

@dp.callback_query(F.data == "confirm_bc")
@admin_only
async def confirm_bc(call: CallbackQuery, state: FSMContext):
    data=await state.get_data(); await state.clear()
    targets=storage.get_broadcast_targets()
    if not targets:
        await safe_edit(call.message,"❌ Guruhlar ro'yxati bo'sh.",reply_markup=kb.main_menu()); return
    prog=await call.message.answer(f"📡 Broadcast boshlandi... 0/{len(targets)}")
    ok,fail=await do_broadcast(targets,data,prog)
    storage.inc_stat("sent",ok); storage.inc_stat("failed",fail)
    storage.add_broadcast_log({"time":datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "type":"broadcast","targets":len(targets),"ok":ok,"fail":fail})
    await safe_edit(prog,
        f"✅ <b>Broadcast tugadi!</b>\n✔ Yuborildi: <b>{ok}</b>\n✘ Xato: <b>{fail}</b>",
        reply_markup=kb.main_menu(), parse_mode="HTML")


# ── TARGET DM ───────────────────────────────────────────────
@dp.callback_query(F.data == "menu_target")
@admin_only
async def menu_target(call: CallbackQuery):
    n=len(storage.get_target_users())
    await safe_edit(call.message,f"🎯 <b>Target DM</b> — {n} ta user",
                    reply_markup=kb.target_menu(),parse_mode="HTML")

_TG={"tg_text":(S.tg_text,"✏️ Matn:"),"tg_photo":(S.tg_photo,"🖼 Rasm:"),
     "tg_video":(S.tg_video,"🎥 Video:"),"tg_audio":(S.tg_audio,"🎵 Audio:"),
     "tg_file":(S.tg_file,"📄 Fayl:")}

@dp.callback_query(F.data.in_(set(_TG)))
@admin_only
async def ask_tg(call: CallbackQuery, state: FSMContext):
    st,pr=_TG[call.data]; await state.set_state(st)
    await safe_edit(call.message,pr,reply_markup=kb.cancel_btn())

@dp.message(S.tg_text)
async def tg_text(msg: Message, state: FSMContext):
    await state.update_data(content=msg.text); await state.set_state(S.tg_confirm)
    n=len(storage.get_target_users())
    await safe_answer(msg,
        f"🎯 Bu matnni <b>{n}</b> ta userlarga?\n\n<i>{msg.text[:200]}</i>",
        reply_markup=kb.confirm_send("tg"),parse_mode="HTML")

@dp.message(S.tg_photo)
async def tg_photo(msg: Message, state: FSMContext):
    if not msg.photo: await safe_answer(msg,"❌ Rasm.",reply_markup=kb.cancel_btn()); return
    await state.update_data(content=msg.caption or "",file_id=msg.photo[-1].file_id,file_type="photo")
    await state.set_state(S.tg_confirm)
    await safe_answer(msg,f"🎯 Rasmni <b>{len(storage.get_target_users())}</b> ta userlarga?",
                      reply_markup=kb.confirm_send("tg"),parse_mode="HTML")

@dp.message(S.tg_video)
async def tg_video(msg: Message, state: FSMContext):
    if not msg.video: await safe_answer(msg,"❌ Video.",reply_markup=kb.cancel_btn()); return
    await state.update_data(content=msg.caption or "",file_id=msg.video.file_id,file_type="video")
    await state.set_state(S.tg_confirm)
    await safe_answer(msg,f"🎯 Videoni <b>{len(storage.get_target_users())}</b> ta userlarga?",
                      reply_markup=kb.confirm_send("tg"),parse_mode="HTML")

@dp.message(S.tg_audio)
async def tg_audio(msg: Message, state: FSMContext):
    if not msg.audio: await safe_answer(msg,"❌ Audio.",reply_markup=kb.cancel_btn()); return
    await state.update_data(content=msg.caption or "",file_id=msg.audio.file_id,file_type="audio")
    await state.set_state(S.tg_confirm)
    await safe_answer(msg,"🎯 Audioni userlarga?",reply_markup=kb.confirm_send("tg"),parse_mode="HTML")

@dp.message(S.tg_file)
async def tg_file(msg: Message, state: FSMContext):
    if not msg.document: await safe_answer(msg,"❌ Fayl.",reply_markup=kb.cancel_btn()); return
    await state.update_data(content=msg.caption or "",file_id=msg.document.file_id,file_type="file")
    await state.set_state(S.tg_confirm)
    await safe_answer(msg,"🎯 Faylni userlarga?",reply_markup=kb.confirm_send("tg"),parse_mode="HTML")

@dp.callback_query(F.data == "confirm_tg")
@admin_only
async def confirm_tg(call: CallbackQuery, state: FSMContext):
    data=await state.get_data(); await state.clear()
    users=storage.get_target_users()
    if not users:
        await safe_edit(call.message,"❌ Userlar ro'yxati bo'sh.",reply_markup=kb.main_menu()); return
    ok_lim,rem=storage.check_dm_limit(config.DAILY_DM_LIMIT)
    if not ok_lim:
        await safe_edit(call.message,
            f"⚠️ <b>Kunlik DM limit ({config.DAILY_DM_LIMIT}) to'ldi!</b>",
            reply_markup=kb.main_menu(),parse_mode="HTML"); return
    send_u=users[:rem]
    prog=await call.message.answer(f"🎯 DM boshlandi... 0/{len(send_u)}")
    ok=fail=0
    for i,u in enumerate(send_u):
        if storage.is_blacklisted(u): fail+=1; continue
        sent=await safe_send(u,
            text=data.get("content") or None,
            photo=data.get("file_id") if data.get("file_type")=="photo" else None,
            video=data.get("file_id") if data.get("file_type")=="video" else None,
            audio=data.get("file_id") if data.get("file_type")=="audio" else None,
            file=data.get("file_id")  if data.get("file_type")=="file"  else None)
        if sent: ok+=1
        else: fail+=1
        if (i+1)%10==0:
            try: await prog.edit_text(f"🎯 {i+1}/{len(send_u)} ✔{ok} ✘{fail}")
            except: pass
        await asyncio.sleep(config.DM_DELAY)
    storage.inc_dm_count(ok); storage.inc_stat("sent",ok); storage.inc_stat("failed",fail)
    storage.add_broadcast_log({"time":datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "type":"DM","targets":len(send_u),"ok":ok,"fail":fail})
    extra=f"\n⚠️ Limit: {len(users)-len(send_u)} ta o'tkazildi" if len(users)>len(send_u) else ""
    await safe_edit(prog,
        f"✅ <b>Target DM tugadi!</b>\n✔ {ok}\n✘ {fail}{extra}",
        reply_markup=kb.main_menu(),parse_mode="HTML")


# ── SUB-ADMINLAR ────────────────────────────────────────────
@dp.callback_query(F.data == "menu_admins")
@admin_strict
async def menu_admins(call: CallbackQuery):
    ad=storage.get_allowed_users()
    await safe_edit(call.message,
        f"👮 <b>Sub-Adminlar ({len(ad)})</b>\n\n"
        "Sub-adminlar botning asosiy funksiyalarini ishlatadi.\n"
        "Admin qo'shish/o'chirish — faqat siz.",
        reply_markup=kb.admins_menu(),parse_mode="HTML")

@dp.callback_query(F.data == "list_admins")
@admin_strict
async def list_admins(call: CallbackQuery):
    ad=storage.get_allowed_users()
    await safe_edit(call.message,
        f"📋 <b>Sub-Adminlar ({len(ad)}):</b>\n\n{fmt_list(ad,'Hech kim yo\'q')}",
        reply_markup=kb.admins_menu(),parse_mode="HTML")

@dp.callback_query(F.data == "add_admin")
@admin_strict
async def ask_add_admin(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.add_adm)
    await safe_edit(call.message,
        "➕ <b>Sub-admin qo'shish</b>\n\nUsername, ID yoki +telefon:",
        reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.add_adm)
@admin_strict
async def do_add_admin(msg: Message, state: FSMContext):
    await state.clear()
    raw=msg.text.strip()
    try:
        from helpers import userbot_client
        val=raw if raw.startswith("+") else raw.lstrip("@")
        try: val=int(val)
        except: pass
        e=await userbot_client.get_entity(val)
        uid=e.id; name=f"{e.first_name or ''} @{e.username or uid}"
    except Exception as ex:
        await safe_answer(msg,f"❌ Topilmadi: <code>{ex}</code>",
                          reply_markup=kb.admins_menu(),parse_mode="HTML"); return
    if uid==config.ADMIN_ID:
        await safe_answer(msg,"⚠️ Siz allaqachon asosiy adminsiz.",reply_markup=kb.admins_menu()); return
    if storage.add_allowed_user(uid):
        await safe_answer(msg,f"✅ Sub-admin qo'shildi: <b>{name}</b> (<code>{uid}</code>)",
                          reply_markup=kb.admins_menu(),parse_mode="HTML")
    else:
        await safe_answer(msg,f"⚠️ Allaqachon sub-admin: <code>{uid}</code>",
                          reply_markup=kb.admins_menu(),parse_mode="HTML")

@dp.callback_query(F.data == "del_admin")
@admin_strict
async def ask_del_admin(call: CallbackQuery, state: FSMContext):
    ad=storage.get_allowed_users()
    if not ad: await call.answer("Ro'yxat bo'sh!",show_alert=True); return
    await state.set_state(S.del_adm)
    await safe_edit(call.message,f"➖ O'chirish uchun ID:\n\n{fmt_list(ad)}",
                    reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.del_adm)
@admin_strict
async def do_del_admin(msg: Message, state: FSMContext):
    await state.clear()
    val=msg.text.strip()
    try: val=int(val)
    except: pass
    if storage.remove_allowed_user(val):
        await safe_answer(msg,f"🗑 O'chirildi: <code>{val}</code>",reply_markup=kb.admins_menu(),parse_mode="HTML")
    else:
        await safe_answer(msg,f"❌ Topilmadi: <code>{val}</code>",reply_markup=kb.admins_menu(),parse_mode="HTML")


# ── BROADCAST LOG ───────────────────────────────────────────
@dp.callback_query(F.data == "menu_bc_log")
@admin_only
async def menu_bc_log(call: CallbackQuery):
    logs=storage.get_broadcast_log()
    if not logs:
        text="<i>Broadcast tarixi bo'sh</i>"
    else:
        lines=[]
        for it in logs:
            tp="📡" if it["type"]=="broadcast" else "🎯"
            lines.append(f"{tp} <b>{it['time']}</b> — {it['type']}\n"
                         f"   Target: {it['targets']} | ✔{it['ok']} ✘{it['fail']}")
        text="📋 <b>Broadcast tarixi (oxirgi 20):</b>\n\n"+"\n\n".join(lines)
    await safe_edit(call.message,text,reply_markup=kb.back_main(),parse_mode="HTML")


async def start_bot():
    log.info("Control bot ishga tushdi.")
    await dp.start_polling(bot, allowed_updates=["message","callback_query"])
