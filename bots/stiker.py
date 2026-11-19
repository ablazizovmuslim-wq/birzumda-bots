"""🧩 Birzumda Stiker — rasmdan Telegram stiker va shaxsiy stikerpak."""
import io

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputSticker,
                           Message)
from PIL import Image, ImageOps

from common import variants, LANGS, count, db, get_lang, menu, touch, tr

KEY, USERNAME = "stiker", "Birzumda_Stiker_bot"

TX = {
    "start": {"uz": "👋 Salom, <b>{name}</b>!\n\n🧩 Menga <b>rasm</b> yuboring — undan Telegram <b>stiker</b> yasayman.\n\n"
                    "➕ Yoqqan stikerlarni bir tugma bilan <b>o'z stikerpakingizga</b> qo'shing va do'stlaringizga ulashing!",
              "ru": "👋 Привет, <b>{name}</b>!\n\n🧩 Отправьте <b>фото</b> — сделаю из него <b>стикер</b> для Telegram.\n\n"
                    "➕ Понравившиеся стикеры одной кнопкой добавляйте в <b>свой стикерпак</b> и делитесь с друзьями!",
              "en": "👋 Hi, <b>{name}</b>!\n\n🧩 Send me a <b>photo</b> — I'll turn it into a Telegram <b>sticker</b>.\n\n"
                    "➕ Add the ones you like to <b>your own sticker pack</b> with one tap and share it!"},
    "b_pack": {"uz": "📦 Mening stikerpakim", "ru": "📦 Мой стикерпак", "en": "📦 My sticker pack"},
    "b_help": {"uz": "❓ Qanday ishlaydi", "ru": "❓ Как работает", "en": "❓ How it works"},
    "add": {"uz": "➕ Stikerpakimga qo'shish", "ru": "➕ В мой стикерпак", "en": "➕ Add to my pack"},
    "round": {"uz": "⚪ Doira shaklida", "ru": "⚪ Круглый", "en": "⚪ Round"},
    "added": {"uz": "✅ Qo'shildi! Stikerpakingiz: {link}", "ru": "✅ Добавлено! Ваш стикерпак: {link}",
              "en": "✅ Added! Your pack: {link}"},
    "no_pack": {"uz": "Hali stikerpakingiz yo'q. Rasm yuboring va «➕» ni bosing.",
                "ru": "У вас пока нет стикерпака. Отправьте фото и нажмите «➕».",
                "en": "You don't have a pack yet. Send a photo and tap «➕»."},
    "pack": {"uz": "📦 Stikerpakingiz ({n} ta): {link}", "ru": "📦 Ваш стикерпак ({n} шт.): {link}", "en": "📦 Your pack ({n}): {link}"},
    "send_photo": {"uz": "📸 Rasm yuboring (rasm sifatida yoki fayl sifatida).", "ru": "📸 Отправьте фото (как фото или файлом).",
                   "en": "📸 Send a photo (as a photo or a file)."},
    "gone": {"uz": "Bu stiker eskirgan — rasmni qaytadan yuboring.", "ru": "Стикер устарел — отправьте фото заново.",
             "en": "This sticker expired — send the photo again."},
    "err": {"uz": "😕 Qo'shib bo'lmadi: {e}", "ru": "😕 Не удалось добавить: {e}", "en": "😕 Couldn't add: {e}"},
}

LAST: dict[int, dict] = {}  # foydalanuvchining oxirgi rasmi va stikeri: {"raw": bytes, "file_id": str}


