import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getSampleData = async () => {
  const response = await api.get('/sample-data');
  return response.data;
};

export const generatePlan = async (useSampleData = true, videoUrls = null) => {
  const response = await api.post('/generate-plan', {
    use_sample_data: useSampleData,
    video_urls: videoUrls,
  });
  return response.data;
};

export const renderVideo = async (plan) => {
  const response = await api.post('/render-video', plan);
  return response.data;
};

export const getRenderStatus = async (jobId) => {
  const response = await api.get(`/render-status/${jobId}`);
  return response.data;
};

export const getSavedPlan = async () => {
  const response = await api.get('/timeline-plan');
  return response.data;
};

export const getDownloadUrl = (filename) => {
  return `${API_BASE_URL}/download/${filename}`;
};

export default api;
