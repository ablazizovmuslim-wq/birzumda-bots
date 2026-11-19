"""Bot profili: About (qisqa tavsif), Description (bo'sh chatdagi matn) va avatarka — 3 tilda.

Ishga tushganda o'zgargan bo'lsagina Telegram'ga yuboriladi (versiya bazada saqlanadi).
"""
import hashlib
import json
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, InputProfilePhotoStatic

from common import db, log

ASSETS = Path(__file__).parent / "assets"
SITE = "mybirzumda.uz"

PROFILES = {
    "lotin": {
        "about": {"uz": "🔤 Kirill ↔ lotin: matn va Word fayllarni bir zumda o'giradi. Bepul! ⚡ " + SITE,
                  "ru": "🔤 Кириллица ↔ латиница: текст и Word-файлы в один миг. Бесплатно! ⚡ " + SITE,
                  "en": "🔤 Uzbek Cyrillic ↔ Latin: text and Word files in an instant. Free! ⚡ " + SITE},
        "desc": {"uz": "🔤 Birzumda Lotin — o'zbek matnini kirilldan lotinga va lotindan kirillga o'giradi.\n\n"
                       "✍️ Matn yuboring — alifboni o'zim aniqlayman\n📄 Word (.docx) va .txt — formati saqlanadi\n"
                       "✅ Rasmiy imlo: oʻ, gʻ, ye, tutuq belgisi\n🆓 Butunlay bepul\n\n«Start» ni bosing 👇",
                 "ru": "🔤 Birzumda Lotin — переводит узбекский текст с кириллицы на латиницу и обратно.\n\n"
                       "✍️ Отправьте текст — алфавит определю сам\n📄 Word (.docx) и .txt — с сохранением оформления\n"
                       "✅ Официальные правила: oʻ, gʻ, ye, ъ\n🆓 Полностью бесплатно\n\nНажмите «Start» 👇",
                 "en": "🔤 Birzumda Lotin converts Uzbek text from Cyrillic to Latin and back.\n\n"
                       "✍️ Send text — I'll detect the alphabet\n📄 Word (.docx) and .txt — formatting kept\n"
                       "✅ Official spelling rules\n🆓 Completely free\n\nTap «Start» 👇"}},
    "hisob": {
        "about": {"uz": "🧮 Valyuta kursi (Markaziy bank), konvertor, QR kod va kredit kalkulyatori. Bepul! ⚡ " + SITE,
                  "ru": "🧮 Курс валют ЦБ, конвертер, QR-код и кредитный калькулятор. Бесплатно! ⚡ " + SITE,
                  "en": "🧮 Central Bank exchange rates, converter, QR codes and loan calculator. Free! ⚡ " + SITE},
        "desc": {"uz": "🧮 Birzumda Hisob — kundalik hisob-kitob uchun yordamchi.\n\n💵 Markaziy bank valyuta kurslari\n"
                       "🔄 Konvertor: «100 usd», «1000000 so'm eur»\n📱 Havola yoki matndan QR kod\n🏦 Kredit: oylik to'lov va ortiqcha to'lov\n"
                       "🆓 Bepul\n\n«Start» ni bosing 👇",
                 "ru": "🧮 Birzumda Hisob — помощник для ежедневных расчётов.\n\n💵 Курсы валют Центробанка Узбекистана\n"
                       "🔄 Конвертер: «100 usd», «1000000 сум eur»\n📱 QR-код из ссылки или текста\n🏦 Кредит: ежемесячный платёж и переплата\n"
                       "🆓 Бесплатно\n\nНажмите «Start» 👇",
                 "en": "🧮 Birzumda Hisob — your everyday calculator.\n\n💵 Central Bank of Uzbekistan rates\n"
                       "🔄 Converter: «100 usd», «1000000 sum eur»\n📱 QR codes from links or text\n🏦 Loan: monthly payment and overpayment\n"
                       "🆓 Free\n\nTap «Start» 👇"}},
    "stiker": {
        "about": {"uz": "🧩 Rasmdan Telegram stiker va o'z stikerpakingiz — bir zumda! Bepul ⚡ " + SITE,
                  "ru": "🧩 Стикеры из фото и свой стикерпак в Telegram — в один миг! Бесплатно ⚡ " + SITE,
                  "en": "🧩 Turn photos into Telegram stickers and your own pack — instantly! Free ⚡ " + SITE},
        "desc": {"uz": "🧩 Birzumda Stiker — rasmlaringizdan stiker yasaydi.\n\n📸 Rasm yuboring — stiker tayyor\n⚪ Doira shaklidagi stiker\n"
                       "📦 Bir tugma bilan o'z stikerpakingizga qo'shing\n🎁 Do'stlaringizga ulashing\n🆓 Bepul\n\n«Start» ni bosing 👇",
                 "ru": "🧩 Birzumda Stiker — делает стикеры из ваших фото.\n\n📸 Отправьте фото — стикер готов\n⚪ Круглый стикер\n"
                       "📦 Одной кнопкой в свой стикерпак\n🎁 Делитесь с друзьями\n🆓 Бесплатно\n\nНажмите «Start» 👇",
                 "en": "🧩 Birzumda Stiker turns your photos into stickers.\n\n📸 Send a photo — sticker ready\n⚪ Round stickers\n"
                       "📦 Add to your own pack with one tap\n🎁 Share with friends\n🆓 Free\n\nTap «Start» 👇"}},
    "musiqa": {
        "about": {"uz": "🎵 Videodan, dumaloq videodan va ovozli xabardan MP3 ajratib beradi. Bepul! ⚡ " + SITE,
                  "ru": "🎵 Достаёт MP3 из видео, кружков и голосовых сообщений. Бесплатно! ⚡ " + SITE,
                  "en": "🎵 Extracts MP3 from videos, video notes and voice messages. Free! ⚡ " + SITE},
        "desc": {"uz": "🎵 Birzumda Musiqa — videodagi musiqa va ovozni MP3 qilib beradi.\n\n🎬 Video yuboring — MP3 tayyor\n"
                       "⭕ Dumaloq video va 🎤 ovozli xabarlar ham\n🎧 Yuqori sifat (192 kbps)\n📥 Video yuklash: @Birzumda_Yukla_bot\n"
                       "🆓 Bepul\n\n«Start» ni bosing 👇",
                 "ru": "🎵 Birzumda Musiqa — превращает звук из видео в MP3.\n\n🎬 Отправьте видео — MP3 готов\n"
                       "⭕ Кружки и 🎤 голосовые тоже\n🎧 Высокое качество (192 kbps)\n📥 Скачать видео: @Birzumda_Yukla_bot\n"
                       "🆓 Бесплатно\n\nНажмите «Start» 👇",
                 "en": "🎵 Birzumda Musiqa turns the sound of any video into MP3.\n\n🎬 Send a video — MP3 ready\n"
                       "⭕ Video notes and 🎤 voice messages too\n🎧 High quality (192 kbps)\n📥 Download videos: @Birzumda_Yukla_bot\n"
                       "🆓 Free\n\nTap «Start» 👇"}},
    "eslatma": {
        "about": {"uz": "⏰ Eslatmalar va dars jadvali: ertalab bugungi rejangizni yuboraman. Bepul! ⚡ " + SITE,
                  "ru": "⏰ Напоминания и расписание: утром пришлю план на день. Бесплатно! ⚡ " + SITE,
                  "en": "⏰ Reminders and timetable: your plan for the day every morning. Free! ⚡ " + SITE},
        "desc": {"uz": "⏰ Birzumda Eslatma — hech narsani unutmang!\n\n✍️ «18:30 Dars», «ertaga 9:00 Imtihon», «30 min Choy»\n"
                       "📅 Dars jadvali — har kuni ertalab bugungi darslar\n📋 Eslatmalar ro'yxati\n🕐 Toshkent vaqti\n🆓 Bepul\n\n«Start» ni bosing 👇",
                 "ru": "⏰ Birzumda Eslatma — ничего не забывайте!\n\n✍️ «18:30 Пара», «завтра 9:00 Экзамен», «30 мин Чай»\n"
                       "📅 Расписание — каждое утро пары на сегодня\n📋 Список напоминаний\n🕐 Время Ташкента\n🆓 Бесплатно\n\nНажмите «Start» 👇",
                 "en": "⏰ Birzumda Eslatma — never forget a thing!\n\n✍️ «18:30 Class», «tomorrow 9:00 Exam», «30 min Tea»\n"
                       "📅 Timetable — today's classes every morning\n📋 Reminder list\n🕐 Tashkent time\n🆓 Free\n\nTap «Start» 👇"}},
}