def to_sticker(raw: bytes, round_: bool = False) -> bytes:
    """Rasm → 512 px WEBP stiker (shaffof fon saqlanadi)."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGBA")
    if round_:
        side = min(img.size)
        img = ImageOps.fit(img, (side, side))
        mask = Image.new("L", (side, side), 0)
        from PIL import ImageDraw
        ImageDraw.Draw(mask).ellipse((0, 0, side - 1, side - 1), fill=255)
        img.putalpha(mask)
    img.thumbnail((512, 512), Image.LANCZOS)
    w, h = img.size  # bir tomoni aniq 512 bo'lishi kerak
    k = 512 / max(w, h)
    img = img.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="WEBP", quality=90)
    return out.getvalue()


def kb(lang):
    return menu(lang, [TX["b_pack"][lang], TX["b_help"][lang]])


def sticker_kb(lang):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TX["add"][lang], callback_data="st:add")],
                                                 [InlineKeyboardButton(text=TX["round"][lang], callback_data="st:round")]])


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

    @r.message(F.text.in_(variants(TX["b_pack"])))
    async def my_pack(m: Message):
        lang = get_lang(KEY, m.from_user.id)
        with db() as con:
            row = con.execute("SELECT * FROM stickers WHERE user_id=?", (m.from_user.id,)).fetchone()
        if not row:
            return await m.answer(TX["no_pack"][lang])
        await m.answer(TX["pack"][lang].format(n=row["count"], link=f"https://t.me/addstickers/{row['set_name']}"))

    @r.message(F.photo | (F.document & F.document.mime_type.startswith("image/")))
    async def photo(m: Message, bot: Bot):
        lang = touch(KEY, m.from_user)
        src = m.photo[-1] if m.photo else m.document
        buf = io.BytesIO()
        await bot.download(src, destination=buf)
        raw = buf.getvalue()
        msg = await m.answer_sticker(BufferedInputFile(to_sticker(raw), "sticker.webp"), reply_markup=sticker_kb(lang))
        LAST[m.from_user.id] = {"raw": raw, "file_id": msg.sticker.file_id}
        count(KEY, "sticker")

    @r.callback_query(F.data == "st:round")
    async def round_(c: CallbackQuery):
        lang = get_lang(KEY, c.from_user.id)
        last = LAST.get(c.from_user.id)
        if not last:
            return await c.answer(TX["gone"][lang], show_alert=True)
        msg = await c.message.answer_sticker(BufferedInputFile(to_sticker(last["raw"], True), "round.webp"),
                                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                                                 InlineKeyboardButton(text=TX["add"][lang], callback_data="st:add")]]))
        last["file_id"] = msg.sticker.file_id
        await c.answer()

    @r.callback_query(F.data == "st:add")
    async def add(c: CallbackQuery, bot: Bot):
        lang = get_lang(KEY, c.from_user.id)
        file_id = c.message.sticker.file_id if c.message.sticker else (LAST.get(c.from_user.id) or {}).get("file_id")
        if not file_id:
            return await c.answer(TX["gone"][lang], show_alert=True)
        uid = c.from_user.id
        name = f"p{uid}_by_{USERNAME}"
        st = InputSticker(sticker=file_id, format="static", emoji_list=["😎"])
        with db() as con:
            row = con.execute("SELECT * FROM stickers WHERE user_id=?", (uid,)).fetchone()
        try:
            if row:
                await bot.add_sticker_to_set(user_id=uid, name=name, sticker=st)
            else:
                title = f"{c.from_user.first_name[:40]} — Birzumda"
                await bot.create_new_sticker_set(user_id=uid, name=name, title=title, stickers=[st])
        except Exception as e:
            return await c.message.answer(TX["err"][lang].format(e=str(e)[:150]))
        with db() as con:
            con.execute("""INSERT INTO stickers(user_id, set_name, count) VALUES(?,?,1)
                           ON CONFLICT(user_id) DO UPDATE SET count=count+1""", (uid, name))
        count(KEY, "pack_add")
        await c.message.answer(TX["added"][lang].format(link=f"https://t.me/addstickers/{name}"))
        await c.answer("✅")

    @r.message(F.text & ~F.text.startswith("/"))
    async def other(m: Message):
        await m.answer(TX["send_photo"][touch(KEY, m.from_user)])

    return r


async def on_lang(msg: Message, lang: str):
    await msg.answer("👇", reply_markup=kb(lang))
