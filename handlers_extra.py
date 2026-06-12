# =============================================================
#  handlers_extra.py  —  Auto, AR-log, Notes, Filters, Tags,
#                         Schedule, Blacklist, Stats, Settings, Tools
# =============================================================
import asyncio, json, logging
from datetime import datetime, timedelta
from aiogram import F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

import config, storage, keyboards as kb
from helpers import admin_only, admin_strict, fmt_list, safe_edit, safe_answer
from control_bot import dp, bot, S

log = logging.getLogger(__name__)


# ── AUTO-FUNKSIYALAR ────────────────────────────────────────
async def _auto_text():
    ar=storage.get_auto_reply(); wl=storage.get_welcome(); gb=storage.get_goodbye()
    return (
        f"🤖 <b>Auto-funksiyalar</b>\n{'─'*28}\n"
        f"🔄 Auto-reply: <b>{'✅ Yoq' if ar else '❌ O\'ch'}</b>\n"
        f"<i>{storage.get_auto_reply_text()[:100]}</i>\n\n"
        f"👋 Welcome: <b>{'✅ Yoq' if wl['on'] else '❌ O\'ch'}</b>\n"
        f"<i>{wl['text'][:80]}</i>\n\n"
        f"👋 Goodbye: <b>{'✅ Yoq' if gb['on'] else '❌ O\'ch'}</b>\n"
        f"<i>{gb['text'][:80]}</i>"
    )

@dp.callback_query(F.data=="menu_auto")
@admin_only
async def menu_auto(call: CallbackQuery):
    await safe_edit(call.message,await _auto_text(),reply_markup=kb.auto_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="toggle_autoreply")
@admin_only
async def toggle_ar(call: CallbackQuery):
    cur=storage.get_auto_reply(); storage.set_auto_reply(not cur)
    await call.answer(f"Auto-reply: {'✅ Yoqildi' if not cur else '❌ O\'chirildi'}",show_alert=True)
    await safe_edit(call.message,await _auto_text(),reply_markup=kb.auto_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="edit_autoreply_text")
@admin_only
async def ask_ar(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.edit_ar)
    await safe_edit(call.message,
        f"✏️ Yangi auto-reply matni:\n\n<i>Hozirgi: {storage.get_auto_reply_text()}</i>",
        reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.edit_ar)
@admin_only
async def do_ar(msg: Message, state: FSMContext):
    await state.clear(); storage.set_auto_reply_text(msg.text)
    await safe_answer(msg,f"✅ Yangilandi:\n<i>{msg.text}</i>",reply_markup=kb.auto_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="toggle_welcome")
@admin_only
async def tog_wl(call: CallbackQuery):
    cur=storage.get_welcome()["on"]; storage.set_welcome(on=not cur)
    await call.answer(f"Welcome: {'✅' if not cur else '❌'}",show_alert=True)
    await safe_edit(call.message,await _auto_text(),reply_markup=kb.auto_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="edit_welcome_text")
@admin_only
async def ask_wl(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.edit_welcome)
    await safe_edit(call.message,
        f"✏️ Welcome matni (<code>{{name}}</code> = ism):\n\n<i>{storage.get_welcome()['text']}</i>",
        reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.edit_welcome)
@admin_only
async def do_wl(msg: Message, state: FSMContext):
    await state.clear(); storage.set_welcome(text=msg.text)
    await safe_answer(msg,f"✅ Yangilandi:\n<i>{msg.text}</i>",reply_markup=kb.auto_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="toggle_goodbye")
@admin_only
async def tog_gb(call: CallbackQuery):
    cur=storage.get_goodbye()["on"]; storage.set_goodbye(on=not cur)
    await call.answer(f"Goodbye: {'✅' if not cur else '❌'}",show_alert=True)
    await safe_edit(call.message,await _auto_text(),reply_markup=kb.auto_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="edit_goodbye_text")
@admin_only
async def ask_gb(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.edit_goodbye)
    await safe_edit(call.message,
        f"✏️ Goodbye matni (<code>{{name}}</code> = ism):\n\n<i>{storage.get_goodbye()['text']}</i>",
        reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.edit_goodbye)
@admin_only
async def do_gb(msg: Message, state: FSMContext):
    await state.clear(); storage.set_goodbye(text=msg.text)
    await safe_answer(msg,f"✅ Yangilandi:\n<i>{msg.text}</i>",reply_markup=kb.auto_menu(),parse_mode="HTML")