def _version(key: str) -> str:
    p = ASSETS / f"{key}.jpg"
    raw = json.dumps(PROFILES.get(key, {}), ensure_ascii=False).encode() + (p.read_bytes() if p.exists() else b"")
    return hashlib.sha1(raw).hexdigest()[:16]


async def apply_profile(bot: Bot, key: str):
    prof = PROFILES.get(key)
    if not prof:
        return
    ver = _version(key)
    with db() as con:
        con.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
        row = con.execute("SELECT v FROM meta WHERE k=?", (f"profile_{key}",)).fetchone()
    if row and row["v"] == ver:
        return
    try:
        for lang in ("uz", "ru", "en"):
            code = None if lang == "uz" else lang          # o'zbekcha — standart (boshqa tillar uchun ham)
            await bot.set_my_short_description(short_description=prof["about"][lang][:120], language_code=code)
            await bot.set_my_description(description=prof["desc"][lang][:512], language_code=code)
        photo = ASSETS / f"{key}.jpg"
        if photo.exists():
            await bot.set_my_profile_photo(photo=InputProfilePhotoStatic(photo=FSInputFile(photo)))
        with db() as con:
            con.execute("INSERT INTO meta(k, v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (f"profile_{key}", ver))
        log.info("%s: profil yangilandi", key)
    except Exception as e:
        log.warning("%s: profilni yangilab bo'lmadi: %s", key, e)
