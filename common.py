"""Birzumda botlari uchun umumiy narsalar: baza, til, menyu, boshqa botlar, admin statistikasi."""
import json
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.filters import Command
from aiogram.methods import (EditMessageCaption, EditMessageText, SendAudio, SendDocument, SendMessage, SendPhoto,
                             SendVideo)
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message,
                           ReplyKeyboardMarkup)

DB_PATH = os.getenv("DB_PATH", "bots.db")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_ID", "5808241795").replace(" ", "").split(",") if x}
SITE = "https://mybirzumda.uz"
SUPPORT = "@Abdulazizov_prince"
TZ = timezone(timedelta(hours=5))  # Toshkent
LANGS = ("uz", "ru", "en")

# Birzumda oilasidagi barcha botlar — har bir botda «Boshqa botlarimiz» menyusi uchun
FAMILY = [
    ("📥", "Birzumda_Yukla_bot", {"uz": "Video yuklash", "ru": "Скачать видео", "en": "Video download"}),
    ("📊", "Birzumda_Tayyorla_bot", {"uz": "Taqdimot, kurs ishi", "ru": "Презентации, курсовые", "en": "Slides, papers"}),
    ("🔤", "Birzumda_Lotin_bot", {"uz": "Kirill ↔ lotin", "ru": "Кириллица ↔ латиница", "en": "Cyrillic ↔ Latin"}),
    ("🧮", "Birzumda_Hisob_bot", {"uz": "Kurs, QR, kredit", "ru": "Курс, QR, кредит", "en": "Rates, QR, loans"}),
    ("🧩", "Birzumda_Stiker_bot", {"uz": "Rasmdan stiker", "ru": "Стикер из фото", "en": "Photo to sticker"}),
    ("🎵", "Birzumda_Musiqa_bot", {"uz": "Videodan MP3", "ru": "MP3 из видео", "en": "MP3 from video"}),
    ("⏰", "Birzumda_Eslatma_bot", {"uz": "Eslatma va jadval", "ru": "Напоминания", "en": "Reminders"}),
]

# ------------------------------------------------------------------ 💎 premium (animatsion) emoji
# Oddiy emoji → premium emoji ID. Bot egasida Telegram Premium bo'lsa, matn va tugmalarda animatsion chiqadi.
# Yangisini qo'shish: admin istalgan botga premium emojili xabar yuboradi — hamma botlar uchun saqlanadi.
EMOJI = {
    "👋": "5215248074498128418", "✨": "5211057719720561874", "🎓": "5373012449597335010", "👩‍🏫": "5372926953978341366",
    "✅": "4956672355876209142", "💰": "5188208446461188962", "💵": "5188208446461188962", "👇": "5470177992950946662",
    "📋": "5188311512791393083", "🌐": "5447410659077661506", "🤖": "5244983043621411868", "🎵": "5213323516832667837",
    "🎨": "5375074927252621134", "📢": "5370599459661045441", "✍️": "5237808360882977239", "🎁": "5345961113479572537",
    "⚡": "5176998281170911817", "🇺🇿": "5222404546575219535", "🇷🇺": "5449408995691341691", "🇬🇧": "5224518800061245598",
    "📚": "5226512880362332956",
}
PREMIUM = os.getenv("PREMIUM_EMOJI", "1") != "0"
_TAG = re.compile(r"(<tg-emoji[^>]*>.*?</tg-emoji>|<code>.*?</code>|<pre>.*?</pre>|<a [^>]*>)", re.S)
_EMOJI_RE = None


def load_emoji():
    """Admin saqlagan qo'shimcha emoji ID'lari (baza: meta.emoji_map)."""
    global _EMOJI_RE
    try:
        with db() as con:
            con.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
            row = con.execute("SELECT v FROM meta WHERE k='emoji_map'").fetchone()
        if row:
            EMOJI.update(json.loads(row["v"]))
    except Exception as e:
        logging.warning("emoji_map: %s", e)
    keys = sorted(EMOJI, key=len, reverse=True)
    _EMOJI_RE = re.compile("|".join(re.escape(k) for k in keys)) if keys else None