# ── AUTO-REPLY LOG ──────────────────────────────────────────
@dp.callback_query(F.data=="menu_ar_log")
@admin_only
async def menu_ar_log(call: CallbackQuery):
    users=storage.get_auto_replied_users()
    if not users:
        text="<i>Hali hech kim yozmagan</i>"
    else:
        lines=[]
        for u in users[:30]:
            un=f"@{u['username']}" if u.get("username") else "—"
            lines.append(
                f"👤 <b>{u.get('name','?')}</b> ({un})\n"
                f"   🆔 <code>{u['id']}</code> | 📩 {u.get('count',1)} ta xabar\n"
                f"   🕐 {u.get('last_seen','?')}"
            )
        text=(f"💬 <b>Avto-javob berilgan userlar ({len(users)}):</b>\n{'─'*28}\n\n"
              +"\n\n".join(lines))
        if len(users)>30: text+=f"\n\n<i>...va yana {len(users)-30} ta</i>"
    await safe_edit(call.message,text,reply_markup=kb.ar_log_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="confirm_clear_ar_log")
@admin_strict
async def confirm_clear_ar(call: CallbackQuery):
    await safe_edit(call.message,"⚠️ AR logini tozalashni istaysizmi?",
                    reply_markup=kb.confirm_action("clear_ar_log"))

@dp.callback_query(F.data=="yes_clear_ar_log")
@admin_strict
async def do_clear_ar(call: CallbackQuery):
    storage.clear_auto_replied_users()
    await call.answer("✅ AR log tozalandi",show_alert=True)
    await safe_edit(call.message,"🗑 AR log tozalandi.",reply_markup=kb.ar_log_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="dm_to_ar_log")
@admin_only
async def dm_to_ar_log(call: CallbackQuery):
    """AR log dagi barcha userlarga target userlarga qo'shadi."""
    users=storage.get_auto_replied_users()
    if not users:
        await call.answer("AR log bo'sh!",show_alert=True); return
    added=0
    for u in users:
        if storage.add_target_user(u["id"]): added+=1
    await call.answer(f"✅ {added} ta user target ro'yxatiga qo'shildi",show_alert=True)
    await safe_edit(call.message,
        f"✅ <b>AR log → Target list</b>\n\n{added} ta yangi user qo'shildi.",
        reply_markup=kb.ar_log_menu(),parse_mode="HTML")


# ── ESLATMALAR ──────────────────────────────────────────────
@dp.callback_query(F.data=="menu_notes")
@admin_only
async def menu_notes(call: CallbackQuery):
    await safe_edit(call.message,f"📝 <b>Eslatmalar ({len(storage.get_notes())} ta)</b>",
                    reply_markup=kb.notes_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="add_note")
@admin_only
async def ask_note_name(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.note_name)
    await safe_edit(call.message,"📝 Eslatma nomi kiriting:\nMisol: <code>manzil</code>",
                    reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.note_name)
@admin_only
async def got_note_name(msg: Message, state: FSMContext):
    await state.update_data(note_name=msg.text.strip().lower())
    await state.set_state(S.note_text)
    await safe_answer(msg,"📝 Matnini yozing:",reply_markup=kb.cancel_btn())

@dp.message(S.note_text)
@admin_only
async def got_note_text(msg: Message, state: FSMContext):
    data=await state.get_data(); await state.clear()
    storage.add_note(data["note_name"],msg.text)
    await safe_answer(msg,f"✅ Saqlandi: <code>{data['note_name']}</code>",
                      reply_markup=kb.notes_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="list_notes")
@admin_only
async def list_notes(call: CallbackQuery):
    notes=storage.get_notes()
    text="\n".join(f"  • <code>{k}</code>" for k in notes) if notes else "<i>Bo'sh</i>"
    await safe_edit(call.message,f"📋 <b>Eslatmalar:</b>\n\n{text}",
                    reply_markup=kb.notes_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="get_note")
@admin_only
async def ask_get_note(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.get_note)
    await safe_edit(call.message,"🔍 Nom kiriting:",reply_markup=kb.cancel_btn())

@dp.message(S.get_note)
@admin_only
async def do_get_note(msg: Message, state: FSMContext):
    await state.clear()
    name=msg.text.strip().lower(); text=storage.get_note(name)
    if text:
        await safe_answer(msg,f"📝 <b>{name}:</b>\n\n{text}",reply_markup=kb.notes_menu(),parse_mode="HTML")
    else:
        await safe_answer(msg,f"❌ Topilmadi: <code>{name}</code>",reply_markup=kb.notes_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="del_note")
@admin_only
async def ask_del_note(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.del_note)
    notes=storage.get_notes()
    text="\n".join(f"  • <code>{k}</code>" for k in notes) or "<i>Bo'sh</i>"
    await safe_edit(call.message,f"🗑 O'chirish uchun nom:\n\n{text}",
                    reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.del_note)
