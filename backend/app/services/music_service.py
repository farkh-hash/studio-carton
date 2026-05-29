import asyncio
import httpx
import tempfile
import os
import random

TRACKS = {
    "viral": [
        "https://assets.mixkit.co/music/download/mixkit-hazy-after-hours-132.mp3",
        "https://assets.mixkit.co/music/download/mixkit-deep-urban-623.mp3",
        "https://assets.mixkit.co/music/download/mixkit-hip-hop-02-738.mp3",
    ],
    "educational": [
        "https://assets.mixkit.co/music/download/mixkit-life-is-a-dream-837.mp3",
        "https://assets.mixkit.co/music/download/mixkit-dreaming-big-31.mp3",
    ],
    "storytelling": [
        "https://assets.mixkit.co/music/download/mixkit-life-is-a-dream-837.mp3",
        "https://assets.mixkit.co/music/download/mixkit-hazy-after-hours-132.mp3",
    ],
    "humour": [
        "https://assets.mixkit.co/music/download/mixkit-hip-hop-02-738.mp3",
        "https://assets.mixkit.co/music/download/mixkit-deep-urban-623.mp3",
    ],
}


async def fetch_music(style: str) -> str | None:
    urls = TRACKS.get(style, TRACKS["viral"])
    random.shuffle(urls)
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for url in urls:
            try:
                r = await client.get(url)
                r.raise_for_status()
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                tmp.write(r.content)
                tmp.close()
                print(f"[MUSIC] Downloaded: {url.split('/')[-1]}")
                return tmp.name
            except Exception as e:
                print(f"[MUSIC] Failed {url}: {e}")
                continue
    return None
