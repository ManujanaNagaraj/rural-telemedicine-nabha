import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { appointmentService } from '../services';
import { useSync } from '../context/SyncContext';
import { statusUtils, dateUtils } from '../utils';

function AppointmentsListPage() {
  const navigate = useNavigate();
  const { syncStatus } = useSync();
  const [appointments, setAppointments] = useState([]);
  const [filteredAppointments, setFilteredAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    loadAppointments();
  }, []);

  useEffect(() => {
    // Filter appointments based on selected status
    let filtered = appointments;
    if (statusFilter !== 'all') {
      filtered = appointments.filter((apt) => apt.status === statusFilter);
    }
    filtered.sort((a, b) => new Date(b.scheduled_time) - new Date(a.scheduled_time));
    setFilteredAppointments(filtered);
  }, [appointments, statusFilter]);

  const loadAppointments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await appointmentService.getAppointments();
      setAppointments(data.results || data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelAppointment = async (appointmentId) => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) {
      return;
    }

    try {
      await appointmentService.cancelAppointment(appointmentId, 'Cancelled by user');
      setAppointments((prev) =>
        prev.map((apt) =>
          apt.id === appointmentId ? { ...apt, status: 'cancelled' } : apt
        )
      );
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <button onClick={() => navigate('/dashboard')} style={styles.backButton}>
            ← Back
          </button>
          <h1>Appointments</h1>
        </div>
        <div style={styles.loadingCenter}>Loading appointments...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <button onClick={() => navigate('/dashboard')} style={styles.backButton}>
          ← Back
        </button>
        <h1>Appointments</h1>
        <button
          onClick={() => navigate('/appointments/new')}
          style={styles.newButton}
        >
          + New Appointment
        </button>
      </div>

      {error && <div style={styles.errorAlert}>{error}</div>}

      <div style={styles.filters}>
        <label style={styles.filterLabel}>Filter by Status:</label>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={styles.filterSelect}
        >
          <option value="all">All</option>
          {appointmentService.getStatusOptions().map((status) => (
            <option key={status} value={status}>
              {statusUtils.getStatusDisplay(status)}
            </option>
          ))}
        </select>
      </div>

      {filteredAppointments.length === 0 ? (
        <div style={styles.emptyState}>
          <p>No appointments found</p>
          <button
            onClick={() => navigate('/appointments/new')}
            style={styles.primaryButton}
          >
            Schedule Your First Appointment
          </button>
        </div>
      ) : (
        <div style={styles.appointmentsList}>
          {filteredAppointments.map((appointment) => (
            <div
              key={appointment.id}
              style={styles.appointmentCard}
              onClick={() => navigate(`/appointments/${appointment.id}`)}
            >
              <div style={styles.cardHeader}>
                <div style={styles.cardTitle}>
                  {appointment.doctor_name || 'Doctor'}
                </div>
                <div style={{
                  ...styles.badge,
                  ...styles[statusUtils.getStatusClass(appointment.status)],
                }}>
                  {statusUtils.getStatusDisplay(appointment.status)}
                </div>
              </div>

              <div style={styles.cardBody}>
                <div style={styles.appointmentDetail}>
                  <span style={styles.detailLabel}>📅 Date & Time:</span>
                  <span style={styles.detailValue}>
                    {dateUtils.formatDateTime(appointment.scheduled_time)}
                  </span>
                </div>

                {appointment.reason && (
                  <div style={styles.appointmentDetail}>
                    <span style={styles.detailLabel}>📝 Reason:</span>
                    <span style={styles.detailValue}>{appointment.reason}</span>
                  </div>
                )}

                {appointment.appointment_type && (
                  <div style={styles.appointmentDetail}>
                    <span style={styles.detailLabel}>🏥 Type:</span>
                    <span style={styles.detailValue}>{appointment.appointment_type}</span>
                  </div>
                )}
              </div>

              <div style={styles.cardFooter}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/appointments/${appointment.id}`);
                  }}
                  style={styles.viewButton}
                >
                  View Details
                </button>

                {appointment.status === 'pending' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCancelAppointment(appointment.id);
                    }}
                    style={styles.cancelButton}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={styles.syncInfo}>
        <span style={styles.syncStatus}>
          {syncStatus.isOnline ? '✓ Online' : '✗ Offline (Cached Data)'}
        </span>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    padding: '20px',
    fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
    marginBottom: '30px',
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
  },
  backButton: {
    padding: '8px 16px',
    backgroundColor: '#ecf0f1',
    border: '1px solid #bdc3c7',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  newButton: {
    marginLeft: 'auto',
    padding: '8px 16px',
    backgroundColor: '#27ae60',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  filters: {
    display: 'flex',
    alignItems: 'center',
    gap: '15px',
    marginBottom: '20px',
    backgroundColor: 'white',
    padding: '15px',
    borderRadius: '4px',
  },
  filterLabel: {
    fontSize: '14px',
    fontWeight: '500',
  },
  filterSelect: {
    padding: '8px 12px',
    border: '1px solid #bdc3c7',
    borderRadius: '4px',
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
  appointmentsList: {
    display: 'grid',
    gap: '15px',
    marginBottom: '20px',
  },
  appointmentCard: {
    backgroundColor: 'white',
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
    cursor: 'pointer',
    transition: 'box-shadow 0.3s ease',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '15px',
    borderBottom: '1px solid #ecf0f1',
    backgroundColor: '#f9f9f9',
  },
  cardTitle: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#2c3e50',
  },
  badge: {
    padding: '4px 12px',
    borderRadius: '20px',
    fontSize: '12px',
    fontWeight: '600',
  },
  'badge-info': {
    backgroundColor: '#d1ecf1',
    color: '#0c5460',
  },
  'badge-warning': {
    backgroundColor: '#fff3cd',
    color: '#856404',
  },
  'badge-success': {
    backgroundColor: '#d4edda',
    color: '#155724',
  },
  'badge-danger': {
    backgroundColor: '#f8d7da',
    color: '#721c24',
  },
  cardBody: {
    padding: '15px',
  },
  appointmentDetail: {
    display: 'flex',
    alignItems: 'center',
    marginBottom: '10px',
    gap: '10px',
  },
  detailLabel: {
    fontSize: '13px',
    fontWeight: '500',
    color: '#7f8c8d',
    minWidth: '100px',
  },
  detailValue: {
    fontSize: '13px',
    color: '#2c3e50',
  },
  cardFooter: {
    display: 'flex',
    gap: '10px',
    padding: '15px',
    borderTop: '1px solid #ecf0f1',
    backgroundColor: '#f9f9f9',
  },
  viewButton: {
    flex: 1,
    padding: '8px 12px',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '13px',
  },
  cancelButton: {
    flex: 1,
    padding: '8px 12px',
    backgroundColor: '#e74c3c',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '13px',
  },
  primaryButton: {
    padding: '12px 24px',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    marginTop: '15px',
  },
  emptyState: {
    backgroundColor: 'white',
    padding: '40px',
    borderRadius: '8px',
    textAlign: 'center',
    marginBottom: '20px',
  },
  loadingCenter: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '400px',
  },
  syncInfo: {
    textAlign: 'center',
    fontSize: '12px',
    color: '#7f8c8d',
    marginTop: '20px',
  },
  syncStatus: {
    padding: '8px 12px',
    backgroundColor: 'white',
    borderRadius: '4px',
    display: 'inline-block',
  },
};

export default AppointmentsListPage;
