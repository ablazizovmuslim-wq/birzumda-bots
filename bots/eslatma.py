"""⏰ Birzumda Eslatma — eslatmalar va dars jadvali, ertalab kunlik reja (Toshkent vaqti)."""
import asyncio
import html
import re
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from common import variants, LANGS, count, db, get_lang, log, menu, now_local, touch, tr

KEY, USERNAME = "eslatma", "Birzumda_Eslatma_bot"
FMT = "%Y-%m-%d %H:%M"

WD = {  # hafta kunlari: 0 = dushanba
    0: ("du", "dushanba", "пн", "понедельник", "mon", "monday"), 1: ("se", "seshanba", "вт", "вторник", "tue", "tuesday"),
    2: ("ch", "chorshanba", "ср", "среда", "wed", "wednesday"), 3: ("pa", "payshanba", "чт", "четверг", "thu", "thursday"),
    4: ("ju", "juma", "пт", "пятница", "fri", "friday"), 5: ("sh", "shanba", "сб", "суббота", "sat", "saturday"),
    6: ("ya", "yakshanba", "вс", "воскресенье", "sun", "sunday")}
WD_NAME = {"uz": ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"],
           "ru": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
           "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}

TX = {
    "start": {"uz": "👋 Salom, <b>{name}</b>!\n\n⏰ Men sizga hech narsani unutmaslikka yordam beraman.\n\n"
                    "✍️ <b>Eslatma</b> — shunchaki yozing:\n<code>18:30 Dars</code>\n<code>ertaga 9:00 Imtihon</code>\n"
                    "<code>25.11 14:00 Uchrashuv</code>\n<code>30 min Choy</code>\n\n📅 <b>Dars jadvali</b> — har kuni ertalab bugungi darslarni yuboraman.",
              "ru": "👋 Привет, <b>{name}</b>!\n\n⏰ Помогу ничего не забывать.\n\n"
                    "✍️ <b>Напоминание</b> — просто напишите:\n<code>18:30 Пара</code>\n<code>завтра 9:00 Экзамен</code>\n"
                    "<code>25.11 14:00 Встреча</code>\n<code>30 мин Чай</code>\n\n📅 <b>Расписание</b> — каждое утро пришлю пары на сегодня.",
              "en": "👋 Hi, <b>{name}</b>!\n\n⏰ I'll help you never forget anything.\n\n"
                    "✍️ <b>Reminder</b> — just type:\n<code>18:30 Class</code>\n<code>tomorrow 9:00 Exam</code>\n"
                    "<code>25.11 14:00 Meeting</code>\n<code>30 min Tea</code>\n\n📅 <b>Timetable</b> — every morning I'll send today's classes."},
    "b_list": {"uz": "📋 Eslatmalarim", "ru": "📋 Мои напоминания", "en": "📋 My reminders"},
    "b_sched": {"uz": "📅 Dars jadvali", "ru": "📅 Расписание", "en": "📅 Timetable"},
    "b_today": {"uz": "☀️ Bugun", "ru": "☀️ Сегодня", "en": "☀️ Today"},
    "b_help": {"uz": "❓ Qanday ishlaydi", "ru": "❓ Как работает", "en": "❓ How it works"},
    "saved": {"uz": "✅ Eslatma saqlandi!\n🗓 <b>{when}</b>\n📝 {text}", "ru": "✅ Напоминание сохранено!\n🗓 <b>{when}</b>\n📝 {text}",
              "en": "✅ Reminder saved!\n🗓 <b>{when}</b>\n📝 {text}"},
    "ring": {"uz": "⏰ <b>Eslatma!</b>\n\n{text}", "ru": "⏰ <b>Напоминание!</b>\n\n{text}", "en": "⏰ <b>Reminder!</b>\n\n{text}"},
    "none": {"uz": "Hozircha eslatmalar yo'q.", "ru": "Пока напоминаний нет.", "en": "No reminders yet."},
    "list": {"uz": "📋 <b>Eslatmalaringiz:</b>", "ru": "📋 <b>Ваши напоминания:</b>", "en": "📋 <b>Your reminders:</b>"},
    "del": {"uz": "🗑 O'chirildi", "ru": "🗑 Удалено", "en": "🗑 Deleted"},
    "bad": {"uz": "🤔 Vaqtni tushunmadim. Masalan: <code>18:30 Dars</code> yoki <code>ertaga 9:00 Imtihon</code>",
            "ru": "🤔 Не понял время. Например: <code>18:30 Пара</code> или <code>завтра 9:00 Экзамен</code>",
            "en": "🤔 I didn't get the time. E.g. <code>18:30 Class</code> or <code>tomorrow 9:00 Exam</code>"},
    "sched_h": {"uz": "📅 <b>Dars jadvali</b>\n\n{list}\n\n➕ Qo'shish uchun yozing (bir nechta qator mumkin):\n<code>Du 08:30 Matematika</code>\n<code>Se 10:00 Fizika</code>\n\n"
                      "🔔 Ertalabki xabar: <b>{dig}</b> ({time})\nVaqtni o'zgartirish: <code>/vaqt 06:30</code>",
                "ru": "📅 <b>Расписание</b>\n\n{list}\n\n➕ Чтобы добавить, напишите (можно несколько строк):\n<code>Пн 08:30 Математика</code>\n<code>Вт 10:00 Физика</code>\n\n"
                      "🔔 Утреннее сообщение: <b>{dig}</b> ({time})\nИзменить время: <code>/vaqt 06:30</code>",
                "en": "📅 <b>Timetable</b>\n\n{list}\n\n➕ To add, type (several lines are fine):\n<code>Mon 08:30 Math</code>\n<code>Tue 10:00 Physics</code>\n\n"
                      "🔔 Morning message: <b>{dig}</b> ({time})\nChange time: <code>/vaqt 06:30</code>"},
    "empty": {"uz": "<i>Jadval hali bo'sh</i>", "ru": "<i>Расписание пока пустое</i>", "en": "<i>Timetable is empty</i>"},
    "added_l": {"uz": "✅ Jadvalga {n} ta dars qo'shildi.", "ru": "✅ Добавлено пар: {n}.", "en": "✅ Added {n} class(es)."},
    "on": {"uz": "yoqilgan", "ru": "включено", "en": "on"}, "off": {"uz": "o'chirilgan", "ru": "выключено", "en": "off"},
    "toggle": {"uz": "🔔 Ertalabki xabar: yoqish/o'chirish", "ru": "🔔 Утреннее сообщение: вкл/выкл", "en": "🔔 Morning message: on/off"},
    "clear": {"uz": "🗑 Jadvalni tozalash", "ru": "🗑 Очистить расписание", "en": "🗑 Clear timetable"},
    "today_t": {"uz": "☀️ <b>Bugun — {day}</b>\n\n{list}", "ru": "☀️ <b>Сегодня — {day}</b>\n\n{list}", "en": "☀️ <b>Today — {day}</b>\n\n{list}"},
    "morning": {"uz": "🌅 Xayrli tong! Bugungi darslaringiz:\n\n{list}\n\nOmad! 💪", "ru": "🌅 Доброе утро! Сегодня у вас:\n\n{list}\n\nУдачи! 💪",
                "en": "🌅 Good morning! Today's classes:\n\n{list}\n\nGood luck! 💪"},
    "no_today": {"uz": "Bugun darslar yo'q 🎉", "ru": "Сегодня пар нет 🎉", "en": "No classes today 🎉"},
    "time_ok": {"uz": "✅ Ertalabki xabar vaqti: {t}", "ru": "✅ Время утреннего сообщения: {t}", "en": "✅ Morning message time: {t}"},
}

REL = re.compile(r"^(\d{1,3})\s*(min|daqiqa|daq|мин|минут\w*|m|soat|час\w*|h|hour\w*|kun|день|дн\w*|day\w*)\b\s*(.*)$", re.I | re.S)
TOMORROW = ("ertaga", "завтра", "tomorrow")


def parse_reminder(text: str, now: datetime):
    """Matndan (vaqt, eslatma matni) ajratadi. Vaqt Toshkent bo'yicha naive datetime."""
    t = text.strip()
    m = REL.match(t)
    if m:
        n, unit, rest = int(m.group(1)), m.group(2).lower(), m.group(3).strip()
        if unit.startswith(("soat", "час", "h")):
            delta = timedelta(hours=n)
        elif unit.startswith(("kun", "ден", "дн", "day")):
            delta = timedelta(days=n)
        else:
            delta = timedelta(minutes=n)
        return now + delta, rest or "⏰"
    day = now.date()
    low = t.lower()
    for w in TOMORROW:
        if low.startswith(w):
            day += timedelta(days=1)
            t = t[len(w):].strip()
            break
    explicit = False
    dm = re.match(r"^(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?\s+(?=\d{1,2}[:.]\d{2})", t)  # sana faqat vaqtdan oldin
    if dm:
        d, mo, y = int(dm.group(1)), int(dm.group(2)), dm.group(3)
        year = int(y) + (2000 if y and len(y) == 2 else 0) if y else now.year
        try:
            day = datetime(year, mo, d).date()
        except ValueError:
            return None
        explicit = True
        t = t[dm.end():]
    tm = re.match(r"^(\d{1,2})[:.](\d{2})\s*(.*)$", t, re.S)
    if not tm:
        return None
    h, mi = int(tm.group(1)), int(tm.group(2))
    if h > 23 or mi > 59:
        return None
    due = datetime.combine(day, datetime.min.time()).replace(hour=h, minute=mi)
    if due <= now and not explicit and day == now.date():
        due += timedelta(days=1)            # bugungi vaqt o'tib ketgan bo'lsa — ertaga
    if explicit and due <= now and not dm.group(3):
        due = due.replace(year=due.year + 1)
    return due, (tm.group(3).strip() or "⏰")


def parse_lessons(text: str):
    out = []
    for line in text.splitlines():
        m = re.match(r"^\s*([^\s\d]+)\.?\s+(\d{1,2})[:.](\d{2})\s+(.+)$", line.strip())
        if not m:
            continue
        w = m.group(1).lower()
        wd = next((k for k, names in WD.items() if w in names), None)
        if wd is None or int(m.group(2)) > 23 or int(m.group(3)) > 59:
            continue
        out.append((wd, f"{int(m.group(2)):02d}:{m.group(3)}", m.group(4).strip()[:100]))
    return out


def kb(lang):
    return menu(lang, [TX["b_list"][lang], TX["b_sched"][lang], TX["b_today"][lang], TX["b_help"][lang]])


def digest_row(uid):
    now = now_local()
    last = now.strftime("%Y-%m-%d") if now.strftime("%H:%M") >= "07:00" else ""  # bugungi ertalab o'tgan bo'lsa — ertadan
    with db() as con:
        con.execute("INSERT OR IGNORE INTO digest(user_id, last) VALUES(?,?)", (uid, last))
        return con.execute("SELECT * FROM digest WHERE user_id=?", (uid,)).fetchone()


def lessons_of(uid, wd=None):
    with db() as con:
        q = "SELECT * FROM lessons WHERE user_id=?" + (" AND weekday=?" if wd is not None else "") + " ORDER BY weekday, time"
        return con.execute(q, (uid, wd) if wd is not None else (uid,)).fetchall()


def lessons_text(rows, lang, with_day=True):
    lines, cur = [], None
    for r in rows:
        if with_day and r["weekday"] != cur:
            cur = r["weekday"]
            lines.append(f"\n<b>{WD_NAME[lang][cur]}</b>")
        lines.append(f"🕘 {r['time']} — {html.escape(r['text'])}")
    return "\n".join(lines).strip()


def make_router() -> Router:
    r = Router(name=KEY)

    async def show_sched(m: Message, uid: int, lang: str):
        d = digest_row(uid)
        rows = lessons_of(uid)
        await m.answer(TX["sched_h"][lang].format(list=lessons_text(rows, lang) or TX["empty"][lang],
                                                  dig=TX["on" if d["on_"] else "off"][lang], time=d["time"]),
                       reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                           [InlineKeyboardButton(text=TX["toggle"][lang], callback_data="es:tog")],
                           [InlineKeyboardButton(text=TX["clear"][lang], callback_data="es:clr")]]))

    @r.message(CommandStart())
    async def start(m: Message):
        lang = touch(KEY, m.from_user)
        await m.answer(tr(TX["start"], lang, name=m.from_user.first_name), reply_markup=kb(lang))

    @r.message(F.text.in_(variants(TX["b_help"])))
    async def help_(m: Message):
        lang = get_lang(KEY, m.from_user.id)
        await m.answer(tr(TX["start"], lang, name=m.from_user.first_name), reply_markup=kb(lang))

    @r.message(F.text.in_(variants(TX["b_list"])))
    async def my_list(m: Message):
        lang = get_lang(KEY, m.from_user.id)
        with db() as con:
            rows = con.execute("SELECT * FROM reminders WHERE user_id=? AND sent=0 ORDER BY due LIMIT 30", (m.from_user.id,)).fetchall()
        if not rows:
            return await m.answer(TX["none"][lang])
        await m.answer(TX["list"][lang], reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🗑 {r['due'][5:].replace('-', '.')} — {r['text'][:30]}", callback_data=f"es:d:{r['id']}")]
            for r in rows]))

    @r.callback_query(F.data.startswith("es:d:"))
    async def delete(c: CallbackQuery):
        with db() as con:
            con.execute("DELETE FROM reminders WHERE id=? AND user_id=?", (int(c.data.split(":")[2]), c.from_user.id))
        await c.answer(TX["del"][get_lang(KEY, c.from_user.id)])
        kb_ = [row for row in c.message.reply_markup.inline_keyboard if row[0].callback_data != c.data]
        await c.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_) if kb_ else None)

    @r.message(F.text.in_(variants(TX["b_sched"])))
    async def sched(m: Message):
        await show_sched(m, m.from_user.id, get_lang(KEY, m.from_user.id))

    @r.message(F.text.in_(variants(TX["b_today"])))
    async def today(m: Message):
        lang = get_lang(KEY, m.from_user.id)
        wd = now_local().weekday()
        rows = lessons_of(m.from_user.id, wd)
        await m.answer(TX["today_t"][lang].format(day=WD_NAME[lang][wd], list=lessons_text(rows, lang, False) or TX["no_today"][lang]))

    @r.callback_query(F.data == "es:tog")
    async def toggle(c: CallbackQuery):
        lang = get_lang(KEY, c.from_user.id)
        d = digest_row(c.from_user.id)
        with db() as con:
            con.execute("UPDATE digest SET on_=? WHERE user_id=?", (0 if d["on_"] else 1, c.from_user.id))
        await c.answer("🔔" if not d["on_"] else "🔕")
        await show_sched(c.message, c.from_user.id, lang)

    @r.callback_query(F.data == "es:clr")
    async def clear(c: CallbackQuery):
        with db() as con:
            con.execute("DELETE FROM lessons WHERE user_id=?", (c.from_user.id,))
        await c.answer("🗑")
        await show_sched(c.message, c.from_user.id, get_lang(KEY, c.from_user.id))

    @r.message(Command("vaqt"))
    async def set_time(m: Message):
        lang = get_lang(KEY, m.from_user.id)
        tm = re.search(r"(\d{1,2})[:.](\d{2})", m.text or "")
        if not tm or int(tm.group(1)) > 23 or int(tm.group(2)) > 59:
            return await m.answer("<code>/vaqt 06:30</code>")
        t = f"{int(tm.group(1)):02d}:{tm.group(2)}"
        digest_row(m.from_user.id)
        with db() as con:
            con.execute("UPDATE digest SET time=?, on_=1 WHERE user_id=?", (t, m.from_user.id))
        await m.answer(TX["time_ok"][lang].format(t=t))

    @r.message(F.text & ~F.text.startswith("/"))
    async def any_text(m: Message):
        lang = touch(KEY, m.from_user)
        lessons = parse_lessons(m.text)
        if lessons:
            with db() as con:
                con.executemany("INSERT INTO lessons(user_id, weekday, time, text) VALUES(?,?,?,?)",
                                [(m.from_user.id, *x) for x in lessons])
            digest_row(m.from_user.id)
            count(KEY, "lesson")
            return await m.answer(TX["added_l"][lang].format(n=len(lessons)))
        now = now_local().replace(tzinfo=None, second=0, microsecond=0)
        parsed = parse_reminder(m.text, now)
        if not parsed:
            return await m.answer(TX["bad"][lang])
        due, text = parsed
        with db() as con:
            con.execute("INSERT INTO reminders(user_id, due, text, created) VALUES(?,?,?,?)",
                        (m.from_user.id, due.strftime(FMT), text[:500], now.strftime(FMT)))
        count(KEY, "reminder")
        await m.answer(TX["saved"][lang].format(when=due.strftime("%d.%m.%Y %H:%M"), text=html.escape(text[:500])))

    return r


