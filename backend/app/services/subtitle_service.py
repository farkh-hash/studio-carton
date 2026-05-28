import re
from dataclasses import dataclass
from typing import List


@dataclass
class SubtitleChunk:
    text: str
    start: float
    end: float


def build_subtitles(script: str, audio_duration: float, words_per_chunk: int = 5) -> List[SubtitleChunk]:
    words = re.split(r"\s+", script.strip())
    words = [w for w in words if w]

    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunks.append(" ".join(words[i : i + words_per_chunk]))

    if not chunks:
        return []

    chunk_duration = audio_duration / len(chunks)
    result = []
    for idx, text in enumerate(chunks):
        start = idx * chunk_duration
        end = start + chunk_duration - 0.1
        result.append(SubtitleChunk(text=text, start=round(start, 2), end=round(end, 2)))

    return result


def to_srt(chunks: List[SubtitleChunk]) -> str:
    def fmt(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(str(i))
        lines.append(f"{fmt(chunk.start)} --> {fmt(chunk.end)}")
        lines.append(chunk.text)
        lines.append("")
    return "\n".join(lines)