@admin_only
async def do_del_note(msg: Message, state: FSMContext):
    await state.clear(); name=msg.text.strip().lower()
    if storage.delete_note(name):
        await safe_answer(msg,f"🗑 O'chirildi: <code>{name}</code>",reply_markup=kb.notes_menu(),parse_mode="HTML")
    else:
        await safe_answer(msg,f"❌ Topilmadi: <code>{name}</code>",reply_markup=kb.notes_menu(),parse_mode="HTML")


# ── FILTRLAR ────────────────────────────────────────────────
@dp.callback_query(F.data=="menu_filters")
@admin_only
async def menu_filters(call: CallbackQuery):
    await safe_edit(call.message,
        f"🔍 <b>Filtrlar ({len(storage.get_filters())} ta)</b>\n\n"
        "Kalit so'z kelsa bot avtomatik javob beradi.",
        reply_markup=kb.filters_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="add_filter")
@admin_only
async def ask_flt_kw(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.flt_kw)
    await safe_edit(call.message,"🔍 Kalit so'z:\nMisol: <code>narx</code>",
                    reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.flt_kw)
@admin_only
async def got_flt_kw(msg: Message, state: FSMContext):
    await state.update_data(flt_kw=msg.text.strip().lower())
    await state.set_state(S.flt_reply)
    await safe_answer(msg,"💬 Javob matni:",reply_markup=kb.cancel_btn())

@dp.message(S.flt_reply)
@admin_only
async def got_flt_reply(msg: Message, state: FSMContext):
    data=await state.get_data(); await state.clear()
    storage.add_filter(data["flt_kw"],msg.text)
    await safe_answer(msg,
        f"✅ Filter: <code>{data['flt_kw']}</code> → <i>{msg.text[:80]}</i>",
        reply_markup=kb.filters_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="list_filters")
@admin_only
async def list_filters(call: CallbackQuery):
    f=storage.get_filters()
    text="\n".join(f"  • <code>{k}</code> → <i>{v[:50]}</i>" for k,v in f.items()) if f else "<i>Bo'sh</i>"
    await safe_edit(call.message,f"📋 <b>Filtrlar:</b>\n\n{text}",
                    reply_markup=kb.filters_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="del_filter")
@admin_only
async def ask_del_flt(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.del_flt)
    await safe_edit(call.message,"🗑 O'chirish uchun kalit so'z:",reply_markup=kb.cancel_btn())

@dp.message(S.del_flt)
@admin_only
async def do_del_flt(msg: Message, state: FSMContext):
    await state.clear(); kw=msg.text.strip().lower()
    if storage.delete_filter(kw):
        await safe_answer(msg,f"🗑 O'chirildi: <code>{kw}</code>",reply_markup=kb.filters_menu(),parse_mode="HTML")
    else:
        await safe_answer(msg,f"❌ Topilmadi: <code>{kw}</code>",reply_markup=kb.filters_menu(),parse_mode="HTML")


# ── TEGLAR ──────────────────────────────────────────────────
@dp.callback_query(F.data=="menu_tags")
@admin_only
async def menu_tags(call: CallbackQuery):
    await safe_edit(call.message,f"🏷 <b>Teglar ({len(storage.get_tags())} ta)</b>",
                    reply_markup=kb.tags_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="add_tag")
@admin_only
async def ask_tag(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.tag_uid)
    await safe_edit(call.message,"🏷 User ID kiriting:",reply_markup=kb.cancel_btn())

@dp.message(S.tag_uid)
@admin_only
async def got_tag_uid(msg: Message, state: FSMContext):
    try: uid=int(msg.text.strip())
    except: await safe_answer(msg,"❌ Raqamli ID."); return
    await state.update_data(tag_uid=uid); await state.set_state(S.tag_text)
    await safe_answer(msg,f"🏷 <code>{uid}</code> uchun teg:",reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.tag_text)
@admin_only
async def got_tag_text(msg: Message, state: FSMContext):
    data=await state.get_data(); await state.clear()
    storage.set_tag(data["tag_uid"],msg.text.strip())
    await safe_answer(msg,f"✅ <code>{data['tag_uid']}</code> → <b>{msg.text}</b>",
                      reply_markup=kb.tags_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="list_tags")
@admin_only
async def list_tags(call: CallbackQuery):
    tags=storage.get_tags()
    text="\n".join(f"  • <code>{uid}</code> → <b>{tag}</b>" for uid,tag in tags.items()) if tags else "<i>Bo'sh</i>"
    await safe_edit(call.message,f"📋 <b>Teglar:</b>\n\n{text}",reply_markup=kb.tags_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="del_tag")
