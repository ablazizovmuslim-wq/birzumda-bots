"""Birzumda botlari — bitta jarayonda bir nechta bot (Railway'da xotirani tejash uchun).

Har bir bot o'z tokeni bilan: TOKEN_LOTIN, TOKEN_HISOB, TOKEN_STIKER, TOKEN_MUSIQA, TOKEN_ESLATMA.
Tokeni yo'q bot shunchaki ishga tushmaydi.
"""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bots import eslatma, hisob, lotin, musiqa, stiker
from common import common_router, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
MODULES = [lotin, hisob, stiker, musiqa, eslatma]
COMMANDS = {"uz": "Boshlash", "ru": "Начать", "en": "Start"}


async def run_one(mod):
    token = os.getenv(f"TOKEN_{mod.KEY.upper()}")
    if not token:
        logging.info("%s: token yo'q — o'tkazib yuborildi", mod.KEY)
        return
    bot = Bot(token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(common_router(mod.KEY, mod.USERNAME, mod.on_lang))  # umumiy tugmalar birinchi
    dp.include_router(mod.make_router())
    for lang, text in COMMANDS.items():
        try:
            await bot.set_my_commands([BotCommand(command="start", description=text)], language_code=None if lang == "uz" else lang)
        except Exception as e:
            logging.warning("%s komandalar: %s", mod.KEY, e)
    if hasattr(mod, "background"):
        asyncio.create_task(mod.background(bot))
    logging.info("%s ishga tushdi", mod.KEY)
    await dp.start_polling(bot, handle_signals=False)


async def main():
    init_db()
    await asyncio.gather(*(run_one(m) for m in MODULES))


if __name__ == "__main__":
    asyncio.run(main())
