import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor: Attach JWT token to all requests
 * Also tracks ETags for conditional requests
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add ETag if available for conditional requests
    const etag = localStorage.getItem(`etag_${config.url}`);
    if (etag && config.method === 'get') {
      config.headers['If-None-Match'] = etag;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Response interceptor: Handle 401 (refresh token), 409 (conflicts), and 304 (not modified)
 */
apiClient.interceptors.response.use(
  (response) => {
    // Store ETag for future conditional requests
    if (response.headers.etag) {
      localStorage.setItem(`etag_${response.config.url}`, response.headers.etag);
    }

    // Track last sync time if provided
    if (response.headers['x-last-sync']) {
      localStorage.setItem('last_sync_timestamp', response.headers['x-last-sync']);
    }

    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized - try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed - clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle 409 Conflict - data conflict on sync
    if (error.response?.status === 409) {
      const conflictData = error.response.data;
      error.isConflict = true;
      error.conflictData = conflictData;
    }

    // Handle 304 Not Modified - use cached data
    if (error.response?.status === 304) {
      error.isNotModified = true;
    }

    return Promise.reject(error);
  }
);

export default apiClient;
