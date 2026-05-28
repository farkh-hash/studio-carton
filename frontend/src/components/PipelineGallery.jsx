import { useEffect, useRef } from "react";
import { getPipelineStatus, deletePipelineJob } from "../api/client";

const STATUS_LABELS = {
  pending: "En attente...",
  generating_script: "Génération du script...",
  generating_audio: "Synthèse vocale...",
  assembling_video: "Assemblage vidéo...",
  completed: "Terminé",
  failed: "Échec",
};

const STATUS_COLORS = {
  pending: "#888",
  generating_script: "#f59e0b",
  generating_audio: "#3b82f6",
  assembling_video: "#8b5cf6",
  completed: "#22c55e",
  failed: "#ef4444",
};

function JobCard({ job, onUpdate, onDelete }) {
  const intervalRef = useRef(null);

  useEffect(() => {
    if (["completed", "failed"].includes(job.status)) return;
    intervalRef.current = setInterval(async () => {
      try {
        const res = await getPipelineStatus(job.id);
        onUpdate(res.data);
        if (["completed", "failed"].includes(res.data.status)) {
          clearInterval(intervalRef.current);
        }
      } catch {}
    }, 3000);
    return () => clearInterval(intervalRef.current);
  }, [job.id, job.status]);

  const handleDelete = async () => {
    await deletePipelineJob(job.id);
    onDelete(job.id);
  };

  const videoSrc = job.video_url
    ? (import.meta.env.PROD ? job.video_url : `http://localhost:8000${job.video_url}`)
    : null;

  return (
    <div className="video-card">
      <div className="card-header">
        <span className="card-status" style={{ color: STATUS_COLORS[job.status] }}>
          ● {STATUS_LABELS[job.status] || job.status}
        </span>
        <button className="btn-delete" onClick={handleDelete}>✕</button>
      </div>

      <p className="card-topic">{job.topic}</p>
      <p className="card-meta">{job.style} · {job.duration}s</p>

      {job.status === "completed" && videoSrc && (
        <video
          src={videoSrc}
          controls
          className="card-video"
          style={{ width: "100%", borderRadius: 8, marginTop: 8 }}
        />
      )}

      {job.status === "completed" && videoSrc && (
        <a href={videoSrc} download className="btn-download">
          Télécharger
        </a>
      )}

      {job.status === "failed" && (
        <p className="error-msg">{job.error_msg}</p>
      )}

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
  if (!jobs.length) {
    return <p className="empty-msg">Aucune vidéo générée. Lance ton premier pipeline !</p>;
  }

  return (
    <div className="video-grid">
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} onUpdate={onUpdate} onDelete={onDelete} />
      ))}
    </div>
  );
}
