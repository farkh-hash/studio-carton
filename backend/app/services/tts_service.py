import asyncio
import tempfile
import os
import io
import re

VOICES = [
    "fr-FR-DeniseNeural",
    "fr-FR-HenriNeural",
    "fr-FR-EloiseNeural",
]
EDGE_TTS_TIMEOUT = 25  # secondes max par voix


_UNITS = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
          "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept",
          "dix-huit", "dix-neuf"]
_TENS = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante",
         "soixante", "quatre-vingt", "quatre-vingt"]


def _int_to_fr(n: int) -> str:
    if n < 0:
        return "moins " + _int_to_fr(-n)
    if n == 0:
        return "zéro"
    if n < 20:
        return _UNITS[n]
    if n < 70:
        t, u = divmod(n, 10)
        return _TENS[t] + ("-" + _UNITS[u] if u else "")
    if n < 80:
        return "soixante-" + _int_to_fr(n - 60)
    if n < 100:
        u = n - 80
        return "quatre-vingt" + ("-" + _int_to_fr(u) if u else "s")
    if n < 1000:
        h, r = divmod(n, 100)
        return (_int_to_fr(h) + " cent" + ("s" if r == 0 and h > 1 else "") +
                (" " + _int_to_fr(r) if r else ""))
    if n < 1_000_000:
        m, r = divmod(n, 1000)
        return ((_int_to_fr(m) + " mille" if m > 1 else "mille") +
                (" " + _int_to_fr(r) if r else ""))
    return str(n)


def _preprocess_for_tts(text: str) -> str:
    """Convertit les chiffres, symboles et abréviations pour une lecture TTS naturelle."""
    # Pourcentages : "73%" → "soixante-treize pourcent"
    def replace_pct(m):
        try:
            return _int_to_fr(int(m.group(1))) + " pourcent"
        except Exception:
            return m.group(0)
    text = re.sub(r'(\d+)\s*%', replace_pct, text)

    # Euros : "500€" ou "500 €" → "cinq cents euros"
    def replace_eur(m):
        try:
            return _int_to_fr(int(m.group(1))) + " euros"
        except Exception:
            return m.group(0)
    text = re.sub(r'(\d+)\s*€', replace_eur, text)

    # Nombres isolés : "73" → "soixante-treize"
    def replace_num(m):
        try:
            n = int(m.group(0))
            if n > 10_000:
                return m.group(0)
            return _int_to_fr(n)
        except Exception:
            return m.group(0)
    text = re.sub(r'\b(\d+)\b', replace_num, text)

    # Abréviations courantes
    text = re.sub(r'\bvs\b', 'versus', text, flags=re.IGNORECASE)
    text = re.sub(r'\betc\b\.?', 'et cetera', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmax\b', 'maximum', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmin\b', 'minimum', text, flags=re.IGNORECASE)

    return text


def _clean_text(text: str) -> str:
    text = _preprocess_for_tts(text)
    text = re.sub(r'[^\w\s\.,;:!?\'\-àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:4500] if len(text) > 4500 else text


async def _run_edge_tts(text: str, voice: str) -> tuple[bytes, list]:
    import edge_tts

    audio_chunks = []
    word_boundaries = []

    communicate = edge_tts.Communicate(text, voice, rate="-3%")

    # Utilise .stream() pour la compatibilité avec toutes les versions
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            start = chunk["offset"] / 10_000_000
            duration = chunk["duration"] / 10_000_000
            word_boundaries.append({
                "word": chunk["value"],
                "start": round(start, 3),
                "end": round(start + duration, 3),
            })

    audio_bytes = b"".join(audio_chunks)
    if not audio_bytes or len(audio_bytes) < 1000:
        raise ValueError(f"Audio vide ({len(audio_bytes)} bytes)")

    return audio_bytes, word_boundaries


async def _edge_tts(text: str) -> tuple[bytes, list]:
    text = _clean_text(text)
    for voice in VOICES:
        try:
            audio, words = await asyncio.wait_for(
                _run_edge_tts(text, voice),
                timeout=EDGE_TTS_TIMEOUT
            )
            print(f"[TTS] edge-tts OK — {voice} — {len(audio)} bytes — {len(words)} mots")
            return audio, words
        except asyncio.TimeoutError:
            print(f"[TTS] {voice} timeout après {EDGE_TTS_TIMEOUT}s")
        except Exception as e:
            print(f"[TTS] {voice} échec: {e}")
    raise ValueError("Toutes les voix edge-tts ont échoué")


def _gtts_fallback(text: str) -> bytes:
    from gtts import gTTS
    text = _clean_text(text)
    buf = io.BytesIO()
    gTTS(text=text, lang="fr", slow=False).write_to_fp(buf)
    print(f"[TTS] gTTS fallback — {len(buf.getvalue())} bytes")
    return buf.getvalue()


async def generate_audio(text: str) -> tuple[bytes, list]:
    try:
        return await _edge_tts(text)
    except Exception as e:
        print(f"[TTS] edge-tts indisponible ({e}), fallback gTTS")
        loop = asyncio.get_running_loop()
        audio = await loop.run_in_executor(None, _gtts_fallback, text)
        return audio, []
