import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "/api/v1";

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401s — refresh token or redirect to login
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, null, {
            headers: { Authorization: `Bearer ${refreshToken}` },
          });
          localStorage.setItem("access_token", data.access_token);
          original.headers.Authorization = `Bearer ${data.access_token}`;
          return api(original);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// ── API Methods ──

export const auth = {
  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  me: () => api.get("/auth/me"),
};

export const inventory = {
  list: (params) => api.get("/inventory", { params }),
  get: (id) => api.get(`/inventory/${id}`),
  create: (data) => api.post("/inventory", data),
  update: (id, data) => api.patch(`/inventory/${id}`, data),
  delete: (id) => api.delete(`/inventory/${id}`),
  categories: () => api.get("/inventory/categories"),
  availability: (id, params) => api.get(`/inventory/${id}/availability`, { params }),
};

export const projects = {
  list: (params) => api.get("/projects", { params }),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post("/projects", data),
  update: (id, data) => api.patch(`/projects/${id}`, data),
  changeStage: (id, stage) => api.post(`/projects/${id}/stage`, { stage }),
  addItem: (id, data) => api.post(`/projects/${id}/items`, data),
  removeItem: (projectId, itemId) => api.delete(`/projects/${projectId}/items/${itemId}`),
  reorderItems: (id, itemIds) => api.post(`/projects/${id}/items/reorder`, { item_ids: itemIds }),
  getPaymentSchedule: (id) => api.get(`/projects/${id}/payment-schedule`),
};

export const clients = {
  list: (params) => api.get("/clients", { params }),
  get: (id) => api.get(`/clients/${id}`),
  create: (data) => api.post("/clients", data),
  update: (id, data) => api.patch(`/clients/${id}`, data),
};

export const payments = {
  list: (params) => api.get("/payments", { params }),
  createIntent: (data) => api.post("/payments/create-intent", data),
};

export const dispatch = {
  vehicles: () => api.get("/vehicles"),
  createVehicle: (data) => api.post("/vehicles", data),
  routes: (params) => api.get("/routes", { params }),
  createRoute: (data) => api.post("/routes", data),
  autoRoute: (routeId) => api.post(`/routes/${routeId}/auto-route`),
  completeStop: (routeId, stopId) => api.post(`/routes/${routeId}/stops/${stopId}/complete`),
};

export const messages = {
  list: (params) => api.get("/messages", { params }),
  send: (data) => api.post("/messages", data),
};

export const website = {
  wishlists: (params) => api.get("/wishlists", { params }),
};

export const dashboard = {
  stats: () => api.get("/dashboard"),
  revenue: (params) => api.get("/reports/revenue", { params }),
  pipeline: () => api.get("/reports/pipeline"),
};

export const activity = {
  list: (params) => api.get("/activity", { params }),
};

export default api;
