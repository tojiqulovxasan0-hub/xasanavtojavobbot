import os
from dotenv import load_dotenv

load_dotenv()

def _req(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"❌ .env da '{key}' topilmadi!")
    return val

API_ID        = int(_req("API_ID"))
API_HASH      = _req("API_HASH")
PHONE         = os.getenv("PHONE", "")          # Railway da shart emas
ADMIN_ID      = int(_req("ADMIN_ID"))
BOT_TOKEN     = _req("BOT_TOKEN")
SESSION_NAME  = "userbot_session"
SESSION_STRING = os.getenv("SESSION_STRING", "") # Railway uchun base64 session

DM_DELAY        = 15
BROADCAST_DELAY = 3
DAILY_DM_LIMIT  = 30
