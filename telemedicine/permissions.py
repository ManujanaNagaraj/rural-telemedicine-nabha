from rest_framework import permissions

class IsPatient(permissions.BasePermission):
    """
    Permission to check if user is a patient.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'patient')


class IsDoctor(permissions.BasePermission):
    """
    Permission to check if user is a doctor.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'doctor')


class IsOwnPatientRecord(permissions.BasePermission):
    """
    Permission to check if user can only access their own patient record.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            # Admin can access all
            if request.user.is_staff:
                return True
            # Patient can only access their own record
            if hasattr(request.user, 'patient'):
                return obj.user == request.user
        return False


class IsOwnDoctorRecord(permissions.BasePermission):
    """
    Permission to check if user can only access their own doctor record.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            # Admin can access all
            if request.user.is_staff:
                return True
            # Doctor can only access their own record
            if hasattr(request.user, 'doctor'):
                return obj.user == request.user
        return False


class IsAppointmentParticipant(permissions.BasePermission):
    """
    Permission to check if user is part of the appointment.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can access all
        if request.user.is_staff:
            return True
        
        # Patient can access their own appointments
        if hasattr(request.user, 'patient'):
            return obj.patient.user == request.user
        
        # Doctor can access their own appointments
        if hasattr(request.user, 'doctor'):
            return obj.doctor.user == request.user
        
        return False


class IsOwnAppointmentOrAdmin(permissions.BasePermission):
    """
    Permission to allow patients/doctors to access only their appointments.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            # Admin full access
            if request.user.is_staff:
                return True
            
            # Patient can access their appointments
            if hasattr(request.user, 'patient'):
                return obj.patient.user == request.user
            
            # Doctor can access their appointments
            if hasattr(request.user, 'doctor'):
                return obj.doctor.user == request.user
        
        return False
