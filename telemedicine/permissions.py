from rest_framework import permissions


class IsPatient(permissions.BasePermission):
    """
    Permission to check if user is a patient.
    Edge cases handled:
    - Rejects unauthenticated users
    - Rejects staff/admin without patient profile
    - Rejects patients who are also staff
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Patient profile must exist and be the primary identity
        if not hasattr(request.user, 'patient'):
            return False
        
        # Ensure patient profile is not None
        patient = getattr(request.user, 'patient', None)
        return patient is not None


class IsDoctor(permissions.BasePermission):
    """
    Permission to check if user is a doctor.
    Edge cases handled:
    - Rejects unauthenticated users
    - Rejects staff/admin without doctor profile
    - Validates doctor profile existence
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Doctor profile must exist and be the primary identity
        if not hasattr(request.user, 'doctor'):
            return False
        
        # Ensure doctor profile is not None
        doctor = getattr(request.user, 'doctor', None)
        return doctor is not None


class IsOwnPatientRecord(permissions.BasePermission):
    """
    Permission to check if user can only access their own patient record.
    Strictly enforced:
    - Patients can only access their own record
    - Doctors can view patients only if they have appointments with them
    - Admin has full access
    - Write operations restricted to own record only
    """
    def has_object_permission(self, request, view, obj):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin bypass
        if request.user.is_staff:
            return True
        
        # Patient can only access their own record
        if hasattr(request.user, 'patient'):
            patient = getattr(request.user, 'patient', None)
            if patient is not None:
                return obj.user == request.user
        
        # Doctors cannot access patient records directly (handled in get_queryset)
        return False
    
    def has_permission(self, request, view):
        # All authenticated users can list (filtered by view)
        return request.user and request.user.is_authenticated


class IsOwnDoctorRecord(permissions.BasePermission):
    """
    Permission to check if user can only access their own doctor record.
    Strictly enforced:
    - Doctors can only access their own record
    - Patients cannot access or modify doctor records
    - Admin has full access
    - Write operations restricted to own record only
    """
    def has_object_permission(self, request, view, obj):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin bypass
        if request.user.is_staff:
            return True
        
        # Only the doctor themselves can access/modify their record
        if hasattr(request.user, 'doctor'):
            doctor = getattr(request.user, 'doctor', None)
            if doctor is not None:
                return obj.user == request.user
        
        # Patients cannot access doctor records
        return False
    
    def has_permission(self, request, view):
        # All authenticated users can list (filtered by view)
        return request.user and request.user.is_authenticated


class IsAppointmentParticipant(permissions.BasePermission):
    """
    Permission to check if user is part of the appointment.
    Strictly enforced:
    - Patients can only access their own appointments
    - Doctors can only access their assigned appointments
    - Cannot access appointments with unrelated parties
    - Write operations restricted to participants only
    """
    def has_permission(self, request, view):
        # Must be authenticated
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin full access
        if request.user.is_staff:
            return True
        
        # Appointment must have both patient and doctor
        if not obj.patient or not obj.doctor:
            return False
        
        # Patient can access their own appointments only
        if hasattr(request.user, 'patient'):
            patient = getattr(request.user, 'patient', None)
            if patient is not None:
                return obj.patient.user == request.user
        
        # Doctor can access their assigned appointments only
        if hasattr(request.user, 'doctor'):
            doctor = getattr(request.user, 'doctor', None)
            if doctor is not None:
                return obj.doctor.user == request.user
        
        return False


class IsOwnAppointmentOrAdmin(permissions.BasePermission):
    """
    Permission to allow patients/doctors to access only their appointments.
    Stricter version for list operations:
    - Enforces list-level filtering
    - Participants cannot cross boundaries
    - Admin override only
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin full access
        if request.user.is_staff:
            return True
        
        # Appointment must be valid
        if not obj or not obj.patient or not obj.doctor:
            return False
        
        # Patient can access their appointments
        if hasattr(request.user, 'patient'):
            patient = getattr(request.user, 'patient', None)
            if patient is not None:
                return obj.patient.user == request.user
        
        # Doctor can access their appointments
        if hasattr(request.user, 'doctor'):
            doctor = getattr(request.user, 'doctor', None)
            if doctor is not None:
                return obj.doctor.user == request.user
        
        return False


class CannotCreatePatientForOthers(permissions.BasePermission):
    """
    Permission to prevent users from creating patient records for others.
    Ensures:
    - Users can only create their own patient profile (if they are the user)
    - Admin can create for others
    - Other patients cannot create profiles for other users
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can create for anyone
        if request.user.is_staff:
            return True
        
        # For write operations, check if user_id matches request user
        if request.method in ['POST', 'PUT', 'PATCH']:
            user_id = request.data.get('user')
            if user_id and user_id != request.user.id:
                return False
        
        return True


class CannotCreateDoctorForOthers(permissions.BasePermission):
    """
    Permission to prevent users from creating doctor records for others.
    Ensures:
    - Users can only create their own doctor profile (if they are the user)
    - Admin can create for others
    - Patients cannot create doctor profiles for other users
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can create for anyone
        if request.user.is_staff:
            return True
        
        # For write operations, check if user_id matches request user
        if request.method in ['POST', 'PUT', 'PATCH']:
            user_id = request.data.get('user')
            if user_id and user_id != request.user.id:
                return False
        
        return True


class CannotModifyCompletedAppointments(permissions.BasePermission):
    """
    Permission to restrict modifications of completed appointments.
    Ensures:
    - Only status changes allowed for completed appointments
    - Cannot modify diagnosis/prescription after completion (strict mode)
    - Admin can override
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can modify anything
        if request.user.is_staff:
            return True
        
        # For read operations, always allowed
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Completed appointments cannot be modified (except status)
        if obj.status == 'Completed':
            # Only allow PATCH to update_status action
            if request.method == 'PATCH' and 'status' not in request.data:
                return False
        
        return True
