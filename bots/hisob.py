"""🧮 Birzumda Hisob — valyuta kurslari (O'zbekiston Markaziy banki), konvertor, QR kod, kredit kalkulyatori."""
import io
import re
import time

import aiohttp
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import BufferedInputFile, Message

from common import LANGS, count, get_lang, menu, touch, tr

KEY, USERNAME = "hisob", "Birzumda_Hisob_bot"
CBU_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
MAIN = ["USD", "EUR", "RUB", "KZT", "GBP", "CNY", "TRY", "KRW", "AED", "JPY"]
FLAGS = {"USD": "🇺🇸", "EUR": "🇪🇺", "RUB": "🇷🇺", "KZT": "🇰🇿", "GBP": "🇬🇧", "CNY": "🇨🇳", "TRY": "🇹🇷", "KRW": "🇰🇷",
         "AED": "🇦🇪", "JPY": "🇯🇵", "UZS": "🇺🇿"}
ALIASES = {"$": "USD", "dollar": "USD", "доллар": "USD", "usd": "USD", "€": "EUR", "evro": "EUR", "евро": "EUR",
           "rubl": "RUB", "рубль": "RUB", "руб": "RUB", "₽": "RUB", "som": "UZS", "so'm": "UZS", "sum": "UZS", "сум": "UZS",
           "сўм": "UZS", "uzs": "UZS", "tenge": "KZT", "тенге": "KZT", "yuan": "CNY", "юань": "CNY", "lira": "TRY"}

TX = {
    "start": {"uz": "👋 Salom, <b>{name}</b>!\n\n🧮 Men kundalik hisob-kitobga yordam beraman:\n\n"
                    "💵 <b>Valyuta kurslari</b> — Markaziy bank kursi\n🔄 <b>Konvertor</b> — masalan: <code>100 usd</code> yoki <code>1000000 so'm eur</code>\n"
                    "📱 <b>QR kod</b> — havola yoki matndan QR\n🏦 <b>Kredit</b> — oylik to'lovni hisoblash",
              "ru": "👋 Привет, <b>{name}</b>!\n\n🧮 Помогаю с ежедневными расчётами:\n\n"
                    "💵 <b>Курсы валют</b> — курс Центробанка Узбекистана\n🔄 <b>Конвертер</b> — например: <code>100 usd</code> или <code>1000000 сум eur</code>\n"
                    "📱 <b>QR-код</b> — из ссылки или текста\n🏦 <b>Кредит</b> — расчёт ежемесячного платежа",
              "en": "👋 Hi, <b>{name}</b>!\n\n🧮 I help with everyday calculations:\n\n"
                    "💵 <b>Exchange rates</b> — Central Bank of Uzbekistan\n🔄 <b>Converter</b> — e.g. <code>100 usd</code> or <code>1000000 sum eur</code>\n"
                    "📱 <b>QR code</b> — from a link or text\n🏦 <b>Loan</b> — monthly payment calculator"},
    "b_rates": {"uz": "💵 Valyuta kurslari", "ru": "💵 Курсы валют", "en": "💵 Exchange rates"},
    "b_conv": {"uz": "🔄 Konvertor", "ru": "🔄 Конвертер", "en": "🔄 Converter"},
    "b_qr": {"uz": "📱 QR kod", "ru": "📱 QR-код", "en": "📱 QR code"},
    "b_loan": {"uz": "🏦 Kredit", "ru": "🏦 Кредит", "en": "🏦 Loan"},
    "rates_t": {"uz": "💵 <b>Markaziy bank kursi</b> ({date})\n\n", "ru": "💵 <b>Курс Центробанка</b> ({date})\n\n",
                "en": "💵 <b>Central Bank rates</b> ({date})\n\n"},
    "conv_h": {"uz": "🔄 Summa va valyutani yozing, masalan:\n<code>100 usd</code>\n<code>250 eur</code>\n<code>1 000 000 so'm usd</code>",
               "ru": "🔄 Напишите сумму и валюту, например:\n<code>100 usd</code>\n<code>250 eur</code>\n<code>1 000 000 сум usd</code>",
               "en": "🔄 Type an amount and currency, e.g.:\n<code>100 usd</code>\n<code>250 eur</code>\n<code>1 000 000 sum usd</code>"},
    "qr_h": {"uz": "📱 QR kod uchun havola yoki matn yuboring.", "ru": "📱 Отправьте ссылку или текст для QR-кода.",
             "en": "📱 Send a link or text for the QR code."},
    "qr_ok": {"uz": "✅ QR kod tayyor", "ru": "✅ QR-код готов", "en": "✅ QR code ready"},
    "loan_h": {"uz": "🏦 Uch sonni yozing: <b>summa</b>, <b>oylar</b>, <b>yillik foiz</b>.\nMasalan: <code>50000000 24 24</code>",
               "ru": "🏦 Напишите три числа: <b>сумма</b>, <b>месяцы</b>, <b>годовой %</b>.\nНапример: <code>50000000 24 24</code>",
               "en": "🏦 Type three numbers: <b>amount</b>, <b>months</b>, <b>annual %</b>.\nExample: <code>50000000 24 24</code>"},
    "loan_r": {"uz": "🏦 <b>Kredit hisob-kitobi</b>\n\nSumma: <b>{p}</b>\nMuddat: <b>{n} oy</b>\nFoiz: <b>{r}%</b> yillik\n\n"
                     "💳 Oylik to'lov: <b>{m}</b>\n💰 Jami to'lov: <b>{t}</b>\n📈 Ortiqcha to'lov: <b>{o}</b>\n\n<i>Annuitet (teng to'lov) usulida. Bank shartlari farq qilishi mumkin.</i>",
               "ru": "🏦 <b>Расчёт кредита</b>\n\nСумма: <b>{p}</b>\nСрок: <b>{n} мес.</b>\nСтавка: <b>{r}%</b> годовых\n\n"
                     "💳 Ежемесячный платёж: <b>{m}</b>\n💰 Всего выплат: <b>{t}</b>\n📈 Переплата: <b>{o}</b>\n\n<i>Аннуитетный платёж. Условия банка могут отличаться.</i>",
               "en": "🏦 <b>Loan calculation</b>\n\nAmount: <b>{p}</b>\nTerm: <b>{n} months</b>\nRate: <b>{r}%</b> per year\n\n"
                     "💳 Monthly payment: <b>{m}</b>\n💰 Total paid: <b>{t}</b>\n📈 Overpayment: <b>{o}</b>\n\n<i>Annuity method. Bank terms may differ.</i>"},
    "no_rates": {"uz": "😕 Kurslarni hozir olib bo'lmadi, birozdan keyin urinib ko'ring.",
                 "ru": "😕 Не удалось получить курсы, попробуйте чуть позже.", "en": "😕 Couldn't get rates, try again shortly."},
    "unknown": {"uz": "Tushunmadim 🤔 Pastdagi tugmalardan birini tanlang.", "ru": "Не понял 🤔 Выберите кнопку ниже.",
                "en": "I didn't get that 🤔 Choose a button below."},
}

