import { useState } from "react";
import axios from "axios";

const SCENARIO_TYPES = [
  { value: "revelation", label: "🔥 Révélation", desc: "Un secret révélé qui change tout" },
  { value: "transformation", label: "✨ Transformation", desc: "Avant/après — comment tout a changé" },
  { value: "debat", label: "⚔️ Débat", desc: "Deux points de vue opposés" },
  { value: "mentor", label: "🎓 Mentor", desc: "Expert qui enseigne à un débutant" },
  { value: "drama", label: "🎭 Drama", desc: "Situation tendue avec révélation" },
];

export default function ScenarioForm({ onJobCreated }) {
  const [topic, setTopic] = useState("");
  const [duration, setDuration] = useState(60);
  const [type, setType] = useState("revelation");
  const [preview, setPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [step, setStep] = useState("form");

  const handlePreview = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setPreviewLoading(true);
    setError("");
    try {
      const res = await axios.post("/api/scenario/preview", {
        topic, duration, scenario_type: type
      });
      setPreview(res.data);
      setStep("preview");
    } catch {
      setError("Erreur lors de la génération du scénario.");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.post("/api/scenario/generate", {
        topic, duration, scenario_type: type
      });
      onJobCreated(res.data);
      setStep("form");
      setPreview(null);
      setTopic("");
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de la génération.");
    } finally {
      setLoading(false);
    }
  };

  if (step === "preview" && preview) {
    const scenario = preview.scenario;
    return (
      <div className="generator-form">
        <div className="preview-header">
          <h2 className="form-title">🎬 Scénario généré</h2>
          <p className="form-subtitle">{scenario.title}</p>
        </div>

        <div className="scenario-preview">
          {(scenario.scenes || []).map((scene, i) => (
            <div key={i} className="scene-block">
              <div className="scene-label">📍 Scène {i + 1} — {scene.setting}</div>
              {(scene.dialogues || []).map((d, j) => (
                <div key={j} className={`dialogue-line char-${d.character?.toLowerCase()}`}>
                  <span className="char-name">{d.character}</span>
                  <span className="char-emotion">({d.emotion})</span>
                  <p className="char-line">"{d.line}"</p>
                </div>
              ))}
            </div>
          ))}
          {scenario.cta && (
            <div className="cta-block">
              <span className="cta-label">📢 CTA</span>
              <p>{scenario.cta}</p>
            </div>
          )}
        </div>

        {error && <p className="error-msg">{error}</p>}

        <div className="preview-actions">
          <button className="btn-secondary" onClick={() => setStep("form")}>← Modifier</button>
          <button className="btn-secondary" onClick={handlePreview} disabled={previewLoading}>
            {previewLoading ? "⏳" : "🔄 Regénérer"}
          </button>
          <button className="btn-generate" onClick={handleGenerate} disabled={loading}>
            {loading ? "⏳ Génération..." : "🎬 Générer la vidéo →"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <form className="generator-form" onSubmit={handlePreview}>
      <h2 className="form-title">🎭 Pipeline Scénario</h2>
      <p className="form-subtitle">Plusieurs personnages · Dialogue naturel · Format drama viral</p>

      <div className="form-group">
        <label>Sujet du scénario</label>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Ex : Les secrets pour investir sans risque"
          disabled={previewLoading}
        />
      </div>

      <div className="scenario-types">
        {SCENARIO_TYPES.map((t) => (
          <button
            key={t.value}
            type="button"
            className={`scenario-type-btn ${type === t.value ? "active" : ""}`}
            onClick={() => setType(t.value)}
            disabled={previewLoading}
          >
            <span>{t.label}</span>
            <small>{t.desc}</small>
          </button>
        ))}
      </div>

      <div className="form-group" style={{ marginTop: 16 }}>
        <label>Durée</label>
        <select value={duration} onChange={(e) => setDuration(Number(e.target.value))} disabled={previewLoading}>
          <option value={30}>30s</option>
          <option value={60}>60s</option>
          <option value={90}>90s</option>
          <option value={120}>2min</option>
        </select>
      </div>

      {error && <p className="error-msg">{error}</p>}

      <button type="submit" className="btn-generate" disabled={previewLoading || !topic.trim()}>
        {previewLoading ? "⏳ Génération du scénario..." : "📝 Créer le scénario →"}
      </button>
    </form>
  );
}
