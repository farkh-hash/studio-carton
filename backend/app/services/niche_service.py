from groq import Groq
from app.core.config import settings
import json
from datetime import date

# Niches classées par potentiel de monétisation — données 2025-2026
# Source : TikTok Creator Rewards, YouTube RPM, brand deals, affiliate commissions
NICHES_WITH_DATA = [
    {
        "niche": "finances personnelles et investissement",
        "monetisation": "TikTok Rewards $0.40-1.00/1000 vues + affiliate ClickBank 50-75% + brand deals 1500-5000€",
        "rpm_relatif": "10x vs contenu général",
    },
    {
        "niche": "entrepreneuriat et business en ligne",
        "monetisation": "Brand deals + formations + affiliate SaaS 20-40% récurrent",
        "rpm_relatif": "8x vs contenu général",
    },
    {
        "niche": "santé longévité et bien-être premium",
        "monetisation": "TikTok Shop 15-20% commission + supplements affiliate + brand deals santé",
        "rpm_relatif": "8x vs contenu général",
    },
    {
        "niche": "IA et outils digitaux",
        "monetisation": "Affiliate SaaS 20-40% récurrent + formation + brand deals tech",
        "rpm_relatif": "6x vs contenu général",
    },
    {
        "niche": "développement personnel et productivité",
        "monetisation": "Formations 50-75% commission + brand deals + TikTok Rewards",
        "rpm_relatif": "5x vs contenu général",
    },
    {
        "niche": "psychologie et relations humaines",
        "monetisation": "Brand deals bien-être + formations + affiliate livres",
        "rpm_relatif": "4x vs contenu général",
    },
    {
        "niche": "alimentation régime et nutrition",
        "monetisation": "TikTok Shop compléments + affiliate Amazon + brand deals food",
        "rpm_relatif": "4x vs contenu général",
    },
    {
        "niche": "éducation rapide et faits surprenants",
        "monetisation": "YouTube Shorts RPM $0.05-0.08 + TikTok Rewards + sponsoring",
        "rpm_relatif": "4x vs contenu général",
    },
    {
        "niche": "lifestyle minimalisme et habitudes",
        "monetisation": "Brand deals lifestyle + affiliate Amazon + formation",
        "rpm_relatif": "3x vs contenu général",
    },
    {
        "niche": "création de contenu et personal branding",
        "monetisation": "Formation créateurs + affiliate outils + coaching",
        "rpm_relatif": "6x vs contenu général",
    },
]

SYSTEM_PROMPT = """Tu es un stratège de contenu viral expert en monétisation pour TikTok, YouTube Shorts et Instagram Reels.
Tu analyses les niches avec des données précises sur la rentabilité, la croissance et les stratégies de contenu.
Tu réponds toujours en JSON valide uniquement."""


def analyze_niches() -> list[dict]:
    from app.services.groq_client import chat as groq_chat
    today = date.today().strftime("%d/%m/%Y")

    niche_context = json.dumps(
        [{"niche": n["niche"], "monetisation": n["monetisation"]} for n in NICHES_WITH_DATA],
        ensure_ascii=False
    )

    prompt = f"""Date : {today}

Analyse ces 10 niches pour un créateur francophone voulant aller viral et se monétiser.
Données de monétisation réelles fournies pour chaque niche.

Niches avec données : {niche_context}

Pour chaque niche retourne un objet JSON avec exactement ces champs :
- "niche" : nom de la niche
- "emoji" : 1 emoji représentatif
- "score" : note de 1 à 10 (potentiel viral + monétisation combinés)
- "why" : 1 phrase — pourquoi cette niche performe EN CE MOMENT
- "best_platform" : "TikTok" ou "YouTube" ou "Instagram" (meilleure plateforme)
- "posting_frequency" : fréquence optimale (ex: "3-5x/semaine")
- "monetisation_resume" : résumé court de la monétisation en 1 phrase (montants réels)
- "content_angle" : angle éditorial unique et différenciant
- "topics" : liste de 3 objets avec :
  - "title" : sujet accrocheur et spécifique (pas générique)
  - "hook" : première phrase d'accroche (max 12 mots, choc immédiat, formule prouvée)
  - "format" : "30s" ou "60s" ou "90s"
  - "hashtags" : 5 hashtags sans #

RÈGLES ABSOLUES pour les hooks :
- Maximum 10 mots par hook
- PAS de formule générique comme "Découvrez...", "Apprenez...", "Voici..."
- INTERDIT : faux témoignages ("Je suis passé de X à Y"), résultats inventés, promesses de revenus
- Utilise UNE de ces formules validées basées sur des FAITS VÉRIFIABLES :
  * Chiffre précis : "[X]% des gens ignorent ça. Et ça change tout."
  * Contre-intuitif : "[Chose commune] est ce qui empêche [résultat]."
  * Urgence factuelle : "Ce que [experts/études] disent sur [concept] va te surprendre."
  * Révélation : "La vraie raison pour laquelle [croyance populaire] est fausse."
  * Erreur commune : "Arrête de [action courante]. Voici pourquoi."
- Crée une boucle ouverte : le spectateur DOIT regarder la suite
- Chiffres précis uniquement si vérifiables (statistiques réelles, données connues)

Retourne UNIQUEMENT un tableau JSON valide sans texte autour."""

    raw = groq_chat(messages=[{"role": "user", "content": prompt}], system=SYSTEM_PROMPT, max_tokens=4000, temperature=0.75)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw.strip())
    return sorted(data, key=lambda x: x.get("score", 0), reverse=True)


def generate_script_from_topic(topic: str, hook: str, niche: str, format_duration: str, style: str = "viral") -> str:
    from app.services.groq_client import chat as groq_chat

    duration_map = {"30s": 30, "60s": 60, "90s": 90, "2min": 120, "3min": 180}
    duration = duration_map.get(format_duration, 60)
    content_seconds = duration - 10

    prompt = f"""Crée un script viral de {duration} secondes.

SUJET : {topic}
NICHE : {niche}
HOOK IMPOSÉ — commence EXACTEMENT par : "{hook}"

STRUCTURE :
1. HOOK (3-5s) : le hook imposé mot pour mot
2. CONTENU ({content_seconds}s) : faits précis avec chiffres, rythme rapide, boucles ouvertes entre chaque point
3. CTA (5-7s) : question engageante + abonne-toi, naturel

RÈGLES :
- Commence par le hook exact, aucune modification
- Phrases max 8-10 mots
- Chiffres et faits précis et vérifiables uniquement
- Uniquement le texte à lire à voix haute
- Pas d'annotations, tirets ou numéros
- Langage parlé naturel
- Chaque phrase crée l'envie d'entendre la suivante (boucle ouverte)
- INTERDIT : faux témoignages perso, promesses de revenus garantis, résultats inventés"""

    return groq_chat(messages=[{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.85)
