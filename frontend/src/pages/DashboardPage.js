import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSync } from '../context/SyncContext';
import { statusUtils, dateUtils } from '../utils';

function DashboardPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { syncStatus, syncAll } = useSync();
  const [stats, setStats] = useState({
    pendingAppointments: 0,
    completedAppointments: 0,
    unreadNotifications: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load dashboard data
    const loadData = async () => {
      try {
        setLoading(true);
        // In a real app, you'd fetch this from the API
        setStats({
          pendingAppointments: 3,
          completedAppointments: 12,
          unreadNotifications: 2,
        });
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleSyncAll = async () => {
    await syncAll();
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingCenter}>Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.headerContent}>
          <h1 style={styles.appTitle}>Nabha Telemedicine</h1>
          <div style={styles.headerRight}>
            <span style={styles.userInfo}>Welcome, {user?.first_name || 'User'}</span>
            <button onClick={handleLogout} style={styles.logoutButton}>
              Logout
            </button>
          </div>
        </div>
      </header>

      <div style={styles.content}>
        <div style={styles.syncBar}>
          <div style={styles.syncInfo}>
            <span style={statusUtils.getStatusClass(syncStatus.isOnline ? 'active' : 'inactive')}>
              {syncStatus.isOnline ? '● Online' : '● Offline'}
            </span>
            {syncStatus.lastSyncTime && (
              <span style={styles.syncTime}>
                Last sync: {dateUtils.getRelativeTime(syncStatus.lastSyncTime)}
              </span>
            )}
          </div>
          <button
            onClick={handleSyncAll}
            disabled={syncStatus.isSyncing || !syncStatus.isOnline}
            style={{
              ...styles.syncButton,
              opacity: syncStatus.isSyncing ? 0.6 : 1,
            }}
          >
            {syncStatus.isSyncing ? '⟳ Syncing...' : '⟳ Sync Now'}
          </button>
        </div>

        {syncStatus.syncError && (
          <div style={styles.errorAlert}>{syncStatus.syncError}</div>
        )}

        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <div style={styles.statNumber}>{stats.pendingAppointments}</div>
            <div style={styles.statLabel}>Pending Appointments</div>
            <button
              onClick={() => navigate('/appointments')}
              style={styles.cardButton}
            >
              View All
            </button>
          </div>

          <div style={styles.statCard}>
            <div style={styles.statNumber}>{stats.completedAppointments}</div>
            <div style={styles.statLabel}>Completed</div>
            <button
              onClick={() => navigate('/appointments')}
              style={styles.cardButton}
            >
              View History
            </button>
          </div>

          <div style={styles.statCard}>
            <div style={styles.statNumber}>{stats.unreadNotifications}</div>
            <div style={styles.statLabel}>Unread Notifications</div>
            <button
              onClick={() => navigate('/notifications')}
              style={styles.cardButton}
            >
              View All
            </button>
          </div>
        </div>

        <div style={styles.quickActions}>
          <h2 style={styles.sectionTitle}>Quick Actions</h2>
          <div style={styles.actionButtons}>
            <button
              onClick={() => navigate('/appointments')}
              style={styles.actionButton}
            >
              📅 Manage Appointments
            </button>
            <button
              onClick={() => navigate('/symptom-checker')}
              style={styles.actionButton}
            >
              🔍 Symptom Checker
            </button>
            <button
              onClick={() => navigate('/pharmacy')}
              style={styles.actionButton}
            >
              💊 Find Pharmacy
            </button>
            <button
              onClick={() => navigate('/notifications')}
              style={styles.actionButton}
            >
              🔔 Notifications
            </button>
          </div>
        </div>

        <div style={styles.infoBox}>
          <h3 style={styles.infoTitle}>Low-Bandwidth Optimized</h3>
          <p style={styles.infoText}>
            This app is optimized for rural areas with limited connectivity. All data syncs
            automatically when online, and you can continue working offline.
          </p>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
  },
  header: {
    backgroundColor: '#2c3e50',
    color: 'white',
    padding: '20px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  headerContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  appTitle: {
    margin: '0',
    fontSize: '24px',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
  },
  userInfo: {
    fontSize: '14px',
  },
  logoutButton: {
    padding: '8px 16px',
    backgroundColor: '#e74c3c',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  content: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '20px',
  },
  syncBar: {
    backgroundColor: 'white',
    padding: '12px 16px',
    borderRadius: '4px',
    marginBottom: '20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
  },
  syncInfo: {
    display: 'flex',
    gap: '20px',
    fontSize: '14px',
  },
  syncTime: {
    color: '#7f8c8d',
    fontSize: '12px',
  },
  syncButton: {
    padding: '8px 16px',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  errorAlert: {
    backgroundColor: '#f8d7da',
    color: '#721c24',
    padding: '12px',
    borderRadius: '4px',
    marginBottom: '20px',
    border: '1px solid #f5c6cb',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '20px',
    marginBottom: '30px',
  },
  statCard: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
    textAlign: 'center',
  },
  statNumber: {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#3498db',
    marginBottom: '10px',
  },
  statLabel: {
    color: '#7f8c8d',
    marginBottom: '15px',
    fontSize: '14px',
  },
  cardButton: {
    width: '100%',
    padding: '8px',
    backgroundColor: '#ecf0f1',
    border: '1px solid #bdc3c7',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
  },
  quickActions: {
    marginBottom: '30px',
  },
  sectionTitle: {
    color: '#2c3e50',
    marginBottom: '15px',
    fontSize: '18px',
  },
  actionButtons: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '10px',
  },
  actionButton: {
    padding: '15px',
    backgroundColor: 'white',
    border: '1px solid #bdc3c7',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'all 0.3s ease',
  },
  infoBox: {
    backgroundColor: '#e8f4f8',
    border: '1px solid #b8dce8',
    borderRadius: '4px',
    padding: '15px',
  },
  infoTitle: {
    color: '#2c3e50',
    margin: '0 0 10px 0',
    fontSize: '16px',
  },
  infoText: {
    color: '#34495e',
    margin: '0',
    fontSize: '14px',
    lineHeight: '1.5',
  },
  loadingCenter: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
  },
};

export default DashboardPage;
