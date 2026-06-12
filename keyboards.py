# =============================================================
#  keyboards.py
# =============================================================
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as B


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="📡 Broadcast",         callback_data="menu_broadcast"),
         B(text="🎯 Target DM",         callback_data="menu_target")],
        [B(text="👥 Guruhlar",          callback_data="menu_groups"),
         B(text="👤 Userlar",           callback_data="menu_users")],
        [B(text="🤖 Auto-funksiyalar",  callback_data="menu_auto"),
         B(text="💬 Avto-javob logi",   callback_data="menu_ar_log")],
        [B(text="📝 Eslatmalar",        callback_data="menu_notes"),
         B(text="🔍 Filtrlar",          callback_data="menu_filters")],
        [B(text="🏷 Teglar",            callback_data="menu_tags"),
         B(text="⏰ Rejalashtirish",    callback_data="menu_schedule")],
        [B(text="🚫 Qora ro'yxat",      callback_data="menu_blacklist"),
         B(text="👮 Sub-adminlar",      callback_data="menu_admins")],
        [B(text="📊 Statistika",        callback_data="menu_stats"),
         B(text="⚙️ Sozlamalar",       callback_data="menu_settings")],
        [B(text="🛠 Vositalar",         callback_data="menu_tools"),
         B(text="📋 Broadcast tarixi",  callback_data="menu_bc_log")],
    ])


def _back(to="back_main"):
    return [[B(text="🔙 Orqaga", callback_data=to)]]


def back_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=_back())


def cancel_btn() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="❌ Bekor", callback_data="back_main")]
    ])


def confirm_send(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="✅ Ha, yuborish", callback_data=f"confirm_{action}"),
         B(text="❌ Bekor",        callback_data="back_main")],
    ])


def confirm_action(action: str, label="✅ Ha") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text=label,      callback_data=f"yes_{action}"),
         B(text="❌ Yo'q",  callback_data="back_main")],
    ])


# --- Guruhlar ---
def groups_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="➕ Qo'shish",          callback_data="add_group"),
         B(text="➖ O'chirish",         callback_data="del_group")],
        [B(text="📋 Ro'yxat",           callback_data="list_groups"),
         B(text="🗑 Hammasini tozala",  callback_data="confirm_clear_groups")],
        *_back(),
    ])


# --- Userlar ---
def users_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="➕ User qo'shish",     callback_data="add_user"),
         B(text="➖ User o'chirish",    callback_data="del_user")],
        [B(text="📥 Guruhdan import",   callback_data="import_from_group"),
         B(text="📥 Kanaldan import",   callback_data="import_from_channel")],
        [B(text="📋 Ro'yxat",           callback_data="list_users"),
         B(text="🗑 Hammasini tozala",  callback_data="confirm_clear_users")],
        *_back(),
    ])


# --- Broadcast ---
def broadcast_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="✏️ Matn",     callback_data="bc_text"),
         B(text="🖼 Rasm",     callback_data="bc_photo")],
        [B(text="🎥 Video",    callback_data="bc_video"),
         B(text="🎵 Audio",    callback_data="bc_audio")],
        [B(text="📄 Fayl",     callback_data="bc_file"),
         B(text="🔗 Havola",   callback_data="bc_link")],
        *_back(),
    ])


# --- Target DM ---
def target_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="✏️ Matn",     callback_data="tg_text"),
         B(text="🖼 Rasm",     callback_data="tg_photo")],
        [B(text="🎥 Video",    callback_data="tg_video"),
         B(text="🎵 Audio",    callback_data="tg_audio")],
        [B(text="📄 Fayl",     callback_data="tg_file")],
        *_back(),
    ])


# --- Auto ---
def auto_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🔄 Auto-reply on/off",   callback_data="toggle_autoreply"),
         B(text="✏️ Matnni o'zgartir",   callback_data="edit_autoreply_text")],
        [B(text="👋 Welcome on/off",      callback_data="toggle_welcome"),
         B(text="✏️ Welcome matni",       callback_data="edit_welcome_text")],
        [B(text="👋 Goodbye on/off",      callback_data="toggle_goodbye"),
         B(text="✏️ Goodbye matni",       callback_data="edit_goodbye_text")],
        *_back(),
    ])


# --- AR log ---
def ar_log_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🔄 Yangilash",           callback_data="menu_ar_log"),
         B(text="🗑 Logi tozalash",       callback_data="confirm_clear_ar_log")],
        [B(text="📥 Bu userlarga DM yubor", callback_data="dm_to_ar_log")],
        *_back(),
    ])


# --- Notes ---
def notes_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="➕ Qo'shish",    callback_data="add_note"),
         B(text="📋 Barchasi",    callback_data="list_notes")],
        [B(text="🔍 Ko'rish",     callback_data="get_note"),
         B(text="🗑 O'chirish",   callback_data="del_note")],
        *_back(),
    ])


# --- Filters ---
def filters_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="➕ Filter qo'shish",  callback_data="add_filter"),
         B(text="📋 Barchasi",         callback_data="list_filters")],
        [B(text="🗑 O'chirish",        callback_data="del_filter")],
        *_back(),
    ])


# --- Tags ---
def tags_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🏷 Qo'shish",    callback_data="add_tag"),
         B(text="📋 Barchasi",    callback_data="list_tags")],
        [B(text="❌ O'chirish",   callback_data="del_tag")],
        *_back(),
    ])


# --- Schedule ---
def schedule_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="➕ Yangi",         callback_data="add_schedule")],
        [B(text="📋 Ro'yxat",       callback_data="list_schedule"),
         B(text="🗑 Bekor qilish",  callback_data="del_schedule")],
        *_back(),
    ])


# --- Blacklist ---
def blacklist_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="➕ Qo'shish",    callback_data="add_blacklist"),
         B(text="➖ O'chirish",   callback_data="del_blacklist")],
        [B(text="📋 Ro'yxat",     callback_data="list_blacklist")],
        *_back(),
    ])


# --- Admins ---
def admins_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="➕ Admin qo'shish",   callback_data="add_admin"),
         B(text="➖ Admin o'chirish",  callback_data="del_admin")],
        [B(text="📋 Ro'yxat",          callback_data="list_admins")],
        *_back(),
    ])


# --- Stats ---
def stats_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="🔄 Yangilash",       callback_data="show_stats"),
         B(text="♻️ Tozalash",       callback_data="confirm_reset_stats")],
        *_back(),
    ])


# --- Settings ---
def settings_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="⏱ DM delay",         callback_data="set_dm_delay"),
         B(text="📊 Kunlik limit",     callback_data="set_dm_limit")],
        [B(text="⏱ Broadcast delay",  callback_data="set_bc_delay")],
        [B(text="📁 Data export",      callback_data="export_data")],
        *_back(),
    ])


# --- Tools ---
def tools_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [B(text="👤 User info",          callback_data="tool_userinfo"),
         B(text="💬 Chat info",          callback_data="tool_chatinfo")],
        [B(text="📋 Mening guruhlarim",  callback_data="tool_my_groups"),
         B(text="📢 Mening kanallarim",  callback_data="tool_my_channels")],
        [B(text="🖼 Profil rasm",        callback_data="tool_get_photo"),
         B(text="📞 Kontaktlar",         callback_data="tool_contacts")],
        [B(text="📊 Guruh statistikasi", callback_data="tool_group_stats"),
         B(text="ℹ️ Account holati",    callback_data="tool_account_info")],
        *_back(),
    ])