def save_emoji(found: dict):
    with db() as con:
        con.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
        row = con.execute("SELECT v FROM meta WHERE k='emoji_map'").fetchone()
        saved = json.loads(row["v"]) if row else {}
        saved.update(found)
        con.execute("INSERT INTO meta(k, v) VALUES('emoji_map', ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (json.dumps(saved),))
    load_emoji()


def animate(text: str) -> str:
    """HTML matndagi oddiy emojilarni premium <tg-emoji> ga almashtiradi (teglar, kod va havolalar ichida emas)."""
    if not (PREMIUM and text and _EMOJI_RE):
        return text
    parts = _TAG.split(text)
    for i in range(0, len(parts), 2):  # juft indekslar — teg tashqarisidagi matn
        parts[i] = _EMOJI_RE.sub(lambda m: f'<tg-emoji emoji-id="{EMOJI[m.group()]}">{m.group()}</tg-emoji>', parts[i])
    return "".join(parts)


def _split_icon(text: str):
    """«🎵 Musiqa» → ("Musiqa", emoji_id) agar shu emoji premium bo'lsa."""
    head, _, rest = text.partition(" ")
    if PREMIUM and rest and head in EMOJI:
        return rest, EMOJI[head]
    return text, None


def kbtn(text: str, style: str | None = None) -> KeyboardButton:
    t, icon = _split_icon(text)
    extra = {"style": style} if style else {}
    if icon:
        extra["icon_custom_emoji_id"] = icon
    return KeyboardButton(text=t, **extra)


def ibtn(text: str, style: str | None = None, **kw) -> InlineKeyboardButton:
    t, icon = _split_icon(text)
    extra = {"style": style} if style else {}
    if icon:
        extra["icon_custom_emoji_id"] = icon
    return InlineKeyboardButton(text=t, **extra, **kw)


def variants(d: dict) -> set:
    """Tugma matni barcha tillarda — premium ikonka bilan (emojisiz) ham."""
    out = set()
    for v in d.values():
        out |= {v, v.partition(" ")[2] or v}
    return out


class EmojiMiddleware(BaseRequestMiddleware):
    """Bot yuborayotgan har bir HTML xabar va izohga premium emoji qo'yadi."""

    async def __call__(self, make_request, bot, method):
        field = None
        if isinstance(method, (SendMessage, EditMessageText)) and method.parse_mode is not None and isinstance(method.text, str):
            field = "text"
        elif isinstance(method, (SendPhoto, SendDocument, SendAudio, SendVideo, EditMessageCaption)) \
                and method.parse_mode is not None and isinstance(method.caption, str):
            field = "caption"
        if not field:
            return await make_request(bot, method)
        original = getattr(method, field)
        setattr(method, field, animate(original))
        try:
            return await make_request(bot, method)
        except Exception as e:  # Telegram premium emojini qabul qilmasa — oddiy emoji bilan qayta yuboramiz
            if "emoji" not in str(e).lower() and "entit" not in str(e).lower():
                raise
            setattr(method, field, original)
            return await make_request(bot, method)


CT = {
    "family": {"uz": "🌐 Boshqa botlarimiz", "ru": "🌐 Другие наши боты", "en": "🌐 Our other bots"},
    "lang": {"uz": "🌍 Til", "ru": "🌍 Язык", "en": "🌍 Language"},
    "help": {"uz": "❓ Yordam", "ru": "❓ Помощь", "en": "❓ Help"},
    "family_t": {"uz": "⚡ <b>Birzumda</b> — hammasi bir zumda!\n\nBarcha botlarimiz va sayt:",
                 "ru": "⚡ <b>Birzumda</b> — всё в один миг!\n\nВсе наши боты и сайт:",
                 "en": "⚡ <b>Birzumda</b> — everything in an instant!\n\nAll our bots and the website:"},
    "site": {"uz": "🌐 Sayt", "ru": "🌐 Сайт", "en": "🌐 Website"},
    "choose_lang": {"uz": "Tilni tanlang:", "ru": "Выберите язык:", "en": "Choose a language:"},
    "lang_ok": {"uz": "✅ Til: O'zbekcha", "ru": "✅ Язык: русский", "en": "✅ Language: English"},
    "support": {"uz": "Texnik yordam", "ru": "Техподдержка", "en": "Support"},
}


def db():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users(bot TEXT, user_id INTEGER, name TEXT, username TEXT, lang TEXT,
            joined TEXT, last_seen TEXT, PRIMARY KEY(bot, user_id));
        CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, due TEXT,
            text TEXT, sent INTEGER DEFAULT 0, created TEXT);
        CREATE TABLE IF NOT EXISTS lessons(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, weekday INTEGER,
            time TEXT, text TEXT);
        CREATE TABLE IF NOT EXISTS digest(user_id INTEGER PRIMARY KEY, time TEXT DEFAULT '07:00', on_ INTEGER DEFAULT 1,
            last TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS stickers(user_id INTEGER PRIMARY KEY, set_name TEXT, count INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS usage(bot TEXT, day TEXT, action TEXT, n INTEGER DEFAULT 0, PRIMARY KEY(bot, day, action));
        """)


def now_local() -> datetime:
    return datetime.now(TZ)


def touch(bot: str, user) -> str:
    """Foydalanuvchini saqlaydi va tilini qaytaradi (yangi bo'lsa — Telegram tilidan)."""
    stamp = now_local().strftime("%Y-%m-%d %H:%M")
    code = (user.language_code or "")[:2]
    guess = code if code in ("ru", "en") else "uz"
    with db() as con:
        con.execute("""INSERT INTO users(bot, user_id, name, username, lang, joined, last_seen) VALUES(?,?,?,?,?,?,?)
                       ON CONFLICT(bot, user_id) DO UPDATE SET name=excluded.name, username=excluded.username,
                       last_seen=excluded.last_seen""",
                    (bot, user.id, user.full_name, user.username or "", guess, stamp, stamp))
        return con.execute("SELECT lang FROM users WHERE bot=? AND user_id=?", (bot, user.id)).fetchone()["lang"]


def get_lang(bot: str, uid: int) -> str:
    with db() as con:
        r = con.execute("SELECT lang FROM users WHERE bot=? AND user_id=?", (bot, uid)).fetchone()
    return r["lang"] if r and r["lang"] in LANGS else "uz"


def set_lang(bot: str, uid: int, lang: str):
    with db() as con:
        con.execute("UPDATE users SET lang=? WHERE bot=? AND user_id=?", (lang, bot, uid))


def count(bot: str, action: str):
    day = now_local().strftime("%Y-%m-%d")
    with db() as con:
        con.execute("""INSERT INTO usage(bot, day, action, n) VALUES(?,?,?,1)
                       ON CONFLICT(bot, day, action) DO UPDATE SET n=n+1""", (bot, day, action))


def menu(lang: str, buttons: list[str]) -> ReplyKeyboardMarkup:
    """Pastki menyu: botning o'z tugmalari (ko'k) + umumiy tugmalar (yashil). Premium emoji bo'lsa — ikonka."""
    rows = [[kbtn(b, "primary") for b in buttons[i:i + 2]] for i in range(0, len(buttons), 2)]
    rows.append([kbtn(CT["family"][lang], "success"), kbtn(CT["lang"][lang])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def family_kb(lang: str, me: str) -> InlineKeyboardMarkup:
    rows = [[ibtn(f"{ic} {desc[lang]}", "primary", url=f"https://t.me/{u}")]
            for ic, u, desc in FAMILY if u.lower() != me.lower()]
    rows.append([ibtn(CT["site"][lang] + " — mybirzumda.uz", "success", url=SITE)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        ibtn("🇺🇿 O'zbekcha", "success", callback_data="lang:uz"),
        ibtn("🇷🇺 Русский", "primary", callback_data="lang:ru"),
        ibtn("🇬🇧 English", "danger", callback_data="lang:en")]])


def common_router(bot_key: str, username: str, on_lang_changed) -> Router:
    """Har bir botga: tilni almashtirish, «Boshqa botlarimiz», admin /stats."""
    r = Router(name=f"common_{bot_key}")

    @r.message(F.from_user.id.in_(ADMIN_IDS), F.entities.func(lambda es: any(e.type == "custom_emoji" for e in es or [])))
    async def save_premium(m: Message):
        """Admin premium emoji yuborsa — oddiy emoji → ID sifatida hamma botlar uchun saqlanadi."""
        found = {}
        raw = (m.text or "").encode("utf-16-le")
        for e in m.entities:
            if e.type == "custom_emoji":
                alt = raw[e.offset * 2:(e.offset + e.length) * 2].decode("utf-16-le", errors="ignore")
                if alt:
                    found[alt] = e.custom_emoji_id
        save_emoji(found)
        await m.answer("💎 Saqlandi (hamma botlar uchun):\n" + "\n".join(f"{k} → <code>{v}</code>" for k, v in found.items())
                       + "\n\nEndi bu emojilar matn va tugmalarda animatsion bo'ladi. Pastki tugmalar — /start dan keyin.")

    @r.message(F.text.in_(variants(CT["family"])))
    async def family(m: Message):
        lang = get_lang(bot_key, m.from_user.id)
        await m.answer(CT["family_t"][lang] + f"\n\n{CT['support'][lang]}: {SUPPORT}", reply_markup=family_kb(lang, username))

    @r.message(F.text.in_(variants(CT["lang"])))
    async def lang_menu(m: Message):
        await m.answer(CT["choose_lang"][get_lang(bot_key, m.from_user.id)], reply_markup=lang_kb())

    @r.callback_query(F.data.startswith("lang:"))
    async def lang_set(c: CallbackQuery):
        lang = c.data.split(":")[1]
        if lang in LANGS:
            set_lang(bot_key, c.from_user.id, lang)
            await c.message.answer(CT["lang_ok"][lang])
            await on_lang_changed(c.message, lang)
        await c.answer()

    @r.message(Command("stats"), F.from_user.id.in_(ADMIN_IDS))
    async def stats(m: Message):
        day = now_local().strftime("%Y-%m-%d")
        with db() as con:
            total = con.execute("SELECT COUNT(*) FROM users WHERE bot=?", (bot_key,)).fetchone()[0]
            today = con.execute("SELECT COUNT(*) FROM users WHERE bot=? AND joined LIKE ?", (bot_key, day + "%")).fetchone()[0]
            active = con.execute("SELECT COUNT(*) FROM users WHERE bot=? AND last_seen LIKE ?", (bot_key, day + "%")).fetchone()[0]
            acts = con.execute("SELECT action, n FROM usage WHERE bot=? AND day=?", (bot_key, day)).fetchall()
        lines = "\n".join(f"• {a['action']}: {a['n']}" for a in acts) or "—"
        await m.answer(f"📊 <b>@{username}</b>\n👥 Jami: <b>{total}</b>\n🆕 Bugun yangi: <b>{today}</b>\n"
                       f"🔥 Bugun faol: <b>{active}</b>\n\n<b>Bugungi amallar:</b>\n{lines}")

    return r


def tr(d: dict, lang: str, **kw) -> str:
    s = d.get(lang) or d["uz"]
    return s.format(**kw) if kw else s


log = logging.getLogger("birzumda")
