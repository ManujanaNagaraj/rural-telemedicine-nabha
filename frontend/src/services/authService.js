import apiClient from './apiClient';

const AUTH_ENDPOINT = '/auth';

/**
 * Authentication Service - Handles login, logout, token refresh, and user state
 */
const authService = {
  /**
   * Login with email/password and receive JWT tokens
   */
  login: async (email, password) => {
    try {
      const response = await apiClient.post(`${AUTH_ENDPOINT}/token/`, {
        email,
        password,
      });

      const { access, refresh, user } = response.data;

      // Store tokens in localStorage
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user', JSON.stringify(user));

      return { access, refresh, user };
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  },

  /**
   * Logout - Clear tokens and user data
   */
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('last_sync_timestamp');
  },

  /**
   * Get current authenticated user from localStorage or fetch from API
   */
  getCurrentUser: async () => {
    try {
      // First try localStorage
      const cachedUser = localStorage.getItem('user');
      if (cachedUser) {
        return JSON.parse(cachedUser);
      }

      // If not cached, fetch from API
      const response = await apiClient.get(`${AUTH_ENDPOINT}/me/`);
      const user = response.data;
      localStorage.setItem('user', JSON.stringify(user));

      return user;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch user');
    }
  },

  /**
   * Refresh JWT token using refresh token
   */
  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await apiClient.post(`${AUTH_ENDPOINT}/token/refresh/`, {
        refresh: refreshToken,
      });

      const { access } = response.data;
      localStorage.setItem('access_token', access);

      return access;
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      throw new Error(error.response?.data?.detail || 'Token refresh failed');
    }
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },

  /**
   * Get stored access token
   */
  getAccessToken: () => {
    return localStorage.getItem('access_token');
  },

  /**
   * Validate token expiry (basic check)
   */
  isTokenExpired: () => {
    const token = localStorage.getItem('access_token');
    if (!token) return true;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return Date.now() >= payload.exp * 1000;
    } catch {
      return true;
    }
  },
};

export default authService;
