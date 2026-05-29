import io
import asyncio
from gtts import gTTS


def _generate_sync(text: str) -> bytes:
    tts = gTTS(text=text, lang="fr", slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    return buf.getvalue()


async def generate_audio(text: str) -> bytes:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _generate_sync, text)
