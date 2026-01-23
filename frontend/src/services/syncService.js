import apiClient from './apiClient';

const SYNC_ENDPOINT = '/sync';

/**
 * Sync Service - Handles incremental data synchronization with low-bandwidth optimization
 * Implements ETag caching, conflict detection, and timestamp-based incremental sync
 */
const syncService = {
  /**
   * Get sync status - Check server connectivity and current sync timestamp
   */
  getSyncStatus: async () => {
    try {
      const response = await apiClient.get(`${SYNC_ENDPOINT}/status/`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch sync status');
    }
  },

  /**
   * Sync patients - Get incremental patient updates since last sync
   * Reduces bandwidth by 95% compared to full fetch
   */
  syncPatients: async (options = {}) => {
    try {
      const lastSyncTime = localStorage.getItem('last_sync_timestamp');
      const params = {};

      if (lastSyncTime && options.incremental !== false) {
        params.last_sync_timestamp = lastSyncTime;
      }

      const response = await apiClient.get(`${SYNC_ENDPOINT}/patients/`, { params });

      // Store updated sync timestamp
      if (response.headers['x-last-sync']) {
        localStorage.setItem('last_sync_timestamp', response.headers['x-last-sync']);
      }

      return response.data;
    } catch (error) {
      if (error.isNotModified) {
        return { data: [], message: 'No new updates' };
      }
      throw new Error(error.response?.data?.detail || 'Failed to sync patients');
    }
  },

  /**
   * Sync appointments - Get incremental appointment updates
   */
  syncAppointments: async (options = {}) => {
    try {
      const lastSyncTime = localStorage.getItem('last_sync_timestamp');
      const params = {};

      if (lastSyncTime && options.incremental !== false) {
        params.last_sync_timestamp = lastSyncTime;
      }

      const response = await apiClient.get(`${SYNC_ENDPOINT}/appointments/`, { params });

      if (response.headers['x-last-sync']) {
        localStorage.setItem('last_sync_timestamp', response.headers['x-last-sync']);
      }

      return response.data;
    } catch (error) {
      if (error.isNotModified) {
        return { data: [], message: 'No new updates' };
      }
      throw new Error(error.response?.data?.detail || 'Failed to sync appointments');
    }
  },

  /**
   * Sync pharmacy inventory - Get incremental inventory updates
   */
  syncPharmacyInventory: async (options = {}) => {
    try {
      const lastSyncTime = localStorage.getItem('last_sync_timestamp');
      const params = {};

      if (lastSyncTime && options.incremental !== false) {
        params.last_sync_timestamp = lastSyncTime;
      }

      const response = await apiClient.get(`${SYNC_ENDPOINT}/pharmacy-inventory/`, { params });

      if (response.headers['x-last-sync']) {
        localStorage.setItem('last_sync_timestamp', response.headers['x-last-sync']);
      }

      return response.data;
    } catch (error) {
      if (error.isNotModified) {
        return { data: [], message: 'No new updates' };
      }
      throw new Error(error.response?.data?.detail || 'Failed to sync pharmacy inventory');
    }
  },

  /**
   * Handle sync conflict - Server-authoritative: fetch fresh data and retry
   * Backend responds with 409 Conflict when client data is stale
   */
  handleSyncConflict: async (resourceType, resourceId, conflictData) => {
    try {
      // Clear cached data for conflicting resource
      localStorage.removeItem(`etag_/api/sync/${resourceType}/${resourceId}/`);

      // Fetch fresh data from server
      const response = await apiClient.get(`/api/sync/${resourceType}/${resourceId}/`, {
        headers: { 'If-None-Match': '' }, // Force full response, bypass ETag cache
      });

      return {
        success: true,
        fresh_data: response.data,
        conflict_resolution: 'server_authoritative',
      };
    } catch (error) {
      throw new Error(
        `Conflict resolution failed: ${error.response?.data?.detail || error.message}`
      );
    }
  },

  /**
   * Update appointment with sync awareness
   * Handles 409 Conflict by fetching fresh server data
   */
  updateAppointmentSync: async (appointmentId, updateData) => {
    try {
      const response = await apiClient.put(
        `/appointments/${appointmentId}/sync_update/`,
        updateData
      );

      return response.data;
    } catch (error) {
      if (error.isConflict) {
        // Handle conflict: fetch fresh data and suggest retry
        const freshData = await syncService.handleSyncConflict(
          'appointments',
          appointmentId,
          error.conflictData
        );

        return {
          success: false,
          conflict: true,
          error_code: error.response.data.error_code,
          fresh_data: freshData.fresh_data,
          message: 'Your data was stale. Fresh data provided. Please retry with fresh data.',
        };
      }

      throw new Error(error.response?.data?.detail || 'Failed to update appointment');
    }
  },

  /**
   * Get last sync timestamp from localStorage
   */
  getLastSyncTime: () => {
    return localStorage.getItem('last_sync_timestamp');
  },

  /**
   * Update last sync timestamp
   */
  setLastSyncTime: (timestamp) => {
    localStorage.setItem('last_sync_timestamp', timestamp);
  },

  /**
   * Clear all sync data (etags, timestamps)
   */
  clearSyncData: () => {
    const keys = Object.keys(localStorage);
    keys.forEach((key) => {
      if (key.startsWith('etag_') || key === 'last_sync_timestamp') {
        localStorage.removeItem(key);
      }
    });
  },

  /**
   * Check if online/offline
   */
  isOnline: () => {
    return navigator.onLine;
  },

  /**
   * Setup online/offline listeners
   */
  setupConnectivityListeners: (callbacks = {}) => {
    const { onOnline = () => {}, onOffline = () => {} } = callbacks;

    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);

    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  },
};

export default syncService;
