import httpx
import asyncio
import json
from groq import Groq
from app.core.config import settings
from datetime import date

# Base de données des niches monétisables avec données réelles 2025-2026
NICHE_MONETISATION_DATA = {
    "finance_personnelle": {
        "tiktok_rpm": (0.40, 1.20),
        "youtube_rpm": (0.10, 0.25),
        "affiliate_programs": [
            {"name": "ClickBank formations finance", "commission": "50-75%", "avg_sale": "97€"},
            {"name": "Boursorama / Trade Republic", "commission": "50-120€ par inscription", "avg_sale": "80€"},
            {"name": "Audible (livres finance)", "commission": "5€ par inscription", "avg_sale": "10€"},
        ],
        "brand_deal_rate": {"10k": "200-500€", "100k": "1500-3000€"},
        "competition": "élevée",
        "barrier_to_entry": "faible",
    },
    "ia_outils_digitaux": {
        "tiktok_rpm": (0.35, 0.90),
        "youtube_rpm": (0.08, 0.20),
        "affiliate_programs": [
            {"name": "Jasper AI", "commission": "30% récurrent", "avg_sale": "49€/mois"},
            {"name": "Notion / Monday.com", "commission": "20-40% récurrent", "avg_sale": "20€/mois"},
            {"name": "MidJourney / formations IA", "commission": "40-60%", "avg_sale": "97€"},
        ],
        "brand_deal_rate": {"10k": "300-600€", "100k": "2000-4000€"},
        "competition": "moyenne",
        "barrier_to_entry": "faible",
    },
    "entrepreneuriat_side_hustle": {
        "tiktok_rpm": (0.30, 0.80),
        "youtube_rpm": (0.08, 0.18),
        "affiliate_programs": [
            {"name": "Shopify", "commission": "150€ par inscription", "avg_sale": "150€"},
            {"name": "Systeme.io", "commission": "40% récurrent", "avg_sale": "47€/mois"},
            {"name": "Formations business ClickBank", "commission": "50-75%", "avg_sale": "197€"},
        ],
        "brand_deal_rate": {"10k": "250-500€", "100k": "1500-3000€"},
        "competition": "élevée",
        "barrier_to_entry": "faible",
    },
    "sante_bien_etre": {
        "tiktok_rpm": (0.25, 0.70),
        "youtube_rpm": (0.05, 0.15),
        "affiliate_programs": [
            {"name": "iHerb / compléments", "commission": "10-20%", "avg_sale": "50€"},
            {"name": "MyProtein / Foodspring", "commission": "8-15%", "avg_sale": "60€"},
            {"name": "Applications fitness", "commission": "20-40% récurrent", "avg_sale": "15€/mois"},
        ],
        "brand_deal_rate": {"10k": "200-400€", "100k": "1000-2500€"},
        "competition": "très élevée",
        "barrier_to_entry": "moyenne",
    },
    "immobilier_investissement": {
        "tiktok_rpm": (0.50, 1.50),
        "youtube_rpm": (0.15, 0.40),
        "affiliate_programs": [
            {"name": "Robinhood / eToro", "commission": "30-80€ par inscription", "avg_sale": "50€"},
            {"name": "Formations immobilier", "commission": "50-70%", "avg_sale": "497€"},
            {"name": "Crowdfunding immobilier", "commission": "50-100€ par investisseur", "avg_sale": "75€"},
        ],
        "brand_deal_rate": {"10k": "400-800€", "100k": "3000-6000€"},
        "competition": "moyenne",
        "barrier_to_entry": "faible",
    },
    "creation_contenu_personal_brand": {
        "tiktok_rpm": (0.20, 0.60),
        "youtube_rpm": (0.05, 0.12),
        "affiliate_programs": [
            {"name": "Canva Pro", "commission": "20% récurrent", "avg_sale": "13€/mois"},
            {"name": "Formations créateurs", "commission": "40-60%", "avg_sale": "297€"},
            {"name": "Outils IA création", "commission": "25-40% récurrent", "avg_sale": "30€/mois"},
        ],
        "brand_deal_rate": {"10k": "150-350€", "100k": "1000-2000€"},
        "competition": "très élevée",
        "barrier_to_entry": "faible",
    },
}


