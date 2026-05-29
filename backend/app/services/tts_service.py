import asyncio
import tempfile
import os
import edge_tts

VOICE = "fr-FR-DeniseNeural"


async def generate_audio(text: str) -> bytes:
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    try:
        communicate = edge_tts.Communicate(text, VOICE, rate="+10%")
        await communicate.save(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(tmp.name)
        except Exception:
            pass
