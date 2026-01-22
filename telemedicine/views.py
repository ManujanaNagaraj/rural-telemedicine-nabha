from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
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
from .error_messages import ErrorMessages
from .ai.rule_engine import evaluate_symptoms


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
                detail=ErrorMessages.PATIENT_CREATE_OTHER
            )
        
        # Check if patient already exists for this user
        if Patient.objects.filter(user=self.request.user).exists():
            raise ValidationError(
                detail=ErrorMessages.PATIENT_DUPLICATE
            )
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Strict validation for patient updates"""
        # Patients can only update their own record
        if not self.request.user.is_staff:
            if serializer.instance.user != self.request.user:
                raise PermissionDenied(
                    detail=ErrorMessages.PATIENT_MODIFY_OTHER
                )
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Prevent deletion of patient records"""
        if not self.request.user.is_staff:
            raise PermissionDenied(
                detail=ErrorMessages.PATIENT_DELETE_RESTRICTED
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
                detail=ErrorMessages.DOCTOR_CREATE_OTHER
            )
        
        # Check if doctor already exists for this user
        if Doctor.objects.filter(user=self.request.user).exists():
            raise ValidationError(
                detail=ErrorMessages.DOCTOR_DUPLICATE
            )
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Strict validation for doctor updates"""
        # Doctors can only update their own record
        if not self.request.user.is_staff:
            if serializer.instance.user != self.request.user:
                raise PermissionDenied(
                    detail=ErrorMessages.DOCTOR_MODIFY_OTHER
                )
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Prevent deletion of doctor records"""
        if not self.request.user.is_staff:
            raise PermissionDenied(
                detail=ErrorMessages.DOCTOR_DELETE_RESTRICTED
            )
        instance.delete()


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    Enhanced ViewSet for Appointment management with production-ready lifecycle.
    
    Status Flow: PENDING → CONFIRMED → COMPLETED
                           → CANCELLED (anytime)
    
    Features:
    - Strict role-based access control
    - Double booking prevention
    - Patient overlap detection
    - Comprehensive audit trail
    - State transition validation
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsAppointmentParticipant]
    
    def get_queryset(self):
        """Filter appointments based on user type - STRICT enforcement"""
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return Appointment.objects.none()
        
        # Admin can see all
        if user.is_staff:
            return Appointment.objects.all().order_by('-appointment_date')
        
        # Patients can only see their own appointments
        if hasattr(user, 'patient'):
            patient = getattr(user, 'patient', None)
            if patient:
                return Appointment.objects.filter(patient__user=user).order_by('-appointment_date')
        
        # Doctors can only see their assigned appointments
        if hasattr(user, 'doctor'):
            doctor = getattr(user, 'doctor', None)
            if doctor:
                return Appointment.objects.filter(doctor__user=user).order_by('-appointment_date')
        
        # Unauthorized user type
        return Appointment.objects.none()
    
    @action(detail=False, methods=['get'])
    def my_appointments(self, request):
        """
        Get current user's appointments (paginated, sorted by date).
        
        Query Parameters:
        - status: Filter by status (PENDING, CONFIRMED, COMPLETED, CANCELLED, NO_SHOW)
        - upcoming: Boolean - return only future appointments
        """
        user = request.user
        
        if not user or not user.is_authenticated:
            return Response(
                {'detail': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        appointments = self.get_queryset()
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            appointments = appointments.filter(status=status_filter)
        
        # Filter for upcoming appointments if requested
        if request.query_params.get('upcoming') == 'true':
            from django.utils import timezone
            appointments = appointments.filter(appointment_date__gte=timezone.now())
        
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm an appointment (PENDING → CONFIRMED).
        
        Only doctor or admin can confirm.
        """
        appointment = self.get_object()
        
        # Permission check: Only doctor or admin can confirm
        if not request.user.is_staff:
            if not hasattr(request.user, 'doctor') or appointment.doctor.user != request.user:
                return Response(
                    {'detail': 'Only the assigned doctor or admin can confirm this appointment.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        try:
            appointment.confirm()
            serializer = self.get_serializer(appointment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark appointment as completed (CONFIRMED → COMPLETED).
        
        Only doctor or admin can mark as completed.
        """
        appointment = self.get_object()
        
        # Permission check: Only doctor or admin can complete
        if not request.user.is_staff:
            if not hasattr(request.user, 'doctor') or appointment.doctor.user != request.user:
                return Response(
                    {'detail': 'Only the assigned doctor or admin can complete this appointment.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        try:
            appointment.complete()
            serializer = self.get_serializer(appointment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an appointment with reason tracking.
        
        Request Body:
        {
            "reason": "Doctor is unavailable",
            "cancelled_by": "DOCTOR"  # or "PATIENT" or "ADMIN"
        }
        """
        appointment = self.get_object()
        
        reason = request.data.get('reason', '')
        cancelled_by = request.data.get('cancelled_by', 'ADMIN')
        
        # Permission check: Patients can only cancel their own appointments
        if not request.user.is_staff:
            if hasattr(request.user, 'patient'):
                if appointment.patient.user != request.user:
                    return Response(
                        {'detail': 'Patients can only cancel their own appointments.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                cancelled_by = 'PATIENT'
            elif hasattr(request.user, 'doctor'):
                if appointment.doctor.user != request.user:
                    return Response(
                        {'detail': 'Doctors can only cancel their own appointments.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                cancelled_by = 'DOCTOR'
            else:
                return Response(
                    {'detail': 'Unauthorized'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        try:
            appointment.cancel(reason=reason, cancelled_by=cancelled_by)
            serializer = self.get_serializer(appointment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def no_show(self, request, pk=None):
        """Mark appointment as no-show (CONFIRMED → NO_SHOW). Only doctor or admin."""
        appointment = self.get_object()
        
        # Permission check
        if not request.user.is_staff:
            if not hasattr(request.user, 'doctor') or appointment.doctor.user != request.user:
                return Response(
                    {'detail': 'Only the assigned doctor or admin can mark as no-show.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        try:
            appointment.mark_no_show()
            serializer = self.get_serializer(appointment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        """
        Get available appointment slots for a doctor on a given date.
        
        Query Parameters:
        - doctor_id: The doctor's ID
        - date: The date to check (YYYY-MM-DD format)
        - num_slots: Number of slots to return (default: 8)
        
        Example: GET /appointments/available_slots/?doctor_id=1&date=2026-01-25&num_slots=8
        """
        from .appointment_service import AppointmentService
        
        doctor_id = request.query_params.get('doctor_id')
        date_str = request.query_params.get('date')
        num_slots = request.query_params.get('num_slots', 8)
        
        if not doctor_id or not date_str:
            return Response(
                {'detail': 'doctor_id and date parameters are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            from datetime import datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            slots = AppointmentService.get_available_slots(doctor, date, int(num_slots))
            
            return Response({
                'doctor_id': doctor.id,
                'doctor_name': doctor.user.get_full_name(),
                'date': date,
                'available_slots': [slot.isoformat() for slot in slots],
                'total_slots_available': len(slots)
            }, status=status.HTTP_200_OK)
        except Doctor.DoesNotExist:
            return Response(
                {'detail': 'Doctor not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'detail': f'Invalid date format. Use YYYY-MM-DD. Error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def perform_create(self, serializer):
        """Enhanced validation for appointment creation"""
        from .appointment_service import AppointmentService, AppointmentValidationError
        
        patient_id = serializer.initial_data.get('patient')
        doctor_id = serializer.initial_data.get('doctor')
        
        # Permission check: Patient can only create appointment for themselves
        if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id)
                if not self.request.user.is_staff:
                    if patient.user != self.request.user:
                        raise PermissionDenied(
                            detail='Patients can only book appointments for themselves.'
                        )
            except Patient.DoesNotExist:
                raise ValidationError({'patient': 'Patient not found.'})
        
        # Validate doctor exists and perform business logic validation
        if doctor_id:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
            except Doctor.DoesNotExist:
                raise ValidationError({'doctor': 'Doctor not found.'})
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Enhanced validation for appointment updates"""
        from .appointment_service import AppointmentService, AppointmentValidationError
        
        appointment = serializer.instance
        
        # Cannot modify completed or cancelled appointments
        if appointment.status in ['COMPLETED', 'CANCELLED', 'NO_SHOW']:
            raise PermissionDenied(
                detail=f'Cannot modify appointments with status {appointment.status}.'
            )
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Prevent deletion of appointments - use cancel action instead"""
        raise PermissionDenied(
            detail='Direct deletion not allowed. Use the cancel endpoint to cancel appointments.'
        )


@api_view(['POST'])
def symptom_checker(request):
    """
    AI-Based Symptom Checker Endpoint
    
    This endpoint provides a DECISION-SUPPORT TOOL for initial symptom assessment.
    It is NOT a medical diagnosis system.
    
    Endpoint: POST /api/symptom-check/
    Authentication: Not required (public health screening)
    
    Request Body:
    {
        "symptoms": ["fever", "cough", "headache"]
    }
    
    Response:
    {
        "status": "success",
        "matched_conditions": ["viral_infection", "common_cold"],
        "risk_level": "LOW",
        "risk_score": 15,
        "advisory_message": "...",
        "unknown_symptoms": [],
        "confidence": "HIGH",
        "disclaimer": "..."
    }
    
    Error Response (400):
    {
        "status": "error",
        "error_code": "EMPTY_SYMPTOMS",
        "message": "No symptoms provided. Please report at least one symptom for evaluation.",
        "matched_conditions": [],
        "risk_level": null,
        "risk_score": 0
    }
    """
    
    # Allow public access (no authentication required for health screening)
    permission_classes = [AllowAny]
    
    if request.method == 'POST':
        # Get symptoms from request
        symptoms_data = request.data.get('symptoms', [])
        
        # Validate input type
        if not isinstance(symptoms_data, list):
            return Response({
                'status': 'error',
                'error_code': 'INVALID_INPUT_FORMAT',
                'message': 'Symptoms must be provided as a list. Example: {"symptoms": ["fever", "cough"]}',
                'matched_conditions': [],
                'risk_level': None,
                'risk_score': 0,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Evaluate symptoms using AI rule engine
        result = evaluate_symptoms(symptoms_data)
        
        # Determine HTTP status code based on result
        if result.get('status') == 'error':
            response_status = status.HTTP_400_BAD_REQUEST
        else:
            response_status = status.HTTP_200_OK
        
        return Response(result, status=response_status)
    
    else:
        # Only POST allowed
        return Response({
            'detail': 'Method not allowed. Use POST to submit symptoms.',
            'allowed_methods': ['POST']
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