async def background(bot: Bot):
    """Har 20 soniyada: vaqti kelgan eslatmalar va ertalabki jadval."""
    while True:
        try:
            now = now_local().replace(tzinfo=None)
            stamp = now.strftime(FMT)
            with db() as con:
                due = con.execute("SELECT * FROM reminders WHERE sent=0 AND due<=? LIMIT 50", (stamp,)).fetchall()
                for r in due:
                    con.execute("UPDATE reminders SET sent=1 WHERE id=?", (r["id"],))
            for r in due:
                try:
                    await bot.send_message(r["user_id"], TX["ring"][get_lang(KEY, r["user_id"])].format(text=html.escape(r["text"])))
                except Exception as e:
                    log.info("eslatma yuborilmadi %s: %s", r["user_id"], e)
            hm, today = now.strftime("%H:%M"), now.strftime("%Y-%m-%d")
            with db() as con:
                users = con.execute("SELECT * FROM digest WHERE on_=1 AND time<=? AND last<>?", (hm, today)).fetchall()
                for d in users:
                    con.execute("UPDATE digest SET last=? WHERE user_id=?", (today, d["user_id"]))
            for d in users:
                rows = lessons_of(d["user_id"], now.weekday())
                if rows:
                    lang = get_lang(KEY, d["user_id"])
                    try:
                        await bot.send_message(d["user_id"], TX["morning"][lang].format(list=lessons_text(rows, lang, False)))
                    except Exception as e:
                        log.info("jadval yuborilmadi %s: %s", d["user_id"], e)
        except Exception as e:
            log.warning("eslatma sikli: %s", e)
        await asyncio.sleep(20)


async def on_lang(msg: Message, lang: str):
    await msg.answer("👇", reply_markup=kb(lang))