@admin_only
async def ask_del_tag(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.del_tag)
    await safe_edit(call.message,"🗑 User ID:",reply_markup=kb.cancel_btn())

@dp.message(S.del_tag)
@admin_only
async def do_del_tag(msg: Message, state: FSMContext):
    await state.clear()
    try: uid=int(msg.text.strip())
    except: await safe_answer(msg,"❌ Raqamli ID."); return
    storage.remove_tag(uid)
    await safe_answer(msg,f"🗑 O'chirildi: <code>{uid}</code>",reply_markup=kb.tags_menu(),parse_mode="HTML")


# ── REJALASHTIRISH ──────────────────────────────────────────
@dp.callback_query(F.data=="menu_schedule")
@admin_only
async def menu_schedule(call: CallbackQuery):
    await safe_edit(call.message,f"⏰ <b>Rejalashtirilgan ({len(storage.get_scheduled())})</b>",
                    reply_markup=kb.schedule_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="add_schedule")
@admin_only
async def ask_sch_target(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.sch_target)
    await safe_edit(call.message,
        "⏰ <b>Qayerga yuboramiz?</b>\n\n"
        "• <code>broadcast</code> — barcha guruhlar\n"
        "• <code>target</code> — barcha userlar\n"
        "• Yoki ID: <code>-1001234567890</code>",
        reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.sch_target)
@admin_only
async def got_sch_target(msg: Message, state: FSMContext):
    await state.update_data(sch_target=msg.text.strip()); await state.set_state(S.sch_time)
    await safe_answer(msg,
        "⏰ <b>Qachon?</b>\n\n"
        "• <code>2026-06-13 09:00</code>\n"
        "• <code>+30m</code> (30 daqiqadan keyin)\n"
        "• <code>+2h</code> (2 soatdan keyin)",
        reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.sch_time)
@admin_only
async def got_sch_time(msg: Message, state: FSMContext):
    txt=msg.text.strip()
    try:
        if txt.startswith("+"):
            n=int(txt[1:-1]); u=txt[-1]
            d=timedelta(minutes=n) if u=="m" else timedelta(hours=n)
            send_at=(datetime.now()+d).strftime("%Y-%m-%d %H:%M")
        else:
            datetime.strptime(txt,"%Y-%m-%d %H:%M"); send_at=txt
    except:
        await safe_answer(msg,"❌ Format xato. Misol: <code>2026-06-13 09:00</code>",parse_mode="HTML"); return
    await state.update_data(sch_time=send_at); await state.set_state(S.sch_text)
    await safe_answer(msg,f"✅ Vaqt: <b>{send_at}</b>\n\n✏️ Matnini yozing:",
                      reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.sch_text)
@admin_only
async def got_sch_text(msg: Message, state: FSMContext):
    data=await state.get_data(); await state.clear()
    storage.add_scheduled({"target":data["sch_target"],"time":data["sch_time"],
                            "text":msg.text,"done":False})
    await safe_answer(msg,
        f"✅ <b>Rejalashtirildi!</b>\n"
        f"📍 <code>{data['sch_target']}</code>\n"
        f"⏰ <b>{data['sch_time']}</b>\n"
        f"✏️ <i>{msg.text[:100]}</i>",
        reply_markup=kb.schedule_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="list_schedule")
@admin_only
async def list_schedule(call: CallbackQuery):
    items=storage.get_scheduled()
    if not items: text="<i>Bo'sh</i>"
    else:
        lines=[f"<b>{i}.</b> {'✅' if it.get('done') else '⏳'} {it['time']} → <code>{it['target']}</code>\n"
               f"   <i>{it['text'][:60]}</i>" for i,it in enumerate(items)]
        text="📋 <b>Rejalashtirilganlar:</b>\n\n"+"\n\n".join(lines)
    await safe_edit(call.message,text,reply_markup=kb.schedule_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="del_schedule")
@admin_only
async def ask_del_sch(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.del_sch)
    await safe_edit(call.message,"🗑 Tartib raqam kiriting (0 dan boshlanadi):",reply_markup=kb.cancel_btn())

@dp.message(S.del_sch)
@admin_only
async def do_del_sch(msg: Message, state: FSMContext):
    await state.clear()
    try: idx=int(msg.text.strip())
    except: await safe_answer(msg,"❌ Raqam."); return
    if storage.remove_scheduled(idx):
        await safe_answer(msg,f"🗑 #{idx} bekor.",reply_markup=kb.schedule_menu(),parse_mode="HTML")
    else:
        await safe_answer(msg,f"❌ #{idx} topilmadi.",reply_markup=kb.schedule_menu(),parse_mode="HTML")


