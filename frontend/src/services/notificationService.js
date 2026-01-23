import apiClient from './apiClient';

const NOTIFICATIONS_ENDPOINT = '/notifications';

/**
 * Notification Service - Handles notification retrieval and management
 */
const notificationService = {
  /**
   * Get all notifications for authenticated user
   */
  getNotifications: async (filters = {}) => {
    try {
      const params = new URLSearchParams();

      if (filters.unread_only) params.append('unread', 'true');
      if (filters.type) params.append('type', filters.type);
      if (filters.limit) params.append('limit', filters.limit);

      const response = await apiClient.get(NOTIFICATIONS_ENDPOINT, { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch notifications');
    }
  },

  /**
   * Get single notification by ID
   */
  getNotification: async (notificationId) => {
    try {
      const response = await apiClient.get(`${NOTIFICATIONS_ENDPOINT}/${notificationId}/`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch notification');
    }
  },

  /**
   * Mark notification as read
   */
  markAsRead: async (notificationId) => {
    try {
      const response = await apiClient.patch(`${NOTIFICATIONS_ENDPOINT}/${notificationId}/`, {
        is_read: true,
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to mark notification as read');
    }
  },

  /**
   * Mark all notifications as read
   */
  markAllAsRead: async () => {
    try {
      const response = await apiClient.post(`${NOTIFICATIONS_ENDPOINT}/mark-all-read/`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to mark notifications as read');
    }
  },

  /**
   * Delete notification
   */
  deleteNotification: async (notificationId) => {
    try {
      await apiClient.delete(`${NOTIFICATIONS_ENDPOINT}/${notificationId}/`);
      return { success: true };
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to delete notification');
    }
  },

  /**
   * Get notification types
   */
  getNotificationTypes: () => {
    return [
      { value: 'appointment', label: 'Appointment Updates' },
      { value: 'prescription', label: 'Prescription Updates' },
      { value: 'message', label: 'Messages' },
      { value: 'system', label: 'System Alerts' },
    ];
  },

  /**
   * Get unread count
   */
  getUnreadCount: async () => {
    try {
      const response = await apiClient.get(`${NOTIFICATIONS_ENDPOINT}/unread-count/`);
      return response.data.unread_count || 0;
    } catch (error) {
      return 0;
    }
  },

  /**
   * Format notification for display
   */
  formatNotification: (notification) => {
    return {
      ...notification,
      created_at_formatted: new Date(notification.created_at).toLocaleString(),
      type_display:
        notificationService
          .getNotificationTypes()
          .find((t) => t.value === notification.type)?.label || notification.type,
    };
  },

  /**
   * Setup polling for new notifications
   */
  startNotificationPolling: (callback, interval = 30000) => {
    const pollInterval = setInterval(async () => {
      try {
        const notifications = await notificationService.getNotifications({ unread_only: true });
        callback(notifications);
      } catch (error) {
        console.error('Notification polling error:', error);
      }
    }, interval);

    return () => clearInterval(pollInterval);
  },
};

export default notificationService;
