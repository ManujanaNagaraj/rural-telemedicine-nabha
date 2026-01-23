import React, { createContext, useState, useCallback } from 'react';
import syncService from '../services/syncService';

export const SyncContext = createContext();

/**
 * SyncProvider - Manages sync state and provides sync operations to components
 */
export function SyncProvider({ children }) {
  const [syncStatus, setSyncStatus] = useState({
    isOnline: navigator.onLine,
    isSyncing: false,
    lastSyncTime: syncService.getLastSyncTime(),
    syncError: null,
  });

  /**
   * Setup connectivity listeners
   */
  React.useEffect(() => {
    const unsubscribe = syncService.setupConnectivityListeners({
      onOnline: () => {
        setSyncStatus((prev) => ({
          ...prev,
          isOnline: true,
          syncError: null,
        }));
      },
      onOffline: () => {
        setSyncStatus((prev) => ({
          ...prev,
          isOnline: false,
        }));
      },
    });

    return unsubscribe;
  }, []);

  /**
   * Perform sync operation
   */
  const performSync = useCallback(async (syncFn, resourceType) => {
    try {
      setSyncStatus((prev) => ({
        ...prev,
        isSyncing: true,
        syncError: null,
      }));

      const result = await syncFn();

      setSyncStatus((prev) => ({
        ...prev,
        isSyncing: false,
        lastSyncTime: syncService.getLastSyncTime(),
      }));

      return { success: true, data: result };
    } catch (error) {
      setSyncStatus((prev) => ({
        ...prev,
        isSyncing: false,
        syncError: error.message,
      }));

      return { success: false, error: error.message };
    }
  }, []);

  /**
   * Sync patients
   */
  const syncPatients = useCallback(
    async (options = {}) => performSync(() => syncService.syncPatients(options), 'patients'),
    [performSync]
  );

  /**
   * Sync appointments
   */
  const syncAppointments = useCallback(
    async (options = {}) =>
      performSync(() => syncService.syncAppointments(options), 'appointments'),
    [performSync]
  );

  /**
   * Sync pharmacy inventory
   */
  const syncInventory = useCallback(
    async (options = {}) =>
      performSync(() => syncService.syncPharmacyInventory(options), 'inventory'),
    [performSync]
  );

  /**
   * Sync all resources
   */
  const syncAll = useCallback(async (options = {}) => {
    try {
      setSyncStatus((prev) => ({
        ...prev,
        isSyncing: true,
        syncError: null,
      }));

      const results = await Promise.allSettled([
        syncService.syncPatients(options),
        syncService.syncAppointments(options),
        syncService.syncPharmacyInventory(options),
      ]);

      const errors = results.filter((r) => r.status === 'rejected').map((r) => r.reason);

      setSyncStatus((prev) => ({
        ...prev,
        isSyncing: false,
        lastSyncTime: syncService.getLastSyncTime(),
        syncError: errors.length > 0 ? errors.join('; ') : null,
      }));

      return {
        success: errors.length === 0,
        results,
        errors: errors.length > 0 ? errors : null,
      };
    } catch (error) {
      setSyncStatus((prev) => ({
        ...prev,
        isSyncing: false,
        syncError: error.message,
      }));

      return { success: false, error: error.message };
    }
  }, []);

  /**
   * Clear sync error
   */
  const clearSyncError = useCallback(() => {
    setSyncStatus((prev) => ({
      ...prev,
      syncError: null,
    }));
  }, []);

  const value = {
    syncStatus,
    syncPatients,
    syncAppointments,
    syncInventory,
    syncAll,
    clearSyncError,
  };

  return <SyncContext.Provider value={value}>{children}</SyncContext.Provider>;
}

/**
 * Custom hook to use SyncContext
 */
export function useSync() {
  const context = React.useContext(SyncContext);
  if (!context) {
    throw new Error('useSync must be used within SyncProvider');
  }
  return context;
}