# ── QORA RO'YXAT ────────────────────────────────────────────
@dp.callback_query(F.data=="menu_blacklist")
@admin_only
async def menu_bl(call: CallbackQuery):
    await safe_edit(call.message,
        f"🚫 <b>Qora ro'yxat ({len(storage.get_blacklist())} ta)</b>\n\n"
        "Bu userlarga DM yuborilmaydi va auto-reply ishlamaydi.",
        reply_markup=kb.blacklist_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="add_blacklist")
@admin_only
async def ask_add_bl(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.add_bl)
    await safe_edit(call.message,"🚫 Username yoki ID:",reply_markup=kb.cancel_btn())

@dp.message(S.add_bl)
@admin_only
async def do_add_bl(msg: Message, state: FSMContext):
    await state.clear(); val=msg.text.strip().lstrip("@")
    if storage.add_to_blacklist(val):
        await safe_answer(msg,f"✅ Qo'shildi: <code>{val}</code>",reply_markup=kb.blacklist_menu(),parse_mode="HTML")
    else:
        await safe_answer(msg,f"⚠️ Bor: <code>{val}</code>",reply_markup=kb.blacklist_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="del_blacklist")
@admin_only
async def ask_del_bl(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.del_bl)
    await safe_edit(call.message,"🗑 O'chirish uchun username/ID:",reply_markup=kb.cancel_btn())

@dp.message(S.del_bl)
@admin_only
async def do_del_bl(msg: Message, state: FSMContext):
    await state.clear(); val=msg.text.strip().lstrip("@")
    if storage.remove_from_blacklist(val):
        await safe_answer(msg,f"✅ O'chirildi: <code>{val}</code>",reply_markup=kb.blacklist_menu(),parse_mode="HTML")
    else:
        await safe_answer(msg,f"❌ Topilmadi: <code>{val}</code>",reply_markup=kb.blacklist_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="list_blacklist")
@admin_only
async def list_bl(call: CallbackQuery):
    bl=storage.get_blacklist()
    await safe_edit(call.message,
        f"📋 <b>Qora ro'yxat ({len(bl)}):</b>\n\n{fmt_list(bl,'Bo\'sh')}",
        reply_markup=kb.blacklist_menu(),parse_mode="HTML")


# ── STATISTIKA ──────────────────────────────────────────────
async def _stats_text():
    st=storage.get_stats(); g=storage.get_broadcast_targets()
    u=storage.get_target_users(); bl=storage.get_blacklist()
    ad=storage.get_allowed_users(); notes=storage.get_notes()
    f=storage.get_filters(); tags=storage.get_tags()
    sch=storage.get_scheduled(); arl=storage.get_auto_replied_users()
    _,rem=storage.check_dm_limit(config.DAILY_DM_LIMIT)
    return (
        f"📊 <b>Statistika</b>\n{'─'*28}\n"
        f"📤 Yuborildi: <b>{st['sent']}</b>  ❌ Xato: <b>{st['failed']}</b>\n"
        f"🔄 Auto-reply: <b>{st['auto_replies']}</b>  🔍 Filter: <b>{st.get('filter_hits',0)}</b>\n\n"
        f"📡 Guruhlar: <b>{len(g)}</b>  👤 Userlar: <b>{len(u)}</b>\n"
        f"💬 AR log: <b>{len(arl)}</b>  🚫 Blacklist: <b>{len(bl)}</b>\n"
        f"👮 Adminlar: <b>{len(ad)}</b>  📝 Eslatmalar: <b>{len(notes)}</b>\n"
        f"🔍 Filtrlar: <b>{len(f)}</b>  🏷 Teglar: <b>{len(tags)}</b>\n"
        f"⏰ Rejalashtirilgan: <b>{len(sch)}</b>\n\n"
        f"📆 Bugungi DM qolgan: <b>{rem}/{config.DAILY_DM_LIMIT}</b>"
    )

@dp.callback_query(F.data.in_({"menu_stats","show_stats"}))
@admin_only
async def show_stats(call: CallbackQuery):
    await safe_edit(call.message,await _stats_text(),reply_markup=kb.stats_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="confirm_reset_stats")
@admin_strict
async def confirm_rst(call: CallbackQuery):
    await safe_edit(call.message,"⚠️ Statsni tozalashni istaysizmi?",
                    reply_markup=kb.confirm_action("reset_stats"))

@dp.callback_query(F.data=="yes_reset_stats")
@admin_strict
async def do_rst(call: CallbackQuery):
    storage.reset_stats(); await call.answer("✅ Tozalandi",show_alert=True)
    await safe_edit(call.message,await _stats_text(),reply_markup=kb.stats_menu(),parse_mode="HTML")


