import { useState, useEffect } from "react";
import { listVideos, listPipelineJobs } from "./api/client";
import GeneratorForm from "./components/GeneratorForm";
import VideoGallery from "./components/VideoGallery";
import PipelineForm from "./components/PipelineForm";
import PipelineGallery from "./components/PipelineGallery";
import NicheAgent from "./components/NicheAgent";
import TrendsAgent from "./components/TrendsAgent";
import LandingPage from "./components/LandingPage";
import axios from "axios";
import "./App.css";

export default function App() {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("sc_user")); } catch { return null; }
  });
  const [tab, setTab] = useState("trends");
  const [videos, setVideos] = useState([]);
  const [videosLoading, setVideosLoading] = useState(true);
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [pipelineTopic, setPipelineTopic] = useState("");
  const [pipelineScript, setPipelineScript] = useState("");
  const [pipelineFormat, setPipelineFormat] = useState("");

  useEffect(() => {
    if (!user) return;
    listVideos().then((r) => setVideos(r.data)).catch(console.error).finally(() => setVideosLoading(false));
    listPipelineJobs().then((r) => setJobs(r.data)).catch(console.error).finally(() => setJobsLoading(false));
  }, [user]);

  // Vérifier les params URL (retour Stripe)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("success") && params.get("email")) {
      const email = params.get("email");
      axios.get(`/api/users/${email}`).then((r) => {
        setUser(r.data);
        localStorage.setItem("sc_user", JSON.stringify(r.data));
        window.history.replaceState({}, "", "/");
      });
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem("sc_user");
    setUser(null);
  };

  const handleTopicSelect = (topic, script = "", format = "") => {
    setPipelineTopic(topic);
    setPipelineScript(script);
    setPipelineFormat(format);
    setTab("pipeline");
  };

  const handleUpgrade = async () => {
    if (!user) return;
    try {
      const res = await axios.post("/api/users/checkout", { email: user.email });
      window.location.href = res.data.checkout_url;
    } catch {
      alert("Stripe non configuré. Contacte le support.");
    }
  };

  if (!user) return <LandingPage onLogin={handleLogin} />;

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">🎬</span>
          <span>Studio Carton</span>
        </div>
        <div className="header-right">
          {user.is_pro ? (
            <span className="badge-pro">⭐ Pro</span>
          ) : (
            <div className="credits-bar">
              <span className="credits-count">{user.credits} vidéo{user.credits !== 1 ? "s" : ""} restante{user.credits !== 1 ? "s" : ""}</span>
              <button className="btn-upgrade" onClick={handleUpgrade}>Passer Pro →</button>
            </div>
          )}
          <button className="btn-logout" onClick={handleLogout}>{user.email.split("@")[0]}</button>
        </div>
      </header>

      <nav className="tabs">
        <button className={`tab ${tab === "trends" ? "active" : ""}`} onClick={() => setTab("trends")}>
          📡 Tendances
        </button>
        <button className={`tab ${tab === "niches" ? "active" : ""}`} onClick={() => setTab("niches")}>
          🤖 Agent Niches
        </button>
        <button className={`tab ${tab === "pipeline" ? "active" : ""}`} onClick={() => setTab("pipeline")}>
          Pipeline Viral
        </button>
        <button className={`tab ${tab === "kling" ? "active" : ""}`} onClick={() => setTab("kling")}>
          Kling AI
        </button>
      </nav>

      <main className="app-main">
        {tab === "trends" && <TrendsAgent onTopicSelect={handleTopicSelect} />}
        {tab === "niches" && <NicheAgent onTopicSelect={handleTopicSelect} />}

        {tab === "pipeline" && (
          <>
            <PipelineForm
              onJobCreated={(job) => setJobs((prev) => [job, ...prev])}
              initialTopic={pipelineTopic}
              initialScript={pipelineScript}
              initialFormat={pipelineFormat}
              onTopicUsed={() => { setPipelineTopic(""); setPipelineScript(""); setPipelineFormat(""); }}
              userEmail={user.email}
              isPro={user.is_pro}
              credits={user.credits}
              onUpgrade={handleUpgrade}
              onCreditsUpdate={(credits) => {
                const updated = { ...user, credits };
                setUser(updated);
                localStorage.setItem("sc_user", JSON.stringify(updated));
              }}
            />
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
