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


def _clean_text(text: str) -> str:
    text = re.sub(r'[^\w\s\.,;:!?\'\"\-\(\)àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:4500] if len(text) > 4500 else text


async def _run_edge_tts(text: str, voice: str) -> tuple[bytes, list]:
    import edge_tts

    audio_chunks = []
    word_boundaries = []

    communicate = edge_tts.Communicate(text, voice, rate="+5%")

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
        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(None, _gtts_fallback, text)
        return audio, []
