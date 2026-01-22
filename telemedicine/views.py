from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Patient, Doctor, Appointment
from .serializers import PatientSerializer, DoctorSerializer, AppointmentSerializer
from .permissions import (
    IsOwnPatientRecord, IsOwnDoctorRecord, IsAppointmentParticipant,
    CannotCreatePatientForOthers, CannotCreateDoctorForOthers,
    CannotModifyCompletedAppointments
)
from .auth_serializers import (
    CustomTokenObtainPairSerializer, LoginSerializer, 
    UserSerializer, LogoutSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token endpoint with enhanced user information.
    """
    serializer_class = CustomTokenObtainPairSerializer


class LoginView(viewsets.ViewSet):
    """
    Login endpoint that returns JWT tokens and user info.
    """
    serializer_class = LoginSerializer
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """User login endpoint"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            # Get user type
            user_type = 'admin' if user.is_staff else 'user'
            profile_id = None
            
            if hasattr(user, 'patient'):
                user_type = 'patient'
                profile_id = user.patient.id
            elif hasattr(user, 'doctor'):
                user_type = 'doctor'
                profile_id = user.doctor.id
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'user_type': user_type,
                'profile_id': profile_id,
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """User logout endpoint - blacklist refresh token"""
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            try:
                refresh_token = serializer.validated_data['refresh']
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response(
                    {'detail': 'Successfully logged out'},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user information"""
        user = request.user
        
        user_type = 'admin' if user.is_staff else 'user'
        profile_id = None
        
        if hasattr(user, 'patient'):
            user_type = 'patient'
            profile_id = user.patient.id
        elif hasattr(user, 'doctor'):
            user_type = 'doctor'
            profile_id = user.doctor.id
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'user_type': user_type,
            'profile_id': profile_id,
        })


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Patient management with strict authentication and permissions.
    - Patients can only access their own records
    - Doctors can view patients only for their appointments
    - Admin has full access
    - Write operations strictly restricted
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated, IsOwnPatientRecord, CannotCreatePatientForOthers]
    
    def get_queryset(self):
        """Filter queryset based on user type - STRICT enforcement"""
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return Patient.objects.none()
        
        # Admin can see all
        if user.is_staff:
            return Patient.objects.all()
        
        # Patients can only see their own record
        if hasattr(user, 'patient'):
            patient = getattr(user, 'patient', None)
            if patient:
                return Patient.objects.filter(user=user)
        
        # Doctors can see patients only for their appointments
        if hasattr(user, 'doctor'):
            doctor = getattr(user, 'doctor', None)
            if doctor:
                patient_ids = Appointment.objects.filter(
                    doctor=doctor
                ).values_list('patient_id', flat=True).distinct()
                return Patient.objects.filter(id__in=patient_ids)
        
        # Unauthorized user type
        return Patient.objects.none()
    
    def perform_create(self, serializer):
        """Strict validation for patient creation"""
        # User must match the patient being created
        user_id = serializer.initial_data.get('user')
        if user_id and int(user_id) != self.request.user.id:
            raise PermissionDenied(
                detail="You can only create a patient record for yourself"
            )
        
        # Check if patient already exists for this user
        if Patient.objects.filter(user=self.request.user).exists():
            raise ValidationError(
                detail="Patient profile already exists for this user"
            )
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Strict validation for patient updates"""
        # Patients can only update their own record
        if not self.request.user.is_staff:
            if serializer.instance.user != self.request.user:
                raise PermissionDenied(
                    detail="You can only modify your own patient record"
                )
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Prevent deletion of patient records"""
        if not self.request.user.is_staff:
            raise PermissionDenied(
                detail="Patient records cannot be deleted by non-admin users"
            )
        instance.delete()


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Doctor management with strict authentication and permissions.
    - Doctors can only access their own records
    - Patients can view doctors only for their appointments
    - Admin has full access
    - Write operations strictly restricted
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated, IsOwnDoctorRecord, CannotCreateDoctorForOthers]
    
    def get_queryset(self):
        """Filter queryset based on user type - STRICT enforcement"""
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return Doctor.objects.none()
        
        # Admin can see all
        if user.is_staff:
            return Doctor.objects.all()
        
        # Doctors can only see their own record
        if hasattr(user, 'doctor'):
            doctor = getattr(user, 'doctor', None)
            if doctor:
                return Doctor.objects.filter(user=user)
        
        # Patients can see doctors they have appointments with
        if hasattr(user, 'patient'):
            patient = getattr(user, 'patient', None)
            if patient:
                doctor_ids = Appointment.objects.filter(
                    patient=patient
                ).values_list('doctor_id', flat=True).distinct()
                return Doctor.objects.filter(id__in=doctor_ids)
        
        # Unauthorized user type
        return Doctor.objects.none()
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get list of available doctors - visible to authenticated users"""
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        doctors = Doctor.objects.filter(is_available=True)
        serializer = self.get_serializer(doctors, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Strict validation for doctor creation"""
        # User must match the doctor being created
        user_id = serializer.initial_data.get('user')
        if user_id and int(user_id) != self.request.user.id:
            raise PermissionDenied(
                detail="You can only create a doctor record for yourself"
            )
        
        # Check if doctor already exists for this user
        if Doctor.objects.filter(user=self.request.user).exists():
            raise ValidationError(
                detail="Doctor profile already exists for this user"
            )
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Strict validation for doctor updates"""
        # Doctors can only update their own record
        if not self.request.user.is_staff:
            if serializer.instance.user != self.request.user:
                raise PermissionDenied(
                    detail="You can only modify your own doctor record"
                )
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Prevent deletion of doctor records"""
        if not self.request.user.is_staff:
            raise PermissionDenied(
                detail="Doctor records cannot be deleted by non-admin users"
            )
        instance.delete()


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Appointment management with strict role-based access.
    - Patients can only access their own appointments
    - Doctors can only access their assigned appointments
    - Admin has full access
    - Completed appointments cannot be modified
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsAppointmentParticipant, CannotModifyCompletedAppointments]
    
    def get_queryset(self):
        """Filter appointments based on user type - STRICT enforcement"""
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return Appointment.objects.none()
        
        # Admin can see all
        if user.is_staff:
            return Appointment.objects.all()
        
        # Patients can only see their own appointments
        if hasattr(user, 'patient'):
            patient = getattr(user, 'patient', None)
            if patient:
                return Appointment.objects.filter(patient__user=user)
        
        # Doctors can only see their assigned appointments
        if hasattr(user, 'doctor'):
            doctor = getattr(user, 'doctor', None)
            if doctor:
                return Appointment.objects.filter(doctor__user=user)
        
        # Unauthorized user type
        return Appointment.objects.none()
    
    @action(detail=False, methods=['get'])
    def my_appointments(self, request):
        """Get current user's appointments"""
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        appointments = self.get_queryset()
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update appointment status with validation"""
        appointment = self.get_object()
        status_value = request.data.get('status')
        
        # Validate status value
        valid_statuses = ['Scheduled', 'Completed', 'Cancelled', 'No-show']
        if status_value not in valid_statuses:
            return Response(
                {'detail': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Additional validation: Only doctor or admin can mark as completed
        if status_value == 'Completed' and not request.user.is_staff:
            if not hasattr(request.user, 'doctor') or appointment.doctor.user != request.user:
                raise PermissionDenied(
                    detail="Only the assigned doctor can mark an appointment as completed"
                )
        
        appointment.status = status_value
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Strict validation for appointment creation"""
        # User must be either the patient or doctor in the appointment
        patient_id = serializer.initial_data.get('patient')
        doctor_id = serializer.initial_data.get('doctor')
        
        if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id)
                # Patient can only create appointment for themselves
                if not self.request.user.is_staff:
                    if patient.user != self.request.user:
                        raise PermissionDenied(
                            detail="You can only create appointments for yourself"
                        )
            except Patient.DoesNotExist:
                raise ValidationError(detail="Invalid patient ID")
        
        if doctor_id:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
                # Doctor can create appointment for any patient
                if not self.request.user.is_staff and doctor.user != self.request.user:
                    # Only allow if user is the patient (patient creates appointment with doctor)
                    if not hasattr(self.request.user, 'patient'):
                        raise PermissionDenied(
                            detail="Invalid appointment creation request"
                        )
            except Doctor.DoesNotExist:
                raise ValidationError(detail="Invalid doctor ID")
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Strict validation for appointment updates"""
        appointment = serializer.instance
        
        # Cannot modify completed appointments
        if appointment.status == 'Completed':
            raise PermissionDenied(
                detail="Completed appointments cannot be modified"
            )
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Prevent deletion of appointments - use status change instead"""
        raise PermissionDenied(
            detail="Appointments cannot be deleted. Update status to 'Cancelled' instead"
        )
