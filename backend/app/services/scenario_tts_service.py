import asyncio
import tempfile
import os


async def _generate_line_audio(line: str, voice: str) -> bytes:
    """Génère l'audio pour une réplique avec la voix du personnage."""
    import edge_tts

    audio_chunks = []
    communicate = edge_tts.Communicate(line, voice, rate="-3%")

    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
    except Exception:
        # Fallback save method
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        try:
            await asyncio.wait_for(communicate.save(tmp.name), timeout=15)
            with open(tmp.name, "rb") as f:
                return f.read()
        finally:
            try:
                os.remove(tmp.name)
            except Exception:
                pass

    audio = b"".join(audio_chunks)
    if not audio:
        raise ValueError(f"Audio vide pour: {line}")
    return audio


async def _gtts_line(line: str) -> bytes:
    """Fallback gTTS pour une réplique."""
    import io
    from gtts import gTTS
    buf = io.BytesIO()
    gTTS(text=line, lang="fr", slow=False).write_to_fp(buf)
    return buf.getvalue()


async def generate_scenario_audio(scenario: dict) -> list[dict]:
    """
    Génère l'audio pour chaque réplique du scénario.
    Retourne une liste de segments avec audio_bytes, character, line, voice.
    """
    segments = []

    # Collecter toutes les répliques dans l'ordre
    all_dialogues = []
    for scene in scenario.get("scenes", []):
        for dialogue in scene.get("dialogues", []):
            all_dialogues.append(dialogue)

    # Ajouter le CTA comme dernière réplique (voix ALEX par défaut)
    if scenario.get("cta"):
        all_dialogues.append({
            "character": "ALEX",
            "line": scenario["cta"],
            "voice": "fr-FR-HenriNeural",
            "emotion": "engageant"
        })

    # Générer audio pour chaque réplique
    for i, dialogue in enumerate(all_dialogues):
        line = dialogue.get("line", "").strip()
        voice = dialogue.get("voice", "fr-FR-DeniseNeural")
        character = dialogue.get("character", "")

        if not line:
            continue

        # Essayer edge-tts d'abord, fallback gTTS
        try:
            audio = await asyncio.wait_for(
                _generate_line_audio(line, voice),
                timeout=20
            )
        except Exception as e:
            print(f"[SCENARIO TTS] edge-tts failed pour {character}: {e}, fallback gTTS")
            try:
                loop = asyncio.get_running_loop()
                audio = await loop.run_in_executor(None, lambda l=line: _gtts_sync(l))
            except Exception:
                continue

        segments.append({
            "character": character,
            "line": line,
            "voice": voice,
            "emotion": dialogue.get("emotion", ""),
            "audio_bytes": audio,
            "duration_estimate": len(line.split()) / 2.5,  # ~2.5 mots/sec
        })
        print(f"[SCENARIO TTS] Segment {i+1}/{len(all_dialogues)}: {character} - {len(audio)} bytes")

    return segments


def _gtts_sync(text: str) -> bytes:
    import io
    from gtts import gTTS
    buf = io.BytesIO()
    gTTS(text=text, lang="fr", slow=False).write_to_fp(buf)
    return buf.getvalue()
