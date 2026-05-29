import asyncio
import tempfile
import os
import io
import re

VOICES = [
    "fr-FR-DeniseNeural",
    "fr-FR-HenriNeural",
    "fr-FR-VivienneMultilingualNeural",
    "fr-FR-EloiseNeural",
]


def _clean_text(text: str) -> str:
    text = re.sub(r'[^\w\s\.,;:!?\'\"\-\(\)àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:4500] if len(text) > 4500 else text


async def _edge_tts_with_timing(text: str, voice: str) -> tuple[bytes, list]:
    """Retourne (audio_mp3_bytes, word_boundaries).
    word_boundaries = [{"word": str, "start": float, "end": float}, ...]
    """
    import edge_tts

    audio_chunks = []
    word_boundaries = []

    communicate = edge_tts.Communicate(text, voice, rate="+5%")

    async for chunk in asyncio.wait_for(communicate.__aiter__().__anext__(), timeout=60) if False else communicate:
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            # offset et duration sont en unités de 100 nanosecondes
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

    print(f"[TTS] edge-tts OK — {voice} — {len(audio_bytes)} bytes — {len(word_boundaries)} mots")
    return audio_bytes, word_boundaries


async def _edge_tts(text: str) -> tuple[bytes, list]:
    text = _clean_text(text)
    last_err = None
    for voice in VOICES:
        try:
            return await _edge_tts_with_timing(text, voice)
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
    print(f"[TTS] gTTS fallback — {len(buf.getvalue())} bytes")
    return buf.getvalue()


async def generate_audio(text: str) -> tuple[bytes, list]:
    """Retourne (audio_bytes, word_boundaries). word_boundaries peut être vide (fallback gTTS)."""
    try:
        return await _edge_tts(text)
    except Exception as e:
        print(f"[TTS] edge-tts indisponible ({e}), fallback gTTS")
        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(None, _gtts_fallback, text)
        return audio, []  # gTTS n'a pas de timestamps
