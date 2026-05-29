import axios from "axios";

const base = import.meta.env.PROD ? "/api" : "http://localhost:8000/api";

const api = axios.create({ baseURL: base, timeout: 30000 });

// ── Kling AI ──────────────────────────────────────────────────────────────────
export const generateVideo = (payload) => api.post("/videos/generate", payload);
export const listVideos = (limit = 50) => api.get(`/videos/?limit=${limit}`);
export const getVideo = (id) => api.get(`/videos/${id}`);
export const getVideoStatus = (id) => api.get(`/videos/${id}/status`);
export const deleteVideo = (id) => api.delete(`/videos/${id}`);
export const enhancePrompt = (payload) => api.post("/prompts/enhance", payload);
export const getOptions = () => api.get("/prompts/options");

// ── Pipeline Viral ────────────────────────────────────────────────────────────
export const generatePipeline = (payload, email) => api.post(`/pipeline/generate${email ? `?email=${encodeURIComponent(email)}` : ""}`, payload);
export const listPipelineJobs = (limit = 50) => api.get(`/pipeline/?limit=${limit}`);
export const getPipelineJob = (id) => api.get(`/pipeline/${id}`);
export const getPipelineStatus = (id) => api.get(`/pipeline/${id}/status`);
export const deletePipelineJob = (id) => api.delete(`/pipeline/${id}`);