MODE: dict[int, str] = {}  # 'conv' | 'qr' | 'loan'
_rates = {"t": 0.0, "data": {}, "date": ""}


async def rates() -> dict:
    if time.time() - _rates["t"] < 3600 and _rates["data"]:
        return _rates["data"]
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as s:
        async with s.get(CBU_URL) as resp:
            data = await resp.json(content_type=None)
    _rates["data"] = {d["Ccy"]: (float(d["Rate"]) / float(d.get("Nominal") or 1), float(d.get("Diff") or 0)) for d in data}
    _rates["date"] = data[0].get("Date", "") if data else ""
    _rates["t"] = time.time()
    return _rates["data"]


def fmt(n: float, cur: str = "UZS") -> str:
    s = f"{n:,.2f}".replace(",", " ").rstrip("0").rstrip(".")
    return f"{s} {'so‘m' if cur == 'UZS' else cur}"


def parse_conv(text: str):
    """'100 usd', '1 000 000 so'm eur', '$50' → (summa, dan, ga)."""
    t = text.lower().replace(",", ".").strip()
    num = re.search(r"\d[\d\s.]*", t)
    if not num:
        return None
    amount = float(re.sub(r"\s", "", num.group()).rstrip(".") or 0)
    words = re.findall(r"[a-zа-яўқғҳ'‘’$€₽]+|[$€₽]", t)
    curs = []
    for w in words:
        w = w.replace("‘", "'").replace("’", "'")
        c = ALIASES.get(w) or (w.upper() if len(w) == 3 and w.isascii() and w.isalpha() else None)
        if c:
            curs.append(c)
    if not curs:
        return None
    src = curs[0]
    dst = curs[1] if len(curs) > 1 else ("UZS" if src != "UZS" else "USD")
    return amount, src, dst


