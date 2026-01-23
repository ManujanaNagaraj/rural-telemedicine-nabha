import apiClient from './apiClient';

const APPOINTMENTS_ENDPOINT = '/appointments';

/**
 * Appointment Service - Handles appointment CRUD operations
 */
const appointmentService = {
  /**
   * Get all appointments for authenticated user
   */
  getAppointments: async (filters = {}) => {
    try {
      const params = new URLSearchParams();

      if (filters.status) params.append('status', filters.status);
      if (filters.doctor_id) params.append('doctor_id', filters.doctor_id);
      if (filters.date) params.append('date', filters.date);

      const response = await apiClient.get(`${APPOINTMENTS_ENDPOINT}/`, { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch appointments');
    }
  },

  /**
   * Get single appointment by ID
   */
  getAppointment: async (appointmentId) => {
    try {
      const response = await apiClient.get(`${APPOINTMENTS_ENDPOINT}/${appointmentId}/`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch appointment');
    }
  },

  /**
   * Create new appointment
   */
  createAppointment: async (appointmentData) => {
    try {
      const response = await apiClient.post(APPOINTMENTS_ENDPOINT, appointmentData);
      return response.data;
    } catch (error) {
      if (error.response?.data?.errors) {
        throw new Error(
          `Validation error: ${JSON.stringify(error.response.data.errors)}`
        );
      }
      throw new Error(error.response?.data?.detail || 'Failed to create appointment');
    }
  },

  /**
   * Update appointment
   */
  updateAppointment: async (appointmentId, updateData) => {
    try {
      const response = await apiClient.put(
        `${APPOINTMENTS_ENDPOINT}/${appointmentId}/`,
        updateData
      );
      return response.data;
    } catch (error) {
      if (error.response?.data?.errors) {
        throw new Error(
          `Validation error: ${JSON.stringify(error.response.data.errors)}`
        );
      }
      throw new Error(error.response?.data?.detail || 'Failed to update appointment');
    }
  },

  /**
   * Partial update appointment
   */
  patchAppointment: async (appointmentId, updateData) => {
    try {
      const response = await apiClient.patch(
        `${APPOINTMENTS_ENDPOINT}/${appointmentId}/`,
        updateData
      );
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to update appointment');
    }
  },

  /**
   * Cancel appointment
   */
  cancelAppointment: async (appointmentId, reason = '') => {
    try {
      const response = await apiClient.patch(`${APPOINTMENTS_ENDPOINT}/${appointmentId}/`, {
        status: 'cancelled',
        cancellation_reason: reason,
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to cancel appointment');
    }
  },

  /**
   * Reschedule appointment
   */
  rescheduleAppointment: async (appointmentId, newScheduledTime) => {
    try {
      const response = await apiClient.patch(`${APPOINTMENTS_ENDPOINT}/${appointmentId}/`, {
        scheduled_time: newScheduledTime,
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to reschedule appointment');
    }
  },

  /**
   * Get appointment status options
   */
  getStatusOptions: () => {
    return ['pending', 'confirmed', 'completed', 'cancelled', 'no_show'];
  },

  /**
   * Format appointment for display
   */
  formatAppointment: (appointment) => {
    return {
      ...appointment,
      scheduled_time_formatted: new Date(appointment.scheduled_time).toLocaleString(),
      status_display: appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1),
    };
  },
};

export default appointmentService;
