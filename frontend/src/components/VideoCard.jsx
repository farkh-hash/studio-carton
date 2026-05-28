import { useEffect, useRef } from "react";
import { getVideoStatus, deleteVideo } from "../api/client";

const STATUS_COLORS = {
  pending: "#f59e0b",
  processing: "#8b5cf6",
  completed: "#10b981",
  failed: "#ef4444",
};

const STATUS_LABELS = {
  pending: "En attente",
  processing: "Génération en cours...",
  completed: "Terminé",
  failed: "Échec",
};

export default function VideoCard({ video, onUpdate, onDelete }) {
  const pollRef = useRef(null);

  // Polling automatique tant que la vidéo est en cours de génération
  useEffect(() => {
    if (!["pending", "processing"].includes(video.status)) return;

    pollRef.current = setInterval(async () => {
      try {
        const { data } = await getVideoStatus(video.id);
        if (data.status !== video.status || data.video_url) {
          onUpdate({ ...video, ...data });
        }
        if (!["pending", "processing"].includes(data.status)) {
          clearInterval(pollRef.current);
        }
      } catch (e) {
        console.error(e);
      }
    }, 5000);

    return () => clearInterval(pollRef.current);
  }, [video.id, video.status]);

  const handleDelete = async () => {
    if (!confirm("Supprimer cette vidéo ?")) return;
    await deleteVideo(video.id);
    onDelete(video.id);
  };

  const videoUrl = video.video_url
    ? `http://localhost:8000${video.video_url}`
    : null;

  return (
    <div className="video-card">
      <div className="card-thumb">
        {videoUrl ? (
          <video src={videoUrl} controls muted loop playsInline />
        ) : (
          <div className="placeholder-thumb">
            {["pending", "processing"].includes(video.status) && (
              <div className="spinner" />
            )}
            <span>{STATUS_LABELS[video.status] || video.status}</span>
          </div>
        )}
      </div>

      <div className="card-body">
        <span
          className="status-badge"
          style={{ background: STATUS_COLORS[video.status] || "#6b7280" }}
        >
          {STATUS_LABELS[video.status] || video.status}
        </span>
        <p className="card-prompt">{video.prompt}</p>
        <div className="card-meta">
          <span>{video.model}</span>
        </div>
        {video.error_msg && <p className="card-error">{video.error_msg}</p>}
      </div>

      <div className="card-actions">
        {videoUrl && (
          <a className="btn-sm" href={videoUrl} download target="_blank" rel="noreferrer">
            Télécharger
          </a>
        )}
        <button className="btn-sm btn-danger" onClick={handleDelete}>
          Supprimer
        </button>
      </div>
    </div>
  );
}
