"""
Prompt builder pour LTX-Video 2B (T5-XXL, limite ~512 tokens).
Génère des prompts motion-first optimisés pour vidéo virale TikTok/Reels.
"""
import re

# T5-XXL supporte des prompts beaucoup plus longs qu'un CLIP 77 tokens
MAX_PROMPT_CHARS = 600

STYLE_BASE = (
    "3D cartoon animation style, vibrant saturated colors, smooth fluid motion, "
    "cinematic quality, 9:16 vertical format, studio-quality lighting"
)

NEGATIVE_BASE = (
    "worst quality, inconsistent motion, blurry, jittery, watermark, text overlay, "
    "deformed characters, bad anatomy, low resolution, static, frozen"
)

MOOD_MODIFIERS = {
    "fun": "playful comedic action, exaggerated funny expressions, bouncy movement",
    "dramatic": "dramatic cinematic motion, epic sweeping camera, intense expression",
    "cute": "adorable kawaii motion, soft gentle movement, heartwarming scene",
    "epic": "action-packed dynamic movement, hero pose reveal, explosive energy",
    "chill": "relaxed smooth movement, golden hour atmosphere, peaceful scene",
}

STYLE_VARIANTS = {
    "classic": "classic cartoon animation style",
    "neon": "neon glowing cyberpunk cartoon, vibrant neon colors",
    "nature": "lush nature scene, forest environment, organic earthy tones",
    "urban": "city backdrop, urban environment, street scene",
    "space": "cosmic space scene, stars and nebula, zero gravity",
}

_IGNORE_PATTERNS = [
    r'\[\d+[–\-]\d+\s*s[^\]]*\]',
    r'format\s+\d+:\d+',
    r'\d+K',
    r'likes?|commentaires?|abonnements?',
    r'encourage|adapté|compatible|boucle',
]


def extract_visual_scene(raw: str) -> str:
    """Extrait les éléments visuels clés pour LTX-Video depuis un prompt long."""
    text = re.sub(r'\[[^\]]*\]', ' ', raw)
    for pat in _IGNORE_PATTERNS:
        text = re.sub(pat, ' ', text, flags=re.IGNORECASE)

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    visual_lines = []
    for line in lines:
        if any(w in line.lower() for w in [
            'chat', 'pigeon', 'cat', 'bird', 'balcon', 'balcony',
            'gris', 'foulard', 'lunettes', 'thon', 'animation',
            'cartoon', 'cute', 'adorable', 'expressi', 'character',
            'personnage', 'scene', 'scène', 'move', 'jump', 'run'
        ]):
            visual_lines.append(line)
        if len(' '.join(visual_lines)) > MAX_PROMPT_CHARS - 100:
            break

    if visual_lines:
        scene = ' '.join(visual_lines[:3])
    else:
        scene = ' '.join(text.split())[:MAX_PROMPT_CHARS - 100]

    return scene[:MAX_PROMPT_CHARS - 100].rsplit(' ', 1)[0]


def build_animatediff_prompt(raw_topic: str, mood: str = "fun", style_variant: str = "classic") -> str:
    """Construit un prompt riche et optimisé pour LTX-Video 2B."""
    if len(raw_topic) <= MAX_PROMPT_CHARS - 100 and '\n' not in raw_topic:
        core = raw_topic
    else:
        core = extract_visual_scene(raw_topic)

    mood_mod = MOOD_MODIFIERS.get(mood, MOOD_MODIFIERS["fun"])
    style_mod = STYLE_VARIANTS.get(style_variant, STYLE_VARIANTS["classic"])

    prompt = f"{core}, {style_mod}, {mood_mod}, {STYLE_BASE}"

    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[:MAX_PROMPT_CHARS].rsplit(',', 1)[0]

    return prompt


def build_viral_prompt(topic: str, mood: str = "fun", style_variant: str = "classic") -> str:
    return build_animatediff_prompt(topic, mood, style_variant)


def build_negative_prompt() -> str:
    return NEGATIVE_BASE
