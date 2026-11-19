# Birzumda botlari

Bitta Railway servisida bir nechta Telegram bot (xotira tejaladi).

| Bot | Vazifa |
|---|---|
| @Birzumda_Lotin_bot | Kirill ↔ lotin: matn, .docx, .txt |
| @Birzumda_Hisob_bot | Valyuta kurslari (CBU), konvertor, QR, kredit |
| @Birzumda_Stiker_bot | Rasmdan stiker, shaxsiy stikerpak |
| @Birzumda_Musiqa_bot | Videodan / ovozli xabardan MP3 |
| @Birzumda_Eslatma_bot | Eslatmalar, dars jadvali, ertalabki reja |

## Muhit o'zgaruvchilari
- `TOKEN_LOTIN`, `TOKEN_HISOB`, `TOKEN_STIKER`, `TOKEN_MUSIQA`, `TOKEN_ESLATMA` — bot tokenlari (yo'q bo'lsa, bot ishga tushmaydi)
- `DB_PATH` — SQLite baza (Railway volume: `/data/bots.db`)
- `ADMIN_ID` — admin Telegram ID (`/stats` buyrug'i uchun)

Yangi bot qo'shish: `bots/` ichiga modul (`KEY`, `USERNAME`, `make_router()`, `on_lang()`), `main.py` dagi `MODULES` ga qo'shing.
