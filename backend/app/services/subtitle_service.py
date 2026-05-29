import re
from dataclasses import dataclass
from typing import List


@dataclass
class SubtitleChunk:
    text: str
    start: float
    end: float


def build_subtitles(script: str, audio_duration: float, words_per_chunk: int = 3) -> List[SubtitleChunk]:
    words = re.split(r"\s+", script.strip())
    words = [w for w in words if w]

    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunks.append(" ".join(words[i: i + words_per_chunk]))

    if not chunks:
        return []

    chunk_duration = audio_duration / len(chunks)
    result = []
    for idx, text in enumerate(chunks):
        start = idx * chunk_duration
        end = start + chunk_duration - 0.05
        result.append(SubtitleChunk(text=text, start=round(start, 3), end=round(end, 3)))

    return result
