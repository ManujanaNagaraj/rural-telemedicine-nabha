import apiClient from './apiClient';

const PHARMACIES_ENDPOINT = '/pharmacies';
const MEDICINES_ENDPOINT = '/medicines';

/**
 * Pharmacy Service - Handles pharmacy and medicine lookups
 */
const pharmacyService = {
  /**
   * Get all pharmacies
   */
  getPharmacies: async (filters = {}) => {
    try {
      const params = new URLSearchParams();

      if (filters.search) params.append('search', filters.search);
      if (filters.location) params.append('location', filters.location);

      const response = await apiClient.get(PHARMACIES_ENDPOINT, { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch pharmacies');
    }
  },

  /**
   * Get pharmacy by ID
   */
  getPharmacy: async (pharmacyId) => {
    try {
      const response = await apiClient.get(`${PHARMACIES_ENDPOINT}/${pharmacyId}/`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch pharmacy');
    }
  },

  /**
   * Get medicines with optional filtering
   */
  getMedicines: async (filters = {}) => {
    try {
      const params = new URLSearchParams();

      if (filters.search) params.append('search', filters.search);
      if (filters.category) params.append('category', filters.category);

      const response = await apiClient.get(MEDICINES_ENDPOINT, { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch medicines');
    }
  },

  /**
   * Get pharmacy inventory with availability
   */
  getPharmacyInventory: async (pharmacyId, filters = {}) => {
    try {
      const params = new URLSearchParams();

      if (filters.medicine_id) params.append('medicine_id', filters.medicine_id);
      if (filters.in_stock) params.append('in_stock', filters.in_stock);

      const response = await apiClient.get(
        `/pharmacies/${pharmacyId}/inventory/`,
        { params }
      );

      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch inventory');
    }
  },

  /**
   * Check medicine availability at pharmacy
   */
  checkAvailability: async (pharmacyId, medicineId) => {
    try {
      const response = await apiClient.get(
        `/pharmacies/${pharmacyId}/medicines/${medicineId}/availability/`
      );
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to check availability');
    }
  },

  /**
   * Search medicines by name/category
   */
  searchMedicines: async (query) => {
    try {
      const response = await apiClient.get(MEDICINES_ENDPOINT, {
        params: { search: query },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to search medicines');
    }
  },

  /**
   * Get medicine categories
   */
  getMedicineCategories: async () => {
    try {
      const response = await apiClient.get(`${MEDICINES_ENDPOINT}/categories/`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch categories');
    }
  },

  /**
   * Format pharmacy for display
   */
  formatPharmacy: (pharmacy) => {
    return {
      ...pharmacy,
      contact_display: `${pharmacy.phone || ''} - ${pharmacy.email || ''}`,
      hours_display: pharmacy.operating_hours || 'Unknown',
    };
  },

  /**
   * Format medicine for display
   */
  formatMedicine: (medicine) => {
    return {
      ...medicine,
      display_name: `${medicine.name} (${medicine.strength || ''})`,
      category_display:
        medicine.category.charAt(0).toUpperCase() + medicine.category.slice(1),
    };
  },
};

export default pharmacyService;
