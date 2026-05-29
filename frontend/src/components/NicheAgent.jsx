import { useState } from "react";
import axios from "axios";

const PLATFORM_COLOR = { TikTok: "#ff2d55", YouTube: "#ff0000", Instagram: "#e1306c" };

export default function NicheAgent({ onTopicSelect }) {
  const [niches, setNiches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const [activeScript, setActiveScript] = useState(null); // { topic, hook, niche, format, script, loading }

  const analyze = async () => {
    setLoading(true);
    setActiveScript(null);
    try {
      const res = await axios.get("/api/niches/analyze");
      setNiches(res.data);
      setAnalyzed(true);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const generateScript = async (topic, hook, niche, format) => {
    setActiveScript({ topic, hook, niche, format, script: "", loading: true });
    try {
      const res = await axios.post("/api/niches/script", { topic, hook, niche, format });
      setActiveScript({ topic, hook, niche, format, script: res.data.script, loading: false });
    } catch {
      setActiveScript(null);
    }
  };

  const handleUseScript = () => {
    if (!activeScript) return;
    onTopicSelect(activeScript.topic, activeScript.script, activeScript.format);
    setActiveScript(null);
  };

  return (
    <div className="niche-agent">
      <div className="niche-header">
        <h2>🤖 Agent Niches</h2>
        <p>Analyse les meilleures niches virales · génère les hooks et scripts optimisés</p>
        <button className="btn-analyze" onClick={analyze} disabled={loading}>
          {loading ? "⏳ Analyse en cours..." : analyzed ? "🔄 Réanalyser" : "🚀 Analyser les tendances"}
        </button>
      </div>

      {loading && (
        <div className="niche-loading">
          <div className="spinner" />
          <p>L'agent analyse les niches et génère les stratégies...</p>
        </div>
      )}

      {/* Modal script */}
      {activeScript && (
        <div className="script-modal-overlay" onClick={() => setActiveScript(null)}>
          <div className="script-modal" onClick={(e) => e.stopPropagation()}>
            <div className="script-modal-header">
              <div>
                <h3>📝 Script généré</h3>
                <p className="script-modal-topic">{activeScript.topic}</p>
              </div>
              <button className="modal-close" onClick={() => setActiveScript(null)}>✕</button>
            </div>
            {activeScript.loading ? (
              <div className="script-modal-loading"><div className="spinner" /><p>Génération du script...</p></div>
            ) : (
              <>
                <div className="hook-preview">
                  <span className="hook-label">⚡ Hook</span>
                  <p>{activeScript.hook}</p>
                </div>
                <textarea
                  className="script-editor"
                  value={activeScript.script}
                  onChange={(e) => setActiveScript({ ...activeScript, script: e.target.value })}
                  rows={10}
                />
                <div className="script-modal-actions">
                  <button className="btn-secondary" onClick={() => generateScript(activeScript.topic, activeScript.hook, activeScript.niche, activeScript.format)}>
                    🔄 Regénérer
                  </button>
                  <button className="btn-generate" onClick={handleUseScript}>
                    🎬 Utiliser ce script →
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {!loading && niches.length > 0 && (
        <div className="niche-grid">
          {niches.map((niche, i) => (
            <div key={i} className="niche-card">
              <div className="niche-card-header">
                <span className="niche-emoji">{niche.emoji}</span>
                <div style={{ flex: 1 }}>
                  <h3>{niche.niche}</h3>
                  <div className="niche-meta">
                    <span className="niche-score">{"🔥".repeat(Math.min(Math.round(niche.score / 2), 5))} {niche.score}/10</span>
                    <span className="platform-badge" style={{ background: PLATFORM_COLOR[niche.best_platform] || "#6366f1" }}>
                      {niche.best_platform}
                    </span>
                    <span className="freq-badge">{niche.posting_frequency}</span>
                  </div>
                </div>
              </div>
              <p className="niche-why">{niche.why}</p>
              {niche.monetisation_resume && <p className="niche-monetisation">💰 {niche.monetisation_resume}</p>}
              {niche.content_angle && <p className="niche-angle">🎯 {niche.content_angle}</p>}

              <div className="niche-topics">
                {niche.topics?.map((t, j) => (
                  <div key={j} className="topic-item">
                    <div className="topic-item-header">
                      <div className="topic-item-info">
                        <span className="topic-format">{t.format}</span>
                        <span className="topic-title">{t.title}</span>
                      </div>
                      <button
                        className="btn-gen-script"
                        onClick={() => generateScript(t.title, t.hook, niche.niche, t.format)}
                      >
                        ✍️ Script
                      </button>
                    </div>
                    <p className="topic-hook">"{t.hook}"</p>
                    {t.hashtags && (
                      <div className="topic-hashtags">
                        {t.hashtags.map((h, k) => <span key={k} className="hashtag">#{h}</span>)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
