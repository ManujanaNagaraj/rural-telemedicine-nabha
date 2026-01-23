/**
 * LocalStorage utilities for offline support
 */
export const storageUtils = {
  /**
   * Save data to localStorage
   */
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error(`Storage error setting ${key}:`, error);
      return false;
    }
  },

  /**
   * Get data from localStorage
   */
  get: (key) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error(`Storage error getting ${key}:`, error);
      return null;
    }
  },

  /**
   * Remove data from localStorage
   */
  remove: (key) => {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error(`Storage error removing ${key}:`, error);
      return false;
    }
  },

  /**
   * Clear all app data (except auth tokens)
   */
  clearAppData: () => {
    const authKeys = ['access_token', 'refresh_token', 'user'];
    Object.keys(localStorage).forEach((key) => {
      if (!authKeys.includes(key)) {
        localStorage.removeItem(key);
      }
    });
  },
};

/**
 * Date formatting utilities
 */
export const dateUtils = {
  /**
   * Format date to display string
   */
  formatDate: (date) => {
    if (!date) return '';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  },

  /**
   * Format date and time
   */
  formatDateTime: (date) => {
    if (!date) return '';
    return new Date(date).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  },

  /**
   * Format time only
   */
  formatTime: (date) => {
    if (!date) return '';
    return new Date(date).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  },

  /**
   * Get relative time (e.g., "2 hours ago")
   */
  getRelativeTime: (date) => {
    if (!date) return '';

    const now = new Date();
    const diffMs = now - new Date(date);
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

    return dateUtils.formatDate(date);
  },

  /**
   * Check if date is today
   */
  isToday: (date) => {
    const today = new Date();
    const d = new Date(date);
    return (
      d.getFullYear() === today.getFullYear() &&
      d.getMonth() === today.getMonth() &&
      d.getDate() === today.getDate()
    );
  },

  /**
   * Check if date is in the past
   */
  isPast: (date) => {
    return new Date(date) < new Date();
  },

  /**
   * Check if date is in the future
   */
  isFuture: (date) => {
    return new Date(date) > new Date();
  },
};

/**
 * Status display utilities
 */
export const statusUtils = {
  /**
   * Get status display text
   */
  getStatusDisplay: (status) => {
    const statusMap = {
      pending: 'Pending',
      confirmed: 'Confirmed',
      completed: 'Completed',
      cancelled: 'Cancelled',
      no_show: 'No Show',
      active: 'Active',
      inactive: 'Inactive',
      available: 'Available',
      unavailable: 'Unavailable',
    };

    return statusMap[status] || status.charAt(0).toUpperCase() + status.slice(1);
  },

  /**
   * Get status color/badge class
   */
  getStatusClass: (status) => {
    const classMap = {
      pending: 'badge-warning',
      confirmed: 'badge-info',
      completed: 'badge-success',
      cancelled: 'badge-danger',
      no_show: 'badge-secondary',
      active: 'badge-success',
      inactive: 'badge-secondary',
      available: 'badge-success',
      unavailable: 'badge-danger',
    };

    return classMap[status] || 'badge-secondary';
  },

  /**
   * Get status icon
   */
  getStatusIcon: (status) => {
    const iconMap = {
      pending: '⏳',
      confirmed: '✓',
      completed: '✓✓',
      cancelled: '✕',
      no_show: '⊘',
      active: '●',
      inactive: '○',
      available: '✓',
      unavailable: '✕',
    };

    return iconMap[status] || '•';
  },
};

/**
 * Error response utilities
 */
export const errorUtils = {
  /**
   * Extract error message from API response
   */
  getErrorMessage: (error) => {
    if (typeof error === 'string') return error;
    if (error.response?.data?.detail) return error.response.data.detail;
    if (error.response?.data?.message) return error.response.data.message;
    if (error.response?.data?.errors) {
      const errors = error.response.data.errors;
      if (Array.isArray(errors)) return errors[0];
      return Object.values(errors)[0] || 'An error occurred';
    }
    return error.message || 'An error occurred';
  },

  /**
   * Check if error is network error
   */
  isNetworkError: (error) => {
    return !error.response && (error.code === 'ECONNABORTED' || error.message === 'Network Error');
  },

  /**
   * Check if error is 409 Conflict
   */
  isConflict: (error) => {
    return error.response?.status === 409 || error.isConflict;
  },

  /**
   * Check if error is 401 Unauthorized
   */
  isUnauthorized: (error) => {
    return error.response?.status === 401;
  },

  /**
   * Check if error is 403 Forbidden
   */
  isForbidden: (error) => {
    return error.response?.status === 403;
  },

  /**
   * Check if error is 404 Not Found
   */
  isNotFound: (error) => {
    return error.response?.status === 404;
  },
};

/**
 * Format utilities
 */
export const formatUtils = {
  /**
   * Truncate text
   */
  truncate: (text, length = 50) => {
    if (!text) return '';
    return text.length > length ? text.substring(0, length) + '...' : text;
  },

  /**
   * Capitalize string
   */
  capitalize: (text) => {
    if (!text) return '';
    return text.charAt(0).toUpperCase() + text.slice(1);
  },

  /**
   * Format phone number
   */
  formatPhoneNumber: (phone) => {
    if (!phone) return '';
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    }
    return phone;
  },

  /**
   * Format currency
   */
  formatCurrency: (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(amount);
  },

  /**
   * Format file size
   */
  formatFileSize: (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  },
};