# ── SOZLAMALAR ──────────────────────────────────────────────
async def _settings_text():
    return (f"⚙️ <b>Sozlamalar</b>\n{'─'*28}\n"
            f"⏱ DM delay: <b>{config.DM_DELAY}s</b>\n"
            f"⏱ Broadcast delay: <b>{config.BROADCAST_DELAY}s</b>\n"
            f"📊 Kunlik DM limit: <b>{config.DAILY_DM_LIMIT}</b>")

@dp.callback_query(F.data=="menu_settings")
@admin_only
async def menu_settings(call: CallbackQuery):
    await safe_edit(call.message,await _settings_text(),reply_markup=kb.settings_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="set_dm_delay")
@admin_only
async def ask_dm_d(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.dm_delay)
    await safe_edit(call.message,
        f"⏱ DM delay (soniya):\n<i>Hozirgi: {config.DM_DELAY}s | Tavsiya: 10-30</i>",
        reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.dm_delay)
@admin_only
async def do_dm_d(msg: Message, state: FSMContext):
    await state.clear()
    try: config.DM_DELAY=int(msg.text.strip()); await safe_answer(msg,f"✅ DM delay: <b>{config.DM_DELAY}s</b>",reply_markup=kb.settings_menu(),parse_mode="HTML")
    except: await safe_answer(msg,"❌ Raqam kiriting.",reply_markup=kb.settings_menu())

@dp.callback_query(F.data=="set_dm_limit")
@admin_only
async def ask_dm_l(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.dm_limit)
    await safe_edit(call.message,
        f"📊 Kunlik DM limit:\n<i>Hozirgi: {config.DAILY_DM_LIMIT} | Tavsiya: 20-50</i>",
        reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.dm_limit)
@admin_only
async def do_dm_l(msg: Message, state: FSMContext):
    await state.clear()
    try: config.DAILY_DM_LIMIT=int(msg.text.strip()); await safe_answer(msg,f"✅ Limit: <b>{config.DAILY_DM_LIMIT}</b>",reply_markup=kb.settings_menu(),parse_mode="HTML")
    except: await safe_answer(msg,"❌ Raqam.",reply_markup=kb.settings_menu())

@dp.callback_query(F.data=="set_bc_delay")
@admin_only
async def ask_bc_d(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.bc_delay)
    await safe_edit(call.message,
        f"⏱ Broadcast delay (soniya):\n<i>Hozirgi: {config.BROADCAST_DELAY}s</i>",
        reply_markup=kb.cancel_btn(),parse_mode="HTML")

@dp.message(S.bc_delay)
@admin_only
async def do_bc_d(msg: Message, state: FSMContext):
    await state.clear()
    try: config.BROADCAST_DELAY=int(msg.text.strip()); await safe_answer(msg,f"✅ BC delay: <b>{config.BROADCAST_DELAY}s</b>",reply_markup=kb.settings_menu(),parse_mode="HTML")
    except: await safe_answer(msg,"❌ Raqam.",reply_markup=kb.settings_menu())

@dp.callback_query(F.data=="export_data")
@admin_only
async def export_data(call: CallbackQuery):
    try:
        raw=json.dumps(storage._load(),ensure_ascii=False,indent=2).encode("utf-8")
        f=BufferedInputFile(raw,filename="userbot_data.json")
        await bot.send_document(call.from_user.id,f,caption="📁 Userbot ma'lumotlari")
        await call.answer("✅ Yuborildi",show_alert=True)
    except Exception as e:
        await call.answer(f"❌ {e}",show_alert=True)


# ── VOSITALAR ───────────────────────────────────────────────
@dp.callback_query(F.data=="menu_tools")
@admin_only
async def menu_tools(call: CallbackQuery):
    await safe_edit(call.message,"🛠 <b>Userbot Vositalari</b>",
                    reply_markup=kb.tools_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="tool_userinfo")
@admin_only
async def ask_ui(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.t_user)
    await safe_edit(call.message,"👤 Username, ID yoki +telefon:",reply_markup=kb.cancel_btn())

