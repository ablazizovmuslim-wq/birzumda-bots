"""🔤 Birzumda Lotin — kirill ↔ lotin: matn va Word (.docx) fayllar."""
import io

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message)

from common import variants, CT, LANGS, count, get_lang, menu, touch, tr
from translit import convert

KEY, USERNAME = "lotin", "Birzumda_Lotin_bot"

TX = {
    "start": {"uz": "👋 Salom, <b>{name}</b>!\n\n🔤 Men matnni <b>kirilldan lotinga</b> va <b>lotindan kirillga</b> o'giraman.\n\n"
                    "✍️ Matn yuboring — alifboni o'zim aniqlayman.\n📄 Word (.docx) yoki .txt fayl yuboring — butun hujjatni "
                    "formatini saqlagan holda o'girib beraman.",
              "ru": "👋 Привет, <b>{name}</b>!\n\n🔤 Перевожу узбекский текст <b>с кириллицы на латиницу</b> и обратно.\n\n"
                    "✍️ Отправьте текст — алфавит определю сам.\n📄 Отправьте Word (.docx) или .txt — переведу весь документ, "
                    "сохраняя оформление.",
              "en": "👋 Hi, <b>{name}</b>!\n\n🔤 I convert Uzbek text <b>from Cyrillic to Latin</b> and back.\n\n"
                    "✍️ Send text — I'll detect the alphabet.\n📄 Send a Word (.docx) or .txt file — I'll convert the whole "
                    "document and keep the formatting."},
    "b_lat": {"uz": "🔤 Lotinga", "ru": "🔤 На латиницу", "en": "🔤 To Latin"},
    "b_cyr": {"uz": "🔠 Kirillga", "ru": "🔠 На кириллицу", "en": "🔠 To Cyrillic"},
    "b_help": {"uz": "❓ Qanday ishlaydi", "ru": "❓ Как работает", "en": "❓ How it works"},
    "mode_lat": {"uz": "✅ Endi hamma narsani <b>lotinga</b> o'giraman. Matn yoki fayl yuboring.",
                 "ru": "✅ Теперь всё перевожу <b>на латиницу</b>. Отправьте текст или файл.",
                 "en": "✅ Now converting everything <b>to Latin</b>. Send text or a file."},
    "mode_cyr": {"uz": "✅ Endi hamma narsani <b>kirillga</b> o'giraman. Matn yoki fayl yuboring.",
                 "ru": "✅ Теперь всё перевожу <b>на кириллицу</b>. Отправьте текст или файл.",
                 "en": "✅ Now converting everything <b>to Cyrillic</b>. Send text or a file."},
    "again": {"uz": "🔁 Teskarisiga", "ru": "🔁 Обратно", "en": "🔁 Reverse"},
    "file_ok": {"uz": "✅ Tayyor! Hujjat {dir} o'girildi.", "ru": "✅ Готово! Документ переведён {dir}.",
                "en": "✅ Done! The document was converted {dir}."},
    "to_lat": {"uz": "lotinga", "ru": "на латиницу", "en": "to Latin"},
    "to_cyr": {"uz": "kirillga", "ru": "на кириллицу", "en": "to Cyrillic"},
    "bad_file": {"uz": "Faqat .docx yoki .txt fayl yuboring (20 MB gacha).", "ru": "Отправьте файл .docx или .txt (до 20 МБ).",
                 "en": "Please send a .docx or .txt file (up to 20 MB)."},
    "err": {"uz": "😕 Faylni o'qib bo'lmadi. Boshqa fayl yuborib ko'ring.", "ru": "😕 Не удалось прочитать файл. Попробуйте другой.",
            "en": "😕 Couldn't read the file. Try another one."},
}

MODE: dict[int, str] = {}  # foydalanuvchi tanlagan yo'nalish ('lat' / 'cyr'); yo'q bo'lsa — avtomatik


def kb(lang):
    return menu(lang, [TX["b_lat"][lang], TX["b_cyr"][lang], TX["b_help"][lang]])


def docx_convert(raw: bytes, to: str | None):
    from docx import Document
    doc = Document(io.BytesIO(raw))
    sample = " ".join(p.text for p in doc.paragraphs[:60])
    to = to or convert(sample)[1]

    def fix_pars(pars):
        for p in pars:
            for run in p.runs:
                if run.text:
                    run.text = convert(run.text, to)[0]

    def walk(container):
        fix_pars(container.paragraphs)
        for t in container.tables:
            for row in t.rows:
                for cell in row.cells:
                    walk(cell)

    walk(doc)
    for s in doc.sections:
        for part in (s.header, s.footer):
            walk(part)
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue(), to


def make_router() -> Router:
    r = Router(name=KEY)

    @r.message(CommandStart())
    async def start(m: Message):
        lang = touch(KEY, m.from_user)
        await m.answer(tr(TX["start"], lang, name=m.from_user.first_name), reply_markup=kb(lang))

    @r.message(F.text.in_(variants(TX["b_help"])))
    async def help_(m: Message):
        lang = get_lang(KEY, m.from_user.id)
        await m.answer(tr(TX["start"], lang, name=m.from_user.first_name), reply_markup=kb(lang))

    @r.message(F.text.in_(variants(TX["b_lat"]) | variants(TX["b_cyr"])))
    async def mode(m: Message):
        lang = get_lang(KEY, m.from_user.id)
        to = "lat" if m.text in variants(TX["b_lat"]) else "cyr"
        MODE[m.from_user.id] = to
        await m.answer(TX["mode_" + to][lang])

    @r.message(F.document)
    async def file(m: Message, bot: Bot):
        lang = touch(KEY, m.from_user)
        d = m.document
        name = (d.file_name or "file").lower()
        if not (name.endswith(".docx") or name.endswith(".txt")) or (d.file_size or 0) > 20 * 1024 * 1024:
            return await m.answer(TX["bad_file"][lang])
        try:
            buf = io.BytesIO()
            await bot.download(d, destination=buf)
            raw = buf.getvalue()
            if name.endswith(".txt"):
                text = raw.decode("utf-8", errors="replace")
                res, to = convert(text, MODE.get(m.from_user.id))
                out = res.encode("utf-8")
            else:
                out, to = docx_convert(raw, MODE.get(m.from_user.id))
        except Exception:
            return await m.answer(TX["err"][lang])
        count(KEY, "file")
        base = (d.file_name or "file").rsplit(".", 1)
        fname = f"{base[0]}_{'lotin' if to == 'lat' else 'kirill'}.{base[1] if len(base) > 1 else 'txt'}"
        await m.answer_document(BufferedInputFile(out, filename=fname),
                                caption=TX["file_ok"][lang].format(dir=TX["to_" + to][lang]) + "\n\n⚡ @" + USERNAME)

    @r.message(F.text & ~F.text.startswith("/"))
    async def text(m: Message):
        lang = touch(KEY, m.from_user)
        res, to = convert(m.text, MODE.get(m.from_user.id))
        count(KEY, "text")
        back = "cyr" if to == "lat" else "lat"
        for i in range(0, len(res), 4000):  # Telegram cheklovi
            await m.answer(res[i:i + 4000], parse_mode=None, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=TX["again"][lang], callback_data=f"lt:{back}")]]) if i + 4000 >= len(res) else None)

    @r.callback_query(F.data.startswith("lt:"))
    async def reverse(c: CallbackQuery):
        to = c.data.split(":")[1]
        res, _ = convert(c.message.text or "", to)
        await c.message.answer(res[:4000], parse_mode=None)
        await c.answer()

    return r


async def on_lang(msg: Message, lang: str):
    await msg.answer("👇", reply_markup=kb(lang))
