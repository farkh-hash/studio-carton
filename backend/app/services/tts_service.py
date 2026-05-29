import asyncio
import tempfile
import os
import io
import re

# Voix françaises Microsoft Neural (par ordre de préférence)
VOICES = [
    "fr-FR-DeniseNeural",
    "fr-FR-HenriNeural",
    "fr-FR-VivienneMultilingualNeural",
    "fr-FR-EloiseNeural",
]


def _clean_text(text: str) -> str:
    """Nettoie le texte pour éviter les erreurs TTS."""
    # Remplacer les caractères spéciaux non supportés
    text = re.sub(r'[^\w\s\.,;:!?\'\"\-\(\)àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]', ' ', text)
    # Normaliser les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    # Limiter la longueur par segment (edge-tts gère mieux les textes < 5000 chars)
    return text[:4500] if len(text) > 4500 else text


async def _try_edge_tts(text: str, voice: str) -> bytes:
    import edge_tts
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    try:
        communicate = edge_tts.Communicate(text, voice, rate="+5%", volume="+0%")
        await asyncio.wait_for(communicate.save(tmp.name), timeout=30)
        with open(tmp.name, "rb") as f:
            data = f.read()
        if not data or len(data) < 1000:
            raise ValueError(f"Audio vide ou trop court ({len(data)} bytes)")
        return data
    finally:
        try:
            os.remove(tmp.name)
        except Exception:
            pass


async def _edge_tts(text: str) -> bytes:
    text = _clean_text(text)
    last_err = None
    for voice in VOICES:
        try:
            data = await _try_edge_tts(text, voice)
            print(f"[TTS] edge-tts OK — voix: {voice} — {len(data)} bytes")
            return data
        except Exception as e:
            print(f"[TTS] {voice} échec: {e}")
            last_err = e
            continue
    raise ValueError(f"Toutes les voix edge-tts ont échoué: {last_err}")


def _gtts_fallback(text: str) -> bytes:
    from gtts import gTTS
    text = _clean_text(text)
    buf = io.BytesIO()
    gTTS(text=text, lang="fr", slow=False).write_to_fp(buf)
    return buf.getvalue()


async def generate_audio(text: str) -> bytes:
    try:
        return await _edge_tts(text)
    except Exception as e:
        print(f"[TTS] edge-tts indisponible ({e}), fallback gTTS")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _gtts_fallback, text)
