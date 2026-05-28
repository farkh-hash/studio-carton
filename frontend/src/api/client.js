import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 30000,
});

export const generateVideo = (payload) => api.post("/videos/generate", payload);
export const listVideos = (limit = 50) => api.get(`/videos/?limit=${limit}`);
export const getVideo = (id) => api.get(`/videos/${id}`);
export const getVideoStatus = (id) => api.get(`/videos/${id}/status`);
export const deleteVideo = (id) => api.delete(`/videos/${id}`);
export const enhancePrompt = (payload) => api.post("/prompts/enhance", payload);
export const getOptions = () => api.get("/prompts/options");