@dp.message(S.t_user)
@admin_only
async def do_ui(msg: Message, state: FSMContext):
    await state.clear()
    from helpers import userbot_client
    raw=msg.text.strip()
    try:
        val=raw if raw.startswith("+") else raw.lstrip("@")
        try: val=int(val)
        except: pass
        e=await userbot_client.get_entity(val)
        tag=storage.get_tag(e.id)
        bl="🚫 Blacklistda" if storage.is_blacklisted(e.id) else "✅ Ruxsat bor"
        ar_users={u["id"] for u in storage.get_auto_replied_users()}
        ar_info="💬 AR yuborilgan" if e.id in ar_users else "—"
        await safe_answer(msg,
            f"👤 <b>User ma'lumoti</b>\n{'─'*24}\n"
            f"🆔 ID: <code>{e.id}</code>\n"
            f"👤 Ism: <b>{(getattr(e,'first_name','') or '')+' '+(getattr(e,'last_name','') or '')}</b>\n"
            f"📛 Username: @{getattr(e,'username','yo\'q') or 'yo\'q'}\n"
            f"🤖 Bot: {'Ha' if getattr(e,'bot',False) else 'Yo\'q'}\n"
            f"🏷 Teg: <b>{tag or '—'}</b>\n"
            f"📋 Holat: {bl}\n"
            f"💬 AR: {ar_info}",
            reply_markup=kb.tools_menu(),parse_mode="HTML")
    except Exception as ex:
        await safe_answer(msg,f"❌ <code>{ex}</code>",reply_markup=kb.tools_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="tool_chatinfo")
@admin_only
async def ask_ci(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.t_chat)
    await safe_edit(call.message,"💬 Guruh/kanal ID yoki username:",reply_markup=kb.cancel_btn())

@dp.message(S.t_chat)
@admin_only
async def do_ci(msg: Message, state: FSMContext):
    await state.clear()
    from helpers import userbot_client
    from telethon.tl.types import Channel, Chat
    val=msg.text.strip().lstrip("@")
    try:
        try: val=int(val)
        except: pass
        e=await userbot_client.get_entity(val)
        if isinstance(e,(Channel,Chat)):
            await safe_answer(msg,
                f"💬 <b>Chat ma'lumoti</b>\n{'─'*24}\n"
                f"🆔 ID: <code>{e.id}</code>\n"
                f"📛 Nomi: <b>{e.title}</b>\n"
                f"@{getattr(e,'username','—') or '—'}\n"
                f"👥 A'zolar: <b>{getattr(e,'participants_count','?')}</b>\n"
                f"📢 Kanal: {'Ha' if getattr(e,'broadcast',False) else 'Yo\'q'}\n"
                f"🔒 Mega: {'Ha' if getattr(e,'megagroup',False) else 'Yo\'q'}",
                reply_markup=kb.tools_menu(),parse_mode="HTML")
        else:
            await safe_answer(msg,f"ℹ️ Bu user: <code>{e.id}</code>",reply_markup=kb.tools_menu(),parse_mode="HTML")
    except Exception as ex:
        await safe_answer(msg,f"❌ <code>{ex}</code>",reply_markup=kb.tools_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="tool_my_groups")
@admin_only
async def t_groups(call: CallbackQuery):
    from helpers import userbot_client
    from telethon.tl.types import Channel,Chat
    await safe_edit(call.message,"⏳ Yuklanmoqda...")
    try:
        d=await userbot_client.get_dialogs()
        g=[x for x in d if isinstance(x.entity,Chat) or (isinstance(x.entity,Channel) and x.entity.megagroup)]
        lines=[f"  {i+1}. <b>{x.name}</b> — <code>{x.id}</code>" for i,x in enumerate(g[:40])]
        text=f"👥 <b>Guruhlarim ({len(g)}):</b>\n\n"+"\n".join(lines)
        if len(g)>40: text+=f"\n<i>...va yana {len(g)-40} ta</i>"
    except Exception as e: text=f"❌ <code>{e}</code>"
    await safe_edit(call.message,text,reply_markup=kb.tools_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="tool_my_channels")
@admin_only
async def t_channels(call: CallbackQuery):
    from helpers import userbot_client
    from telethon.tl.types import Channel
    await safe_edit(call.message,"⏳ Yuklanmoqda...")
    try:
        d=await userbot_client.get_dialogs()
        c=[x for x in d if isinstance(x.entity,Channel) and x.entity.broadcast]
        lines=[f"  {i+1}. <b>{x.name}</b> — <code>{x.id}</code>" for i,x in enumerate(c[:40])]
        text=f"📢 <b>Kanallarim ({len(c)}):</b>\n\n"+"\n".join(lines)
    except Exception as e: text=f"❌ <code>{e}</code>"
    await safe_edit(call.message,text,reply_markup=kb.tools_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="tool_get_photo")
@admin_only
async def ask_photo(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.t_photo)
    await safe_edit(call.message,"🖼 Username yoki ID:",reply_markup=kb.cancel_btn())

