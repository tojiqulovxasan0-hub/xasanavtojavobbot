# =============================================================
#  main.py  —  Hamma narsani ishga tushiradi
# =============================================================

import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("userbot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

import userbot
import control_bot
import handlers_extra   # noqa
import user_bot         # noqa  — foydalanuvchi handlerlari
import helpers


async def main():
    await userbot.start_userbot()

    # Helpers ga userbot client inject
    helpers.userbot_client = userbot.client

    print("✅ Control bot ishga tushdi. Telegram botingizga /start yuboring.")
    print("=" * 50)

    await asyncio.gather(
        asyncio.ensure_future(userbot.client.run_until_disconnected()),
        asyncio.ensure_future(control_bot.start_bot()),
        asyncio.ensure_future(handlers_extra.schedule_runner()),
    )


if __name__ == "__main__":
    asyncio.run(main())
