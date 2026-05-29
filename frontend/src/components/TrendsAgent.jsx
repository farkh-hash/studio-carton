import { useState } from "react";
import axios from "axios";

const PLATFORM_COLOR = { TikTok: "#ff2d55", YouTube: "#ff0000", Instagram: "#e1306c" };

export default function TrendsAgent({ onTopicSelect }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);

  const analyze = async () => {
    setLoading(true);
    try {
      const res = await axios.get("/api/trends/analyze");
      setData(res.data);
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
        <h2>📡 Agent Tendances</h2>
        <p>Analyse les tendances <strong>en temps réel</strong> — YouTube Trending FR, Google Trends, Reddit, TikTok</p>
        {data && (
          <div className="trends-sources">
            {Object.entries(data.sources || {}).map(([k, v]) => (
              <span key={k} className="source-badge">{k}: {v}</span>
            ))}
            <span className="source-badge date">📅 {data.date}</span>
          </div>
        )}
        <button className="btn-analyze" onClick={analyze} disabled={loading}>
          {loading ? "⏳ Analyse en cours (~30s)..." : analyzed ? "🔄 Réanalyser" : "📡 Analyser les tendances maintenant"}
        </button>
      </div>

      {loading && (
        <div className="niche-loading">
          <div className="spinner" />
          <p>Analyse YouTube Trending FR + Google Trends + Reddit + TikTok...</p>
          <p style={{ fontSize: 12, color: "#6b7280" }}>~30 secondes</p>
        </div>
      )}

      {!loading && data && (
        <>
          {/* Keywords trending */}
          {data.trending_keywords?.length > 0 && (
            <div className="trending-keywords">
              <span className="section-label">🔥 Mots-clés trending maintenant</span>
              <div className="keywords-list">
                {data.trending_keywords.map((k, i) => (
                  <span key={i} className="keyword-badge">{k}</span>
                ))}
              </div>
            </div>
          )}

          {/* Formats chauds */}
          {data.hot_formats?.length > 0 && (
            <div className="trending-formats">
              <span className="section-label">🎬 Formats qui cartonnent</span>
              <div className="keywords-list">
                {data.hot_formats.map((f, i) => (
                  <span key={i} className="format-badge">{f}</span>
                ))}
              </div>
            </div>
          )}

          {/* À éviter */}
          {data.avoid_now?.length > 0 && (
            <div className="trending-avoid">
              <span className="section-label">⛔ À éviter (saturé)</span>
              <div className="keywords-list">
                {data.avoid_now.map((a, i) => (
                  <span key={i} className="avoid-badge">{a}</span>
                ))}
              </div>
            </div>
          )}

          {/* Top niches */}
          <div className="niche-grid" style={{ marginTop: 24 }}>
            {(data.top_niches || []).map((niche, i) => (
              <div key={i} className="niche-card">
                <div className="niche-card-header">
                  <span className="trend-rank">#{i + 1}</span>
                  <div style={{ flex: 1 }}>
                    <h3>{niche.niche}</h3>
                    <div className="niche-meta">
                      <span className="niche-score">{"🔥".repeat(Math.min(Math.round(niche.score / 2), 5))} {niche.score}/10</span>
                      {niche.best_platform && (
                        <span className="platform-badge" style={{ background: PLATFORM_COLOR[niche.best_platform] || "#6366f1" }}>
                          {niche.best_platform}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {niche.proof && <p className="niche-proof">📊 {niche.proof}</p>}
                {niche.why_now && <p className="niche-why">⚡ {niche.why_now}</p>}
                {niche.monetisation && <p className="niche-monetisation">💰 {niche.monetisation}</p>}

                {niche.hook_inspiration && (
                  <div className="hook-preview" style={{ margin: "10px 0" }}>
                    <span className="hook-label">⚡ Hook inspiré des tendances</span>
                    <p style={{ margin: 0, fontSize: 13, color: "#e2e8f0", fontStyle: "italic" }}>"{niche.hook_inspiration}"</p>
                  </div>
                )}

                <div className="niche-topics">
                  {(niche.content_ideas || []).map((idea, j) => (
                    <button
                      key={j}
                      className="topic-btn"
                      onClick={() => onTopicSelect(idea)}
                    >
                      <span>▶</span> {idea}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
