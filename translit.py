"""O'zbek tili: kirill ↔ lotin (1995-yilgi rasmiy imlo qoidalari asosida)."""
import re

OK = "ʻ"   # oʻ, gʻ uchun (U+02BB)
TUT = "ʼ"  # tutuq belgisi — ъ (U+02BC)

C2L = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z", "и": "i", "й": "y",
    "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": TUT, "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ў": "o" + OK, "қ": "q", "ғ": "g" + OK, "ҳ": "h", "ы": "i",
}
VOWELS_CYR = set("аеёиоуэюяўАЕЁИОУЭЮЯЎ")


def _case(src: str, out: str, word_upper: bool) -> str:
    if not src.isupper():
        return out
    return out.upper() if word_upper or len(out) == 1 else out[0].upper() + out[1:]


def cyr_to_lat(text: str) -> str:
    res = []
    for word in re.split(r"(\W+)", text):
        if not word:
            continue
        letters = [ch for ch in word if ch.isalpha()]
        upper = len(letters) > 1 and all(ch.isupper() for ch in letters)
        out = []
        for i, ch in enumerate(word):
            low = ch.lower()
            if low == "е":  # so'z boshida, unlidan yoki ъ/ь dan keyin — "ye"
                prev = word[i - 1] if i else ""
                t = "ye" if (i == 0 or prev in VOWELS_CYR or prev.lower() in "ъь") else "e"
            elif low == "ц":  # unlilar orasida "ts", boshqa joyda "s"
                prev, nxt = (word[i - 1] if i else ""), (word[i + 1] if i + 1 < len(word) else "")
                t = "ts" if prev in VOWELS_CYR and nxt in VOWELS_CYR else "s"
            elif low in C2L:
                t = C2L[low]
            else:
                out.append(ch)
                continue
            out.append(_case(ch, t, upper) if t else t)
        res.append("".join(out))
    return "".join(res)


# lotin → kirill: avval ikki harfli birikmalar
APOS = "ʻʼ'`’‘"
L2C_DI = [("o" + a, "ў") for a in APOS] + [("g" + a, "ғ") for a in APOS] + [
    ("sh", "ш"), ("ch", "ч"), ("yo", "ё"), ("yu", "ю"), ("ya", "я"), ("ye", "е")]
L2C = {"a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ", "i": "и", "j": "ж", "k": "к",
       "l": "л", "m": "м", "n": "н", "o": "о", "p": "п", "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у",
       "v": "в", "x": "х", "y": "й", "z": "з", "c": "ц", "w": "в"}


def lat_to_cyr(text: str) -> str:
    out, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        two = text[i:i + 2]
        word_start = i == 0 or not text[i - 1].isalpha() and text[i - 1] not in APOS
        hit = next((c for d, c in L2C_DI if two.lower() == d), None)
        # s'h / s’h → сҳ (ajratish belgisi)
        if two.lower() in ("s" + a for a in APOS) and i + 2 < n and text[i + 2].lower() == "h":
            out.append("С" if ch.isupper() else "с"); i += 2; continue
        if hit:
            out.append(hit.upper() if ch.isupper() else hit)
            i += 2
            continue
        low = ch.lower()
        if ch in APOS:  # ikki harf orasida — tutuq belgisi ъ (ma'no → маъно, san'at → санъат)
            prev, nxt = (text[i - 1] if i else ""), (text[i + 1] if i + 1 < n else "")
            out.append("ъ" if prev.isalpha() and nxt.isalpha() else ch)
            i += 1
            continue
        if low == "e" and word_start:
            t = "э"
        elif low in L2C:
            t = L2C[low]
        else:
            out.append(ch); i += 1; continue
        out.append(t.upper() if ch.isupper() else t)
        i += 1
    return "".join(out)


def detect(text: str) -> str:
    """'cyr' yoki 'lat' — qaysi alifbo ko'p bo'lsa."""
    cyr = sum(1 for ch in text if "Ѐ" <= ch <= "ӿ")
    lat = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    return "cyr" if cyr >= lat else "lat"


def convert(text: str, to: str | None = None) -> tuple[str, str]:
    """Matnni o'giradi. to: 'lat' / 'cyr' / None (avtomatik). Natija va yo'nalish qaytadi."""
    to = to or ("lat" if detect(text) == "cyr" else "cyr")
    return (cyr_to_lat(text) if to == "lat" else lat_to_cyr(text)), to
