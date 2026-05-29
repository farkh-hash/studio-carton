import { useState } from "react";
import axios from "axios";

export default function LandingPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await axios.post("/api/users/login", { email: email.trim() });
      localStorage.setItem("sc_user", JSON.stringify(res.data));
      onLogin(res.data);
    } catch {
      setError("Erreur de connexion. Réessaie.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="landing">
      {/* Hero */}
      <section className="hero">
        <div className="hero-badge">🚀 IA · 100% Automatique</div>
        <h1 className="hero-title">
          Crée des vidéos virales<br />
          <span className="gradient-text">en 3 minutes</span>
        </h1>
        <p className="hero-sub">
          Entre un sujet → notre IA génère le script, la voix, les sous-titres et la vidéo 9:16 prête pour TikTok, Reels et Shorts.
        </p>

        <form className="hero-form" onSubmit={handleLogin}>
          <input
            type="email"
            placeholder="ton@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? "..." : "Commencer gratuitement →"}
          </button>
        </form>
        {error && <p className="hero-error">{error}</p>}
        <p className="hero-note">✅ 3 vidéos gratuites · Aucune carte requise</p>
      </section>

      {/* Features */}
      <section className="features">
        <h2>Comment ça marche</h2>
        <div className="features-grid">
          {[
            { icon: "🤖", title: "Agent Niches", desc: "L'IA analyse les meilleures niches virales du moment et te propose 10 sujets optimisés." },
            { icon: "✍️", title: "Script IA", desc: "Groq (Llama 3.3) génère un script percutant avec hook fort, contenu dense et CTA." },
            { icon: "🎙️", title: "Voix naturelle", desc: "Synthèse vocale française de qualité professionnelle, naturelle et dynamique." },
            { icon: "🎬", title: "Vidéo HD 9:16", desc: "Clips Pexels en fond, sous-titres jaunes animés, format parfait pour tous les réseaux." },
          ].map((f, i) => (
            <div key={i} className="feature-card">
              <span className="feature-icon">{f.icon}</span>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="pricing">
        <h2>Tarifs simples</h2>
        <div className="pricing-grid">
          <div className="plan-card">
            <div className="plan-name">Gratuit</div>
            <div className="plan-price">0€</div>
            <ul className="plan-features">
              <li>✅ 3 vidéos offertes</li>
              <li>✅ Agent Niches</li>
              <li>✅ Tous les formats (30s → 3min)</li>
              <li>✅ Fond vidéo Pexels HD</li>
            </ul>
            <button className="plan-btn outline" onClick={handleLogin}>Commencer</button>
          </div>
          <div className="plan-card featured">
            <div className="plan-badge">⭐ Populaire</div>
            <div className="plan-name">Pro</div>
            <div className="plan-price">9€<span>/mois</span></div>
            <ul className="plan-features">
              <li>✅ Vidéos illimitées</li>
              <li>✅ Génération en batch</li>
              <li>✅ Priorité de traitement</li>
              <li>✅ Support prioritaire</li>
            </ul>
            <button className="plan-btn" onClick={handleLogin}>Passer Pro</button>
          </div>
        </div>
      </section>
    </div>
  );
}
