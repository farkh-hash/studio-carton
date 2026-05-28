import VideoCard from "./VideoCard";

export default function VideoGallery({ videos, onUpdate, onDelete }) {
  if (videos.length === 0) {
    return (
      <div className="empty-state">
        <p>Aucune vidéo générée pour l'instant.</p>
        <p>Utilise le formulaire ci-dessus pour créer ta première vidéo carton 3D !</p>
      </div>
    );
  }

  return (
    <div className="video-gallery">
      {videos.map((v) => (
        <VideoCard key={v.id} video={v} onUpdate={onUpdate} onDelete={onDelete} />
      ))}
    </div>
  );
}
