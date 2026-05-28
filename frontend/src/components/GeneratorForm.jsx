import { useState, useEffect } from "react";
import { generateVideo, getOptions } from "../api/client";
import PromptBuilder from "./PromptBuilder";

const DEFAULT_NEGATIVE =
  "realistic, photographic, blurry, dark, muted colors, flat 2D, ugly, deformed, watermark, nsfw";

export default function GeneratorForm({ onVideoCreated }) {
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState(DEFAULT_NEGATIVE);
  const [model, setModel] = useState("kling-v1-6");
  const [duration, setDuration] = useState(5);
  const [aspectRatio, setAspectRatio] = useState("9:16");
  const [enhance, setEnhance] = useState(false);
  const [options, setOptions] = useState({ models: [], durations: [], aspect_ratios: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showBuilder, setShowBuilder] = useState(false);

  useEffect(() => {
    getOptions().then((r) => setOptions(r.data)).catch(console.error);
  }, []);

  const handlePromptReady = ({ prompt: p, negative_prompt: n }) => {
    setPrompt(p);
    setNegativePrompt(n);
    setEnhance(false);
    setShowBuilder(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await generateVideo({
        prompt,
        negative_prompt: negativePrompt,
        model,
        duration,
        aspect_ratio: aspectRatio,
        enhance_prompt: enhance,
      });
      onVideoCreated(data);
      setPrompt("");
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de la génération");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="generator-form">
      <div className="form-header">
        <h2>Nouvelle vidéo</h2>
        <button className="btn-ghost" onClick={() => setShowBuilder(!showBuilder)}>
          {showBuilder ? "✕ Fermer le builder" : "✨ Builder de prompt"}
        </button>
      </div>

      {showBuilder && <PromptBuilder onPromptReady={handlePromptReady} />}

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Prompt</label>
          <textarea
            rows={3}
            placeholder="Décris ta vidéo carton 3D..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={enhance}
              onChange={(e) => setEnhance(e.target.checked)}
            />
            Enrichir automatiquement avec le style carton 3D
          </label>
        </div>

        <div className="field">
          <label>Prompt négatif</label>
          <textarea
            rows={2}
            value={negativePrompt}
            onChange={(e) => setNegativePrompt(e.target.value)}
          />
        </div>

        <div className="settings-row">
          <div className="field">
            <label>Modèle</label>
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              {options.models.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Durée</label>
            <select value={duration} onChange={(e) => setDuration(Number(e.target.value))}>
              {options.durations.map((d) => (
                <option key={d} value={d}>{d}s</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Format</label>
            <select value={aspectRatio} onChange={(e) => setAspectRatio(e.target.value)}>
              {options.aspect_ratios.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
        </div>

        {error && <p className="error">{error}</p>}

        <button className="btn-primary" type="submit" disabled={loading || !prompt.trim()}>
          {loading ? "Envoi en cours..." : "Générer la vidéo"}
        </button>
      </form>
    </div>
  );
}
