import { useState } from "react";
import axios from "axios";

const SUBSCRIBER_TARGETS = [
  { value: 10000, label: "10K abonnés" },
  { value: 50000, label: "50K abonnés" },
  { value: 100000, label: "100K abonnés" },
  { value: 500000, label: "500K abonnés" },
];

export default function MonetisationAgent({ onTopicSelect }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [target, setTarget] = useState(50000);
  const [analyzed, setAnalyzed] = useState(false);

  const analyze = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`/api/monetisation/analyze?target_subscribers=${target}`);
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
        <h2>💰 Agent Monétisation</h2>
        <p>Analyse les niches par <strong>revenu réel estimé</strong> — RPM, affiliation, brand deals, stratégie</p>

        <div className="target-selector">
          <span>Cible d'abonnés :</span>
          {SUBSCRIBER_TARGETS.map(t => (
            <button
              key={t.value}
              className={`target-btn ${target === t.value ? "active" : ""}`}
              onClick={() => setTarget(t.value)}
              disabled={loading}
            >
              {t.label}
            </button>
          ))}
        </div>

        <button className="btn-analyze" onClick={analyze} disabled={loading}>
          {loading ? "⏳ Calcul en cours..." : analyzed ? "🔄 Réanalyser" : "💰 Analyser le potentiel"}
        </button>
      </div>

      {loading && (
        <div className="niche-loading">
          <div className="spinner" />
          <p>Calcul des revenus potentiels par niche...</p>
        </div>
      )}

      {!loading && data && (
        <>
          {/* Recommandation principale */}
          {data.recommended_niche && (
            <div className="money-recommendation">
              <h3>⭐ Niche recommandée</h3>
              <p>{data.recommended_niche}</p>
            </div>
          )}

          {/* Plan 30 jours */}
          {data.first_30_days_plan?.length > 0 && (
            <div className="money-plan">
              <h3>📅 Plan 30 jours pour gagner tes premiers euros</h3>
              <div className="plan-steps">
                {data.first_30_days_plan.map((step, i) => (
                  <div key={i} className="plan-step">
                    <span className="step-num">{i + 1}</span>
                    <p>{step}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Milestone revenu */}
          {data.revenue_milestone && (
            <div className="revenue-milestone">
              💵 {data.revenue_milestone}
            </div>
          )}

          {/* Top niches */}
          <div className="niche-grid" style={{ marginTop: 24 }}>
            {(data.top_niches || []).map((niche, i) => (
              <div key={i} className="niche-card money-card">
                <div className="niche-card-header">
                  <span className="trend-rank">#{niche.rank}</span>
                  <div style={{ flex: 1 }}>
                    <h3>{niche.niche?.replace(/_/g, " ")}</h3>
                    <div className="money-badge">{niche.revenu_mensuel_estime}</div>
                  </div>
                  <span className="money-score">💰 {niche.score_monetisation}/10</span>
                </div>

                {niche.why_monetisable && <p className="niche-why">📊 {niche.why_monetisable}</p>}
                {niche.best_affiliate && <p className="niche-monetisation">🔗 {niche.best_affiliate}</p>}
                {niche.quick_win && <p className="quick-win">⚡ Quick win : {niche.quick_win}</p>}
                {niche.competition_gap && <p className="niche-angle">🎯 {niche.competition_gap}</p>}

                {niche.content_strategy && (
                  <div className="content-strategy">
                    <span className="section-label" style={{ fontSize: 11 }}>Stratégie contenu</span>
                    <p style={{ fontSize: 13, color: "#94a3b8", margin: "4px 0" }}>{niche.content_strategy}</p>
                  </div>
                )}

                {niche.example_topics?.length > 0 && (
                  <div className="niche-topics">
                    {niche.example_topics.map((topic, j) => (
                      <button
                        key={j}
                        className="topic-btn"
                        onClick={() => onTopicSelect(topic)}
                      >
                        <span>▶</span> {topic}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
