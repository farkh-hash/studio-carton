import asyncio
import tempfile
import os
import io

VOICE = "fr-FR-DeniseNeural"


async def _edge_tts(text: str) -> bytes:
    import edge_tts
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    try:
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(tmp.name)
        with open(tmp.name, "rb") as f:
            data = f.read()
        if not data:
            raise ValueError("empty audio from edge-tts")
        return data
    finally:
        try:
            os.remove(tmp.name)
        except Exception:
            pass


def _gtts_fallback(text: str) -> bytes:
    from gtts import gTTS
    buf = io.BytesIO()
    gTTS(text=text, lang="fr", slow=False).write_to_fp(buf)
    return buf.getvalue()


async def generate_audio(text: str) -> bytes:
    try:
        return await _edge_tts(text)
    except Exception as e:
        print(f"[TTS] edge-tts failed ({e}), fallback to gTTS")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _gtts_fallback, text)
