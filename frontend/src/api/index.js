import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 5000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default api;

// API Endpoints
export const recognizeFace = (formData) => api.post('/recognize', formData);
export const getUsers = () => api.get('/users');
export const addUser = (formData) => api.post('/users', formData);
export const deleteUser = (id) => api.delete(`/users/${id}`);
export const getLogs = (params) => api.get('/logs', { params });
export const getConfig = () => api.get('/config');
export const updateConfig = (config) => api.put('/config', config);
