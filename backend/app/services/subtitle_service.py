import re
from dataclasses import dataclass
from typing import List


@dataclass
class SubtitleChunk:
    text: str
    start: float
    end: float


def build_subtitles_from_words(words: list, words_per_chunk: int = 1) -> List[SubtitleChunk]:
    """Sous-titres synchronisés mot à mot via les timestamps edge-tts.
    words_per_chunk=1 : style viral TikTok mot par mot.
    Durée minimum 0.2s par chunk pour garantir la lisibilité."""
    if not words:
        return []

    MIN_DURATION = 0.2

    chunks = []
    for i in range(0, len(words), words_per_chunk):
        group = words[i:i + words_per_chunk]
        text = " ".join(w["word"] for w in group)
        start = group[0]["start"]
        raw_end = group[-1]["end"] + 0.05
        # Garantir durée minimum lisible
        end = max(raw_end, start + MIN_DURATION)
        chunks.append(SubtitleChunk(
            text=text,
            start=round(start, 3),
            end=round(end, 3),
        ))

    return chunks


def build_subtitles(script: str, audio_duration: float, words_per_chunk: int = 3) -> List[SubtitleChunk]:
    """Fallback : découpage temporel égal (utilisé quand pas de timestamps)."""
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
