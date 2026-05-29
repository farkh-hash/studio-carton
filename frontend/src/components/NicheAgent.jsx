import { useState } from "react";
import axios from "axios";

export default function NicheAgent({ onTopicSelect }) {
  const [niches, setNiches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);

  const analyze = async () => {
    setLoading(true);
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

  return (
    <div className="niche-agent">
      <div className="niche-header">
        <h2>🤖 Agent Niches</h2>
        <p>Analyse les meilleures niches virales du moment et génère des sujets optimisés pour TikTok, Reels et Shorts.</p>
        <button className="btn-analyze" onClick={analyze} disabled={loading}>
          {loading ? "⏳ Analyse en cours..." : analyzed ? "🔄 Réanalyser" : "🚀 Analyser les tendances"}
        </button>
      </div>

      {loading && (
        <div className="niche-loading">
          <div className="spinner" />
          <p>L'agent analyse les niches virales...</p>
        </div>
      )}

      {!loading && niches.length > 0 && (
        <div className="niche-grid">
          {niches.map((niche, i) => (
            <div key={i} className="niche-card">
              <div className="niche-card-header">
                <span className="niche-emoji">{niche.emoji}</span>
                <div>
                  <h3>{niche.niche}</h3>
                  <div className="niche-score">
                    {"🔥".repeat(Math.min(niche.score, 5))}
                    <span className="score-num">{niche.score}/10</span>
                  </div>
                </div>
              </div>
              <p className="niche-why">{niche.why}</p>
              <div className="niche-topics">
                {niche.topics?.map((topic, j) => (
                  <button
                    key={j}
                    className="topic-btn"
                    onClick={() => onTopicSelect(topic)}
                  >
                    <span>▶</span> {topic}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
