import { useState, useEffect } from "react";
import { generatePipeline } from "../api/client";
import axios from "axios";

const STYLES = [
  { value: "viral", label: "🔥 Viral" },
  { value: "educatif", label: "📚 Éducatif" },
  { value: "storytelling", label: "🎭 Storytelling" },
  { value: "humour", label: "😄 Humour" },
];

const HOOKS = [
  { value: "auto", label: "🤖 Auto (IA choisit)" },
  { value: "curiosite", label: "🔍 Curiosité" },
  { value: "choc", label: "⚡ Choc / Surprise" },
  { value: "identification", label: "🪞 Identification" },
  { value: "resultat", label: "🎯 Résultat promis" },
  { value: "contre_intuitif", label: "🔄 Contre-intuitif" },
];

export default function PipelineForm({ onJobCreated, initialTopic = "", initialScript = "", initialFormat = "", onTopicUsed, userEmail, isPro, credits, onUpgrade, onCreditsUpdate }) {
  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState("viral");
  const [hookType, setHookType] = useState("auto");
  const [duration, setDuration] = useState(60);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState("");
  const [script, setScript] = useState("");
  const [step, setStep] = useState("form");

  useEffect(() => {
    if (initialTopic) {
      setTopic(initialTopic);
      if (initialScript) { setScript(initialScript); setStep("preview"); }
      if (initialFormat) {
        const map = { "30s": 30, "60s": 60, "90s": 90, "2min": 120, "3min": 180 };
        setDuration(map[initialFormat] || 60);
      }
      onTopicUsed?.();
    }
  }, [initialTopic]);

  const handlePreview = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setPreviewLoading(true);
    setError("");
    try {
      const res = await axios.post("/api/pipeline/preview-script", { topic, duration, style, hook_type: hookType });
      setScript(res.data.script);
      setStep("preview");
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de la génération du script.");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!isPro && credits <= 0) { onUpgrade?.(); return; }
    setLoading(true);
    setError("");
    try {
      const res = await generatePipeline({ topic, style, duration, script_override: script }, userEmail);
      onJobCreated(res.data);
      onCreditsUpdate?.(credits - 1);
      setStep("form");
      setScript("");
      setTopic("");
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de la génération.");
    } finally {
      setLoading(false);
    }
  };

  if (step === "preview") {
    return (
      <div className="generator-form">
        <div className="preview-header">
          <h2 className="form-title">📝 Script généré</h2>
          <p className="form-subtitle">Vérifie et modifie avant de lancer la vidéo</p>
        </div>
        <div className="script-meta">
          <span>📌 {topic}</span>
          <span>⏱️ {duration}s</span>
          <span>🎨 {style}</span>
        </div>
        <textarea
          className="script-editor"
          value={script}
          onChange={(e) => setScript(e.target.value)}
          rows={12}
        />
        {error && <p className="error-msg">{error}</p>}
        <div className="preview-actions">
          <button className="btn-secondary" onClick={() => setStep("form")}>← Modifier les paramètres</button>
          <button className="btn-secondary" onClick={handlePreview} disabled={previewLoading}>
            {previewLoading ? "⏳" : "🔄 Regénérer"}
          </button>
          <button className="btn-generate" onClick={handleGenerate} disabled={loading}>
            {loading ? "⏳ Génération..." : "🎬 Générer la vidéo →"}
          </button>
        </div>
        {!isPro && <p className="credits-note">💳 {credits} crédit{credits !== 1 ? "s" : ""} restant{credits !== 1 ? "s" : ""}</p>}
      </div>
    );
  }

  return (
    <form className="generator-form" onSubmit={handlePreview}>
      <h2 className="form-title">Pipeline Viral</h2>
      <p className="form-subtitle">Script IA → Voix → Sous-titres → Vidéo 9:16</p>

      <div className="form-group">
        <label>Sujet de la vidéo</label>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Ex : 5 erreurs des entrepreneurs débutants"
          disabled={previewLoading}
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Style</label>
          <select value={style} onChange={(e) => setStyle(e.target.value)} disabled={previewLoading}>
            {STYLES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>Type de hook</label>
          <select value={hookType} onChange={(e) => setHookType(e.target.value)} disabled={previewLoading}>
            {HOOKS.map((h) => <option key={h.value} value={h.value}>{h.label}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>Durée</label>
          <select value={duration} onChange={(e) => setDuration(Number(e.target.value))} disabled={previewLoading}>
            <option value={30}>30s</option>
            <option value={60}>60s</option>
            <option value={90}>90s</option>
            <option value={120}>2min</option>
            <option value={180}>3min</option>
          </select>
        </div>
      </div>

      {error && <p className="error-msg">{error}</p>}

      <button type="submit" className="btn-generate" disabled={previewLoading || !topic.trim()}>
        {previewLoading ? "⏳ Génération du script..." : "📝 Générer le script →"}
      </button>
    </form>
  );
}
