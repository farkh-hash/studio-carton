import { useState } from "react";
import { generatePipeline } from "../api/client";

const STYLES = [
  { value: "viral", label: "Viral — accrocheur, rythme rapide" },
  { value: "educatif", label: "Éducatif — clair et informatif" },
  { value: "storytelling", label: "Storytelling — narration émotionnelle" },
  { value: "humour", label: "Humour — ton léger et fun" },
];

export default function PipelineForm({ onJobCreated }) {
  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState("viral");
  const [duration, setDuration] = useState(60);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await generatePipeline({ topic, style, duration });
      onJobCreated(res.data);
      setTopic("");
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de la génération");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="generator-form" onSubmit={handleSubmit}>
      <h2 className="form-title">Pipeline Viral</h2>
      <p className="form-subtitle">Script → Voix IA → Sous-titres → Vidéo 9:16</p>

      <div className="form-group">
        <label>Sujet de la vidéo</label>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Ex : 5 erreurs des entrepreneurs débutants"
          disabled={loading}
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Style</label>
          <select value={style} onChange={(e) => setStyle(e.target.value)} disabled={loading}>
            {STYLES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Durée (secondes)</label>
          <select value={duration} onChange={(e) => setDuration(Number(e.target.value))} disabled={loading}>
            <option value={30}>30s — Short punch</option>
            <option value={60}>60s — Standard TikTok</option>
            <option value={90}>90s — Format long</option>
          </select>
        </div>
      </div>

      {error && <p className="error-msg">{error}</p>}

      <button type="submit" className="btn-generate" disabled={loading || !topic.trim()}>
        {loading ? "Génération en cours..." : "Générer la vidéo"}
      </button>
    </form>
  );
}