def loan(p: float, n: int, rate: float):
    i = rate / 12 / 100
    m = p / n if i == 0 else p * i * (1 + i) ** n / ((1 + i) ** n - 1)
    return m, m * n, m * n - p


def qr_png(text: str) -> bytes:
    import qrcode
    img = qrcode.make(text, box_size=10, border=3)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def kb(lang):
    return menu(lang, [TX["b_rates"][lang], TX["b_conv"][lang], TX["b_qr"][lang], TX["b_loan"][lang]])


def make_router() -> Router:
    r = Router(name=KEY)

    @r.message(CommandStart())
    async def start(m: Message):
        lang = touch(KEY, m.from_user)
        MODE.pop(m.from_user.id, None)
        await m.answer(tr(TX["start"], lang, name=m.from_user.first_name), reply_markup=kb(lang))

    @r.message(F.text.in_({TX["b_rates"][x] for x in LANGS}))
    async def show_rates(m: Message):
        lang = get_lang(KEY, m.from_user.id)
        try:
            data = await rates()
        except Exception:
            return await m.answer(TX["no_rates"][lang])
        count(KEY, "rates")
        lines = []
        for c in MAIN:
            if c in data:
                rate, diff = data[c]
                arrow = "🔺" if diff > 0 else "🔻" if diff < 0 else "▫️"
                lines.append(f"{FLAGS.get(c, '')} <b>1 {c}</b> = {fmt(rate)}  {arrow}{abs(diff):g}")
        await m.answer(TX["rates_t"][lang].format(date=_rates["date"]) + "\n".join(lines) + "\n\n⚡ @" + USERNAME)

    @r.message(F.text.in_({TX["b_conv"][x] for x in LANGS}))
    async def conv_mode(m: Message):
        MODE[m.from_user.id] = "conv"
        await m.answer(TX["conv_h"][get_lang(KEY, m.from_user.id)])

    @r.message(F.text.in_({TX["b_qr"][x] for x in LANGS}))
    async def qr_mode(m: Message):
        MODE[m.from_user.id] = "qr"
        await m.answer(TX["qr_h"][get_lang(KEY, m.from_user.id)])

    @r.message(F.text.in_({TX["b_loan"][x] for x in LANGS}))
    async def loan_mode(m: Message):
        MODE[m.from_user.id] = "loan"
        await m.answer(TX["loan_h"][get_lang(KEY, m.from_user.id)])

    @r.message(F.text & ~F.text.startswith("/"))
    async def any_text(m: Message):
        lang = touch(KEY, m.from_user)
        mode = MODE.get(m.from_user.id)
        if mode == "qr":
            count(KEY, "qr")
            return await m.answer_photo(BufferedInputFile(qr_png(m.text[:1500]), "qr.png"), caption=TX["qr_ok"][lang] + "\n⚡ @" + USERNAME)
        if mode == "loan":
            nums = [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?", m.text.replace(" ", " "))]
            if len(nums) >= 3 and nums[0] > 0 and 0 < nums[1] <= 600:
                p, n, rate = nums[0], int(nums[1]), nums[2]
                mo, tot, over = loan(p, n, rate)
                count(KEY, "loan")
                return await m.answer(TX["loan_r"][lang].format(p=fmt(p), n=n, r=f"{rate:g}", m=fmt(round(mo)), t=fmt(round(tot)), o=fmt(round(over))))
            return await m.answer(TX["loan_h"][lang])
        parsed = parse_conv(m.text)
        if parsed:
            amount, src, dst = parsed
            try:
                data = await rates()
            except Exception:
                return await m.answer(TX["no_rates"][lang])
            to_uzs = amount if src == "UZS" else amount * data.get(src, (0, 0))[0]
            res = to_uzs if dst == "UZS" else (to_uzs / data[dst][0] if dst in data and data[dst][0] else None)
            if src != "UZS" and src not in data or res is None:
                return await m.answer(TX["conv_h"][lang])
            count(KEY, "convert")
            return await m.answer(f"{FLAGS.get(src, '')} <b>{fmt(amount, src)}</b> = {FLAGS.get(dst, '')} <b>{fmt(res, dst)}</b>\n"
                                  f"<i>{_rates['date']}</i>")
        if mode == "conv":
            return await m.answer(TX["conv_h"][lang])
        await m.answer(TX["unknown"][lang], reply_markup=kb(lang))

    return r


async def on_lang(msg: Message, lang: str):
    await msg.answer("👇", reply_markup=kb(lang))
