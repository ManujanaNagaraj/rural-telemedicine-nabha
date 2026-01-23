/**
 * Email validation
 */
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Password validation
 */
export const validatePassword = (password) => {
  // At least 8 characters, uppercase, lowercase, number
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
  return passwordRegex.test(password);
};

/**
 * Phone number validation
 */
export const validatePhoneNumber = (phone) => {
  const phoneRegex = /^[\d\s\-\+\(\)]+$/;
  return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10;
};

/**
 * Form field validation
 */
export const validateField = (name, value) => {
  const errors = {};

  switch (name) {
    case 'email':
      if (!value) {
        errors.email = 'Email is required';
      } else if (!validateEmail(value)) {
        errors.email = 'Invalid email format';
      }
      break;

    case 'password':
      if (!value) {
        errors.password = 'Password is required';
      } else if (value.length < 8) {
        errors.password = 'Password must be at least 8 characters';
      }
      break;

    case 'phone':
      if (value && !validatePhoneNumber(value)) {
        errors.phone = 'Invalid phone number';
      }
      break;

    case 'appointmentTime':
      if (!value) {
        errors.appointmentTime = 'Appointment time is required';
      } else if (new Date(value) < new Date()) {
        errors.appointmentTime = 'Appointment time must be in the future';
      }
      break;

    case 'notes':
      if (value && value.length > 500) {
        errors.notes = 'Notes must be 500 characters or less';
      }
      break;

    default:
      if (!value) {
        errors[name] = `${name} is required`;
      }
  }

  return errors;
};

/**
 * Validate form data
 */
export const validateFormData = (data, requiredFields = []) => {
  const errors = {};

  requiredFields.forEach((field) => {
    if (!data[field]) {
      errors[field] = `${field} is required`;
    }
  });

  // Email validation
  if (data.email && !validateEmail(data.email)) {
    errors.email = 'Invalid email format';
  }

  // Password validation if present
  if (data.password && data.password.length < 8) {
    errors.password = 'Password must be at least 8 characters';
  }

  // Phone validation if present
  if (data.phone && !validatePhoneNumber(data.phone)) {
    errors.phone = 'Invalid phone number';
  }

  return errors;
};

/**
 * Check if form has errors
 */
export const hasErrors = (errors) => {
  return Object.keys(errors).length > 0;
};

/**
 * Get first error message
 */
export const getFirstError = (errors) => {
  const errorKeys = Object.keys(errors);
  return errorKeys.length > 0 ? errors[errorKeys[0]] : null;
};

/**
 * Format error messages for display
 */
export const formatErrorMessage = (error) => {
  if (typeof error === 'string') {
    return error;
  }

  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }

  if (error.response?.data?.errors) {
    return Object.values(error.response.data.errors).flat().join(', ');
  }

  return error.message || 'An error occurred';
};

/**
 * Debounce function for form input
 */
export const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

/**
 * Throttle function for sync operations
 */
export const throttle = (func, limit) => {
  let lastRun = 0;
  return (...args) => {
    const now = Date.now();
    if (now - lastRun >= limit) {
      func(...args);
      lastRun = now;
    }
  };
};