@dp.message(S.t_photo)
@admin_only
async def do_photo(msg: Message, state: FSMContext):
    await state.clear()
    from helpers import userbot_client
    val=msg.text.strip().lstrip("@")
    try:
        try: val=int(val)
        except: pass
        photos=await userbot_client.get_profile_photos(val)
        if photos:
            await userbot_client.send_file(config.ADMIN_ID,photos[0],caption="🖼 Profil rasm")
            await safe_answer(msg,"✅ Yuborildi.",reply_markup=kb.tools_menu())
        else:
            await safe_answer(msg,"❌ Profil rasm yo'q.",reply_markup=kb.tools_menu())
    except Exception as e:
        await safe_answer(msg,f"❌ <code>{e}</code>",reply_markup=kb.tools_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="tool_contacts")
@admin_only
async def t_contacts(call: CallbackQuery):
    from helpers import userbot_client
    from telethon.tl.functions.contacts import GetContactsRequest
    await safe_edit(call.message,"⏳ Yuklanmoqda...")
    try:
        r=await userbot_client(GetContactsRequest(hash=0))
        lines=[f"  • <b>{(u.first_name or '')+' '+(u.last_name or '')}</b> "
               f"(@{u.username or '—'}) <code>{u.id}</code>" for u in r.users[:50]]
        text=f"📞 <b>Kontaktlar ({len(r.users)}):</b>\n\n"+"\n".join(lines)
        if len(r.users)>50: text+=f"\n<i>...va yana {len(r.users)-50} ta</i>"
    except Exception as e: text=f"❌ <code>{e}</code>"
    await safe_edit(call.message,text,reply_markup=kb.tools_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="tool_group_stats")
@admin_only
async def ask_gstats(call: CallbackQuery, state: FSMContext):
    await state.set_state(S.t_gstats)
    await safe_edit(call.message,"📊 Guruh/kanal ID:",reply_markup=kb.cancel_btn())

@dp.message(S.t_gstats)
@admin_only
async def do_gstats(msg: Message, state: FSMContext):
    await state.clear()
    from helpers import userbot_client
    val=msg.text.strip().lstrip("@")
    st=await msg.answer("⏳ Hisoblanmoqda...")
    try:
        try: val=int(val)
        except: pass
        e=await userbot_client.get_entity(val)
        total=bots=no_un=0
        async for p in userbot_client.iter_participants(val):
            total+=1
            if p.bot: bots+=1
            if not p.username: no_un+=1
        await st.edit_text(
            f"📊 <b>{e.title}</b>\n{'─'*24}\n"
            f"👥 Jami: <b>{total}</b>  🤖 Botlar: <b>{bots}</b>\n"
            f"👤 Odamlar: <b>{total-bots}</b>\n"
            f"🔢 Username yo'q: <b>{no_un}</b>\n"
            f"✅ Username bor: <b>{total-bots-no_un}</b>",
            reply_markup=kb.tools_menu(),parse_mode="HTML")
    except Exception as e:
        await st.edit_text(f"❌ <code>{e}</code>",reply_markup=kb.tools_menu(),parse_mode="HTML")

@dp.callback_query(F.data=="tool_account_info")
@admin_only
async def t_account(call: CallbackQuery):
    from helpers import userbot_client
    try:
        me=await userbot_client.get_me()
        await safe_edit(call.message,
            f"ℹ️ <b>Account holati</b>\n{'─'*24}\n"
            f"👤 {me.first_name} (@{me.username})\n"
            f"🆔 ID: <code>{me.id}</code>\n"
            f"📱 Telefon: <code>{me.phone}</code>\n\n"
            f"🔍 Spam tekshiruv: @SpamBot → /start",
            reply_markup=kb.tools_menu(),parse_mode="HTML")
    except Exception as e:
        await safe_edit(call.message,f"❌ <code>{e}</code>",reply_markup=kb.tools_menu(),parse_mode="HTML")


# ── SCHEDULE RUNNER ─────────────────────────────────────────
async def schedule_runner():
    from helpers import userbot_client, safe_send, do_broadcast
    while True:
        await asyncio.sleep(60)
        try:
            items=storage.get_scheduled(); now=datetime.now().strftime("%Y-%m-%d %H:%M")
            for i,it in enumerate(items):
                if it.get("done"): continue
                if it["time"]<=now:
                    try:
                        t=it["target"]; txt=it["text"]
                        if t=="broadcast": await do_broadcast(storage.get_broadcast_targets(),{"content":txt})
                        elif t=="target":  await do_broadcast(storage.get_target_users(),{"content":txt})
                        else: await safe_send(t,text=txt)
                        data=storage._load()
                        if i<len(data["scheduled_messages"]):
                            data["scheduled_messages"][i]["done"]=True; storage._save(data)
                        log.info(f"Schedule yuborildi: {it['time']} → {t}")
                    except Exception as e:
                        log.error(f"Schedule xato: {e}")
        except Exception as e:
            log.error(f"Schedule runner: {e}")
