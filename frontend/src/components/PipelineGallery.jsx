import { useEffect, useRef, useState } from "react";
import { getPipelineStatus, deletePipelineJob } from "../api/client";
import axios from "axios";

const STATUS_LABELS = {
  pending: "En attente...",
  generating_script: "Génération du script...",
  generating_audio: "Synthèse vocale...",
  assembling_video: "Assemblage vidéo...",
  completed: "✅ Terminé",
  failed: "❌ Échec",
};

const STATUS_COLORS = {
  pending: "#888",
  generating_script: "#f59e0b",
  generating_audio: "#3b82f6",
  assembling_video: "#8b5cf6",
  completed: "#22c55e",
  failed: "#ef4444",
};

const PLATFORM_ICONS = { tiktok: "🎵", youtube: "▶️", instagram: "📸" };
const PLATFORM_NAMES = { tiktok: "TikTok", youtube: "YouTube", instagram: "Instagram" };

function CaptionModal({ jobId, topic, onClose }) {
  const [captions, setCaptions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activePlatform, setActivePlatform] = useState("tiktok");
  const [copied, setCopied] = useState("");

  useEffect(() => {
    axios.get(`/api/pipeline/${jobId}/captions`)
      .then(r => { setCaptions(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [jobId]);

  const copy = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(""), 2000);
  };

  const platform = captions?.[activePlatform];

  return (
    <div className="script-modal-overlay" onClick={onClose}>
      <div className="script-modal" onClick={e => e.stopPropagation()}>
        <div className="script-modal-header">
          <div><h3>📋 Prêt à poster</h3><p className="script-modal-topic">{topic}</p></div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div className="script-modal-loading"><div className="spinner" /><p>Génération des captions...</p></div>
        ) : !captions ? (
          <p style={{ color: "#f87171" }}>Erreur lors de la génération.</p>
        ) : (
          <>
            <div className="platform-tabs">
              {["tiktok", "youtube", "instagram"].map(p => (
                <button key={p} className={`platform-tab ${activePlatform === p ? "active" : ""}`} onClick={() => setActivePlatform(p)}>
                  {PLATFORM_ICONS[p]} {PLATFORM_NAMES[p]}
                </button>
              ))}
            </div>

            {platform && (
              <div className="caption-content">
                <div className="caption-block">
                  <div className="caption-block-header">
                    <span>{activePlatform === "youtube" ? "Titre" : "Caption"}</span>
                    <button className="btn-copy" onClick={() => copy(activePlatform === "youtube" ? platform.title : platform.caption, "caption")}>
                      {copied === "caption" ? "✅ Copié !" : "📋 Copier"}
                    </button>
                  </div>
                  <p className="caption-text">{activePlatform === "youtube" ? platform.title : platform.caption}</p>
                </div>

                {activePlatform === "youtube" && platform.description && (
                  <div className="caption-block">
                    <div className="caption-block-header">
                      <span>Description</span>
                      <button className="btn-copy" onClick={() => copy(platform.description, "desc")}>
                        {copied === "desc" ? "✅ Copié !" : "📋 Copier"}
                      </button>
                    </div>
                    <p className="caption-text">{platform.description}</p>
                  </div>
                )}

                <div className="caption-block">
                  <div className="caption-block-header">
                    <span>Hashtags</span>
                    <button className="btn-copy" onClick={() => copy((platform.hashtags || platform.tags || []).map(h => `#${h}`).join(" "), "tags")}>
                      {copied === "tags" ? "✅ Copié !" : "📋 Copier"}
                    </button>
                  </div>
                  <div className="hashtag-list">
                    {(platform.hashtags || platform.tags || []).map((h, i) => (
                      <span key={i} className="hashtag">#{h}</span>
                    ))}
                  </div>
                </div>

                {platform.best_time && (
                  <div className="best-time">⏰ Meilleur moment : <strong>{platform.best_time}</strong></div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function JobCard({ job, onUpdate, onDelete }) {
  const intervalRef = useRef(null);
  const retriesRef = useRef(0);
  const [showCaptions, setShowCaptions] = useState(false);

  useEffect(() => {
    if (["completed", "failed"].includes(job.status)) return;
    if (!job.id) return;
    retriesRef.current = 0;
    intervalRef.current = setInterval(async () => {
      retriesRef.current++;
      // Abandon après 6 minutes (72 × 5s) — évite le polling infini
      if (retriesRef.current > 72) {
        clearInterval(intervalRef.current);
        onUpdate({ ...job, status: "failed", error_msg: "Timeout : job abandonné après 6 minutes." });
        return;
      }
      try {
        const res = await getPipelineStatus(job.id);
        onUpdate(res.data);
        if (["completed", "failed"].includes(res.data.status)) clearInterval(intervalRef.current);
      } catch {}
    }, 5000);
    return () => clearInterval(intervalRef.current);
  }, [job.id, job.status]);

  const videoSrc = job.video_url
    ? (import.meta.env.PROD ? job.video_url : `http://localhost:8000${job.video_url}`)
    : null;

  return (
    <div className="video-card">
      {showCaptions && <CaptionModal jobId={job.id} topic={job.topic} onClose={() => setShowCaptions(false)} />}

      <div className="card-header">
        <span className="card-status" style={{ color: STATUS_COLORS[job.status] }}>
          ● {STATUS_LABELS[job.status] || job.status}
        </span>
        <button className="btn-delete" onClick={async () => { await deletePipelineJob(job.id); onDelete(job.id); }}>✕</button>
      </div>

      <p className="card-topic">{job.topic}</p>
      <p className="card-meta">{job.style} · {job.duration}s</p>

      {job.status === "completed" && videoSrc && (
        <video src={videoSrc} controls className="card-video" style={{ width: "100%", borderRadius: 8, marginTop: 8 }} />
      )}

      {job.status === "completed" && videoSrc && (
        <div className="card-actions">
          <a href={videoSrc} download className="btn-download">⬇️ Télécharger</a>
          <button className="btn-captions" onClick={() => setShowCaptions(true)}>📋 Prêt à poster</button>
        </div>
      )}

      {job.status === "failed" && <p className="error-msg">{job.error_msg}</p>}

      {job.script && job.status === "completed" && (
        <details className="script-details">
          <summary>Voir le script</summary>
          <pre className="script-text">{job.script}</pre>
        </details>
      )}
    </div>
  );
}

export default function PipelineGallery({ jobs, onUpdate, onDelete }) {
  if (!jobs.length) return <p className="empty-msg">Aucune vidéo générée. Lance ton premier pipeline !</p>;
  return (
    <div className="video-grid">
      {jobs.map(job => <JobCard key={job.id} job={job} onUpdate={onUpdate} onDelete={onDelete} />)}
    </div>
  );
}
