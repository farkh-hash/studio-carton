import { useState, useEffect } from "react";
import { listVideos } from "./api/client";
import GeneratorForm from "./components/GeneratorForm";
import VideoGallery from "./components/VideoGallery";
import "./App.css";

function App() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listVideos()
      .then((r) => setVideos(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleVideoCreated = (video) => setVideos((prev) => [video, ...prev]);
  const handleVideoUpdate = (updated) =>
    setVideos((prev) => prev.map((v) => (v.id === updated.id ? updated : v)));
  const handleVideoDelete = (id) => setVideos((prev) => prev.filter((v) => v.id !== id));

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">📦</span>
          <span>Studio Carton</span>
        </div>
        <p className="tagline">Génération de vidéos virales carton 3D — TikTok & Reels</p>
      </header>

      <main className="app-main">
        <GeneratorForm onVideoCreated={handleVideoCreated} />

        <section className="gallery-section">
          <div className="gallery-header">
            <h2>Mes vidéos</h2>
            <span className="count">{videos.length}</span>
          </div>
          {loading ? (
            <p className="loading">Chargement...</p>
          ) : (
            <VideoGallery
              videos={videos}
              onUpdate={handleVideoUpdate}
              onDelete={handleVideoDelete}
            />
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
