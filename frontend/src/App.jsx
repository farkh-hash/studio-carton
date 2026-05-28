import { useState, useEffect } from "react";
import { listVideos, listPipelineJobs } from "./api/client";
import GeneratorForm from "./components/GeneratorForm";
import VideoGallery from "./components/VideoGallery";
import PipelineForm from "./components/PipelineForm";
import PipelineGallery from "./components/PipelineGallery";
import "./App.css";

export default function App() {
  const [tab, setTab] = useState("pipeline");
  const [videos, setVideos] = useState([]);
  const [videosLoading, setVideosLoading] = useState(true);
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(true);

  useEffect(() => {
    listVideos().then((r) => setVideos(r.data)).catch(console.error).finally(() => setVideosLoading(false));
    listPipelineJobs().then((r) => setJobs(r.data)).catch(console.error).finally(() => setJobsLoading(false));
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">🎬</span>
          <span>Studio Carton</span>
        </div>
        <p className="tagline">Génération automatique de vidéos virales TikTok & Reels</p>
      </header>

      <nav className="tabs">
        <button className={`tab ${tab === "pipeline" ? "active" : ""}`} onClick={() => setTab("pipeline")}>
          Pipeline Viral
        </button>
        <button className={`tab ${tab === "kling" ? "active" : ""}`} onClick={() => setTab("kling")}>
          Kling AI
        </button>
      </nav>

      <main className="app-main">
        {tab === "pipeline" && (
          <>
            <PipelineForm onJobCreated={(job) => setJobs((prev) => [job, ...prev])} />
            <section className="gallery-section">
              <div className="gallery-header">
                <h2>Mes vidéos virales</h2>
                <span className="count">{jobs.length}</span>
              </div>
              {jobsLoading ? <p className="loading">Chargement...</p> : (
                <PipelineGallery
                  jobs={jobs}
                  onUpdate={(u) => setJobs((prev) => prev.map((j) => j.id === u.id ? { ...j, ...u } : j))}
                  onDelete={(id) => setJobs((prev) => prev.filter((j) => j.id !== id))}
                />
              )}
            </section>
          </>
        )}

        {tab === "kling" && (
          <>
            <GeneratorForm onVideoCreated={(v) => setVideos((prev) => [v, ...prev])} />
            <section className="gallery-section">
              <div className="gallery-header">
                <h2>Vidéos Kling AI</h2>
                <span className="count">{videos.length}</span>
              </div>
              {videosLoading ? <p className="loading">Chargement...</p> : (
                <VideoGallery
                  videos={videos}
                  onUpdate={(u) => setVideos((prev) => prev.map((v) => v.id === u.id ? u : v))}
                  onDelete={(id) => setVideos((prev) => prev.filter((v) => v.id !== id))}
                />
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
