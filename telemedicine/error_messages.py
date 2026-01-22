"""
Standardized Error Messages for API Responses
Ensures consistent 401/403 error messages across all endpoints
"""

from rest_framework import status


class ErrorMessages:
    """
    Standardized error messages for permission and validation errors.
    All messages are descriptive but safe - no sensitive information leakage.
    """
    
    # ============================================================================
    # 401 UNAUTHORIZED - Authentication Issues
    # ============================================================================
    
    AUTH_CREDENTIALS_REQUIRED = "Authentication credentials were not provided."
    AUTH_INVALID_TOKEN = "Given token is invalid or has expired."
    AUTH_MALFORMED_TOKEN = "Token is malformed or invalid."
    AUTH_SESSION_EXPIRED = "Authentication session has expired. Please login again."
    
    # ============================================================================
    # 403 FORBIDDEN - Patient Record Access/Modification
    # ============================================================================
    
    PATIENT_CREATE_OTHER = "You can only create a patient record for yourself."
    PATIENT_MODIFY_OTHER = "You can only modify your own patient record."
    PATIENT_DELETE_RESTRICTED = "Patient records cannot be deleted by non-admin users."
    PATIENT_DUPLICATE = "Patient profile already exists for this user."
    PATIENT_ACCESS_DENIED = "You do not have permission to access this patient record."
    
    # ============================================================================
    # 403 FORBIDDEN - Doctor Record Access/Modification
    # ============================================================================
    
    DOCTOR_CREATE_OTHER = "You can only create a doctor record for yourself."
    DOCTOR_MODIFY_OTHER = "You can only modify your own doctor record."
    DOCTOR_DELETE_RESTRICTED = "Doctor records cannot be deleted by non-admin users."
    DOCTOR_DUPLICATE = "Doctor profile already exists for this user."
    DOCTOR_ACCESS_DENIED = "You do not have permission to access this doctor record."
    
    # ============================================================================
    # 403 FORBIDDEN - Appointment Access/Modification
    # ============================================================================
    
    APPOINTMENT_CREATE_SELF = "You can only create appointments for yourself."
    APPOINTMENT_MODIFY_COMPLETED = "Completed appointments cannot be modified."
    APPOINTMENT_DELETE_RESTRICTED = "Appointments cannot be deleted. Update status to 'Cancelled' instead."
    APPOINTMENT_UPDATE_ROLE = "Only the assigned doctor can mark an appointment as completed."
    APPOINTMENT_ACCESS_DENIED = "You do not have permission to access this appointment."
    
    # ============================================================================
    # 400 BAD REQUEST - Validation Errors
    # ============================================================================
    
    INVALID_PATIENT_ID = "Invalid patient ID. Please verify and try again."
    INVALID_DOCTOR_ID = "Invalid doctor ID. Please verify and try again."
    INVALID_STATUS = "Invalid status value. Must be one of: Scheduled, Completed, Cancelled, No-show."
    INVALID_REQUEST = "Invalid request. Please verify your input and try again."
    
    # ============================================================================
    # 404 NOT FOUND - Resource Not Found (also used for permission hiding)
    # ============================================================================
    
    RESOURCE_NOT_FOUND = "The requested resource was not found."
    
    @staticmethod
    def get_forbidden_response(message):
        """
        Generate a 403 Forbidden response.
        
        Args:
            message (str): Error message from ErrorMessages constants
            
        Returns:
            dict: Response structure with status and detail
        """
        return {
            "status": status.HTTP_403_FORBIDDEN,
            "detail": message
        }
    
    @staticmethod
    def get_unauthorized_response(message):
        """
        Generate a 401 Unauthorized response.
        
        Args:
            message (str): Error message from ErrorMessages constants
            
        Returns:
            dict: Response structure with status and detail
        """
        return {
            "status": status.HTTP_401_UNAUTHORIZED,
            "detail": message
        }
    
    @staticmethod
    def get_validation_error_response(message):
        """
        Generate a 400 Bad Request response.
        
        Args:
            message (str): Error message from ErrorMessages constants
            
        Returns:
            dict: Response structure with status and detail
        """
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "detail": message
        }
