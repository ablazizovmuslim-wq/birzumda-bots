"""🎵 Birzumda Musiqa — videodan, ovozli xabardan va dumaloq videodan MP3 ajratib beradi."""
import asyncio
import os
import tempfile

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message

from common import variants, LANGS, count, get_lang, menu, touch, tr

KEY, USERNAME = "musiqa", "Birzumda_Musiqa_bot"
MAX_MB = 20  # oddiy Telegram Bot API yuklab olish chegarasi

TX = {
    "start": {"uz": "👋 Salom, <b>{name}</b>!\n\n🎵 Menga <b>video</b>, <b>dumaloq video</b> yoki <b>ovozli xabar</b> yuboring — "
                    "undan <b>MP3</b> ajratib beraman.\n\n📥 Videoni Instagram, YouTube yoki TikTok'dan yuklash kerakmi? → @Birzumda_Yukla_bot",
              "ru": "👋 Привет, <b>{name}</b>!\n\n🎵 Отправьте <b>видео</b>, <b>кружок</b> или <b>голосовое</b> — "
                    "достану из него <b>MP3</b>.\n\n📥 Нужно скачать видео из Instagram, YouTube или TikTok? → @Birzumda_Yukla_bot",
              "en": "👋 Hi, <b>{name}</b>!\n\n🎵 Send a <b>video</b>, <b>video note</b> or <b>voice message</b> — "
                    "I'll extract the <b>MP3</b>.\n\n📥 Need to download a video from Instagram, YouTube or TikTok? → @Birzumda_Yukla_bot"},
    "b_help": {"uz": "❓ Qanday ishlaydi", "ru": "❓ Как работает", "en": "❓ How it works"},
    "b_yukla": {"uz": "📥 Video yuklash", "ru": "📥 Скачать видео", "en": "📥 Download video"},
    "wait": {"uz": "⏳ MP3 tayyorlanmoqda…", "ru": "⏳ Готовлю MP3…", "en": "⏳ Making your MP3…"},
    "big": {"uz": "😕 Fayl juda katta ({mb} MB). {max} MB gacha yuboring.", "ru": "😕 Файл слишком большой ({mb} МБ). Отправьте до {max} МБ.",
            "en": "😕 The file is too large ({mb} MB). Please send up to {max} MB."},
    "err": {"uz": "😕 Bu fayldan ovoz ajratib bo'lmadi.", "ru": "😕 Не удалось извлечь звук из этого файла.",
            "en": "😕 Couldn't extract audio from this file."},
    "send": {"uz": "🎬 Video yoki ovozli xabar yuboring.", "ru": "🎬 Отправьте видео или голосовое сообщение.",
             "en": "🎬 Send a video or a voice message."},
    "yukla": {"uz": "📥 Videolarni yuklash uchun: @Birzumda_Yukla_bot", "ru": "📥 Чтобы скачать видео: @Birzumda_Yukla_bot",
              "en": "📥 To download videos: @Birzumda_Yukla_bot"},
}


def kb(lang):
    return menu(lang, [TX["b_yukla"][lang], TX["b_help"][lang]])


async def to_mp3(src: str, dst: str) -> bool:
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "2", "-b:a", "192k", dst,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    try:
        await asyncio.wait_for(proc.wait(), timeout=180)
    except asyncio.TimeoutError:
        proc.kill()
        return False
    return proc.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 0


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

    @r.message(F.text.in_(variants(TX["b_yukla"])))
    async def yukla(m: Message):
        await m.answer(TX["yukla"][get_lang(KEY, m.from_user.id)])

    @r.message(F.video | F.video_note | F.voice | F.audio | (F.document & (F.document.mime_type.startswith("video/")
                                                                          | F.document.mime_type.startswith("audio/"))))
    async def media(m: Message, bot: Bot):
        lang = touch(KEY, m.from_user)
        src = m.video or m.video_note or m.voice or m.audio or m.document
        size = (src.file_size or 0) / 1024 / 1024
        if size > MAX_MB:
            return await m.answer(TX["big"][lang].format(mb=round(size), max=MAX_MB))
        note = await m.answer(TX["wait"][lang])
        with tempfile.TemporaryDirectory() as tmp:  # fayllar darhol o'chiriladi — xotira tejaladi
            inp, out = os.path.join(tmp, "in"), os.path.join(tmp, "out.mp3")
            await bot.download(src, destination=inp)
            ok = await to_mp3(inp, out)
            if not ok:
                return await note.edit_text(TX["err"][lang])
            title = (getattr(src, "file_name", None) or "Birzumda").rsplit(".", 1)[0][:60]
            await m.answer_audio(FSInputFile(out, filename=f"{title}.mp3"), title=title, performer="Birzumda",
                                 caption="⚡ @" + USERNAME)
        await note.delete()
        count(KEY, "mp3")

    @r.message(F.text & ~F.text.startswith("/"))
    async def other(m: Message):
        await m.answer(TX["send"][touch(KEY, m.from_user)])

    return r


async def on_lang(msg: Message, lang: str):
    await msg.answer("👇", reply_markup=kb(lang))
