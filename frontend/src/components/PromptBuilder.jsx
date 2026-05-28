import { useState, useEffect } from "react";
import { enhancePrompt, getOptions } from "../api/client";

export default function PromptBuilder({ onPromptReady }) {
  const [topic, setTopic] = useState("");
  const [mood, setMood] = useState("fun");
  const [styleVariant, setStyleVariant] = useState("classic");
  const [options, setOptions] = useState({ moods: [], style_variants: [] });
  const [loading, setLoading] = useState(false);
  const [built, setBuilt] = useState(null);

  useEffect(() => {
    getOptions().then((r) => setOptions(r.data)).catch(console.error);
  }, []);

  const handleBuild = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    try {
      const { data } = await enhancePrompt({ topic, mood, style_variant: styleVariant });
      setBuilt(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="prompt-builder">
      <h3>Générateur de prompt carton 3D</h3>
      <div className="field-row">
        <label>Sujet / idée</label>
        <input
          type="text"
          placeholder="ex: un chat qui cuisine des ramen"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleBuild()}
        />
      </div>
      <div className="field-row row2">
        <div>
          <label>Ambiance</label>
          <select value={mood} onChange={(e) => setMood(e.target.value)}>
            {options.moods.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
        <div>
          <label>Style</label>
          <select value={styleVariant} onChange={(e) => setStyleVariant(e.target.value)}>
            {options.style_variants.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>
      <button className="btn-secondary" onClick={handleBuild} disabled={loading || !topic.trim()}>
        {loading ? "Génération..." : "Construire le prompt"}
      </button>
      {built && (
        <div className="built-prompt">
          <p className="prompt-text">{built.prompt}</p>
          <button className="btn-use" onClick={() => onPromptReady(built)}>
            Utiliser ce prompt →
          </button>
        </div>
      )}
    </div>
  );
}