def _estimate_monthly_revenue(niche_data: dict, subscribers: int = 50000, views_per_month: int = 500000) -> dict:
    """Estime le revenu mensuel pour une niche à un niveau d'audience donné."""
    tiktok_rpm_min, tiktok_rpm_max = niche_data["tiktok_rpm"]
    yt_rpm_min, yt_rpm_max = niche_data["youtube_rpm"]

    # Creator Fund TikTok (vues / 1000 * RPM)
    tiktok_fund_min = (views_per_month / 1000) * tiktok_rpm_min
    tiktok_fund_max = (views_per_month / 1000) * tiktok_rpm_max

    # YouTube Shorts (moins généreux)
    yt_min = (views_per_month / 1000) * yt_rpm_min * 0.3  # 30% des vues sur YT
    yt_max = (views_per_month / 1000) * yt_rpm_max * 0.3

    # Affiliation (estimation conservative : 0.1% conversion, 50€ commission moyenne)
    affiliate_min = views_per_month * 0.001 * 0.01 * 50  # 1% clics, 1% conversion
    affiliate_max = views_per_month * 0.002 * 0.02 * 80

    # Brand deals (1-2 par mois selon la taille)
    sub_key = "10k" if subscribers < 50000 else "100k"
    brand_range = niche_data["brand_deal_rate"].get(sub_key, "0€")
    brand_parts = brand_range.replace("€", "").split("-")
    brand_min = int(brand_parts[0]) * (1 if subscribers < 50000 else 2)
    brand_max = int(brand_parts[-1]) * (1 if subscribers < 50000 else 2)

    return {
        "tiktok_fund": f"{int(tiktok_fund_min)}-{int(tiktok_fund_max)}€",
        "youtube": f"{int(yt_min)}-{int(yt_max)}€",
        "affiliation": f"{int(affiliate_min)}-{int(affiliate_max)}€",
        "brand_deals": f"{brand_min}-{brand_max}€",
        "total_min": int(tiktok_fund_min + yt_min + affiliate_min + brand_min),
        "total_max": int(tiktok_fund_max + yt_max + affiliate_max + brand_max),
    }


async def _search_affiliate_opportunities(niche: str) -> list[str]:
    """Cherche des opportunités affiliées actuelles sur Google."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    query = f"meilleur programme affiliation {niche} 2025 commission"
    try:
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            resp = await client.get("https://www.google.com/search", params={"q": query, "num": 5, "hl": "fr"})
            import re
            titles = re.findall(r'<h3[^>]*>(.*?)</h3>', resp.text, re.DOTALL)
            import re as re2
            return [re2.sub(r'<[^>]+>', '', t).strip() for t in titles[:4] if len(t) > 10]
    except Exception:
        return []


async def analyze_monetisation(target_subscribers: int = 50000) -> dict:
    """
    Analyse complète des meilleures niches à monétiser.
    Classement par revenu potentiel réel estimé.
    """
    today = date.today().strftime("%d/%m/%Y")
    print(f"[MONETISATION] Analyse au {today} pour {target_subscribers:,} abonnés cible")

    # Calculer les revenus pour chaque niche
    niche_revenues = []
    for niche_key, data in NICHE_MONETISATION_DATA.items():
        views = target_subscribers * 10  # estimation 10 vues/abonné/mois
        revenue = _estimate_monthly_revenue(data, target_subscribers, views)
        niche_revenues.append({
            "key": niche_key,
            "data": data,
            "revenue": revenue,
        })

    # Trier par revenu max potentiel
    niche_revenues.sort(key=lambda x: x["revenue"]["total_max"], reverse=True)

    # Chercher des opportunités affiliées en parallèle pour top 3
    top_niches = niche_revenues[:3]
    affiliate_tasks = [_search_affiliate_opportunities(n["key"].replace("_", " ")) for n in top_niches]
    affiliate_results = await asyncio.gather(*affiliate_tasks, return_exceptions=True)

    # Analyse Groq avec fallback automatique
    from app.services.groq_client import chat_fast as groq_chat

    niche_context = json.dumps([
        {
            "niche": n["key"],
            "revenu_mensuel_estime": n["revenue"],
            "competition": n["data"]["competition"],
            "programmes_affiliation": [p["name"] for p in n["data"]["affiliate_programs"]],
        }
        for n in niche_revenues
    ], ensure_ascii=False, indent=2)

    prompt = f"""Date : {today}
Cible : {target_subscribers:,} abonnés sur TikTok/YouTube

Analyse ces niches par potentiel de monétisation et retourne un JSON :
{{
  "top_niches": [
    {{
      "rank": 1,
      "niche": "nom de la niche",
      "score_monetisation": 9,
      "revenu_mensuel_estime": "800-2400€/mois",
      "why_monetisable": "Raison précise pourquoi cette niche rapporte (données réelles)",
      "quick_win": "Action concrète pour gagner les 1ers euros en moins de 30 jours",
      "content_strategy": "Type de contenu exact à créer pour monétiser (3 formats)",
      "best_affiliate": "Meilleur programme affilié avec commission exacte",
      "tiktok_path": "Chemin exact vers la monétisation TikTok pour cette niche",
      "competition_gap": "Ce qui manque dans cette niche (opportunité non exploitée)",
      "example_topics": ["Sujet vidéo 1 qui convertit", "Sujet 2", "Sujet 3"]
    }}
  ],
  "recommended_niche": "La niche #1 à choisir maintenant et pourquoi",
  "first_30_days_plan": [
    "Action jour 1-7",
    "Action jour 8-14",
    "Action jour 15-21",
    "Action jour 22-30"
  ],
  "revenue_milestone": "Combien peut-on espérer gagner après 90 jours de contenus réguliers"
}}

Données niches :
{niche_context}

Sois précis avec des chiffres réels. JSON uniquement."""

    raw = groq_chat(messages=[{"role": "user", "content": prompt}], max_tokens=2500, temperature=0.5)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        analysis = json.loads(raw.strip())
    except Exception:
        analysis = {"top_niches": [], "recommended_niche": "", "first_30_days_plan": []}

    analysis["date"] = today
    analysis["target_subscribers"] = target_subscribers
    analysis["niche_revenues_raw"] = {
        n["key"]: n["revenue"] for n in niche_revenues
    }
    return analysis
