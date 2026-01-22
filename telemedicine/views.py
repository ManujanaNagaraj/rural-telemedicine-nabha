from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Patient, Doctor, Appointment, Pharmacy, Medicine, PharmacyInventory, Notification, NotificationPreference
from .serializers import (
    PatientSerializer, DoctorSerializer, AppointmentSerializer,
    MedicineSerializer, PharmacySerializer, PharmacyInventorySerializer,
    PharmacyInventoryUpdateSerializer, MedicineAvailabilitySerializer,
    NotificationSerializer, NotificationMarkReadSerializer, NotificationPreferenceSerializer
)
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
from .notification_service import NotificationService


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
            
            # Send notifications to patient and doctor
            notification_service = NotificationService()
            notification_service.notify_appointment_confirmed(appointment)
            
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
            
            # Send notifications to patient and doctor
            notification_service = NotificationService()
            notification_service.notify_appointment_completed(appointment)
            
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
            
            # Send notifications to patient and doctor
            notification_service = NotificationService()
            notification_service.notify_appointment_cancelled(appointment, reason)
            
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
            
            # Send notifications to patient and doctor
            notification_service = NotificationService()
            notification_service.notify_appointment_no_show(appointment)
            
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


class MedicineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Medicine model - read-only for all authenticated users.
    
    Provides:
    - GET /api/medicines/ - List all medicines
    - GET /api/medicines/{id}/ - Get medicine details
    """
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get all medicines, optionally filtered."""
        queryset = Medicine.objects.all()
        
        # Filter by prescription requirement if specified
        is_prescription = self.request.query_params.get('is_prescription_required')
        if is_prescription is not None:
            is_prescription = is_prescription.lower() == 'true'
            queryset = queryset.filter(is_prescription_required=is_prescription)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


class PharmacyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Pharmacy model - read-only access for all authenticated users.
    
    Provides:
    - GET /api/pharmacies/ - List all active pharmacies
    - GET /api/pharmacies/{id}/ - Get pharmacy details with inventory
    """
    queryset = Pharmacy.objects.filter(is_active=True)
    serializer_class = PharmacySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get all active pharmacies, optionally filtered."""
        queryset = Pharmacy.objects.filter(is_active=True)
        
        # Filter by location/area
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


class PharmacyInventoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Pharmacy Inventory management.
    
    Features:
    - GET /api/pharmacy-inventory/ - List inventory (filtered for active pharmacies, stock > 0)
    - GET /api/pharmacy-inventory/?medicine_id=X - Get availability of specific medicine
    - PATCH /api/pharmacy-inventory/{id}/update_quantity/ - Update inventory (pharmacy/admin only)
    
    Permissions:
    - Read: All authenticated users
    - Write: Pharmacy staff and admin only
    """
    serializer_class = PharmacyInventorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get inventory for active pharmacies with stock > 0."""
        queryset = PharmacyInventory.objects.filter(
            pharmacy__is_active=True,
            quantity_available__gt=0
        ).select_related('pharmacy', 'medicine')
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializer for update action."""
        if self.action == 'update_quantity':
            return PharmacyInventoryUpdateSerializer
        return PharmacyInventorySerializer
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_quantity(self, request, pk=None):
        """
        Update inventory quantity for a medicine at a pharmacy.
        
        Only pharmacy staff and admin can perform this action.
        
        Request Body:
        {
            "quantity": 50,
            "reason": "Restock from distributor"
        }
        """
        inventory = self.get_object()
        
        # Permission check: Only pharmacy staff or admin can update
        if not request.user.is_staff:
            # Check if user has pharmacy access (optional - can be extended)
            return Response(
                {'detail': 'Only admin and pharmacy staff can update inventory.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            quantity = serializer.validated_data['quantity']
            
            try:
                inventory.update_quantity(quantity)
                return Response(
                    {
                        'detail': 'Inventory updated successfully',
                        'medicine': inventory.medicine.name,
                        'pharmacy': inventory.pharmacy.name,
                        'new_quantity': inventory.quantity_available
                    },
                    status=status.HTTP_200_OK
                )
            except ValidationError as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def by_medicine(self, request):
        """
        Get all pharmacies with a specific medicine in stock.
        
        Query Parameters:
        - medicine_id: Required. The medicine ID
        
        Example: GET /api/pharmacy-inventory/by_medicine/?medicine_id=5
        """
        medicine_id = request.query_params.get('medicine_id')
        
        if not medicine_id:
            return Response(
                {'detail': 'medicine_id query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            medicine = Medicine.objects.get(id=medicine_id)
        except Medicine.DoesNotExist:
            return Response(
                {'detail': f'Medicine with ID {medicine_id} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all inventory items for this medicine with stock > 0
        inventory_items = PharmacyInventory.objects.filter(
            medicine=medicine,
            pharmacy__is_active=True,
            quantity_available__gt=0
        ).select_related('pharmacy', 'medicine')
        
        availability_data = {
            'medicine_id': medicine.id,
            'medicine_name': medicine.name,
            'is_prescription_required': medicine.is_prescription_required,
            'inventory_items': inventory_items
        }
        
        serializer = MedicineAvailabilitySerializer(availability_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def by_pharmacy(self, request):
        """
        Get all medicines available at a specific pharmacy.
        
        Query Parameters:
        - pharmacy_id: Required. The pharmacy ID
        
        Example: GET /api/pharmacy-inventory/by_pharmacy/?pharmacy_id=3
        """
        pharmacy_id = request.query_params.get('pharmacy_id')
        
        if not pharmacy_id:
            return Response(
                {'detail': 'pharmacy_id query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pharmacy = Pharmacy.objects.get(id=pharmacy_id, is_active=True)
        except Pharmacy.DoesNotExist:
            return Response(
                {'detail': f'Active pharmacy with ID {pharmacy_id} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all medicines at this pharmacy with stock > 0
        inventory_items = pharmacy.inventory.filter(quantity_available__gt=0)
        serializer = self.get_serializer(inventory_items, many=True)
        
        return Response({
            'pharmacy_id': pharmacy.id,
            'pharmacy_name': pharmacy.name,
            'pharmacy_location': pharmacy.location,
            'pharmacy_contact': pharmacy.contact_number,
            'medicines': serializer.data
        }, status=status.HTTP_200_OK)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Notification management - users can view and manage their own notifications.
    
    Features:
    - GET /api/notifications/ - List user's notifications
    - GET /api/notifications/{id}/ - Get specific notification
    - PATCH /api/notifications/{id}/mark_read/ - Mark notification as read
    - GET /api/notifications/unread_count/ - Get unread notification count
    - GET /api/notifications/?type=APPOINTMENT - Filter by type
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only current user's notifications."""
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        
        # Filter by notification type if specified
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by read status if specified
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            is_read = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """
        Mark notification as read.
        
        Request Body (optional):
        {
            "is_read": true
        }
        """
        notification = self.get_object()
        
        # Check permission: user can only mark their own notifications as read
        if notification.user != request.user:
            return Response(
                {'detail': 'You can only mark your own notifications as read.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = NotificationMarkReadSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            is_read = serializer.validated_data.get('is_read', True)
            
            if is_read:
                notification.mark_as_read()
            else:
                # Mark as unread
                notification.is_read = False
                notification.read_at = None
                notification.save()
            
            return Response(
                {
                    'detail': 'Notification marked as read.' if is_read else 'Notification marked as unread.',
                    'notification': NotificationSerializer(notification).data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications for current user."""
        user = request.user
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        
        return Response({
            'username': user.username,
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read for current user."""
        user = request.user
        unread_notifications = Notification.objects.filter(user=user, is_read=False)
        count = unread_notifications.count()
        
        for notification in unread_notifications:
            notification.mark_as_read()
        
        return Response({
            'detail': f'Marked {count} notifications as read.',
            'notifications_marked': count
        }, status=status.HTTP_200_OK)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Notification Preferences - users can manage their notification settings.
    
    Features:
    - GET /api/notification-preferences/my_preferences/ - Get user's preferences
    - PUT /api/notification-preferences/my_preferences/ - Update preferences
    """
    
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only current user's preference."""
        user = self.request.user
        return NotificationPreference.objects.filter(user=user)
    
    @action(detail=False, methods=['get', 'put'])
    def my_preferences(self, request):
        """
        Get or update current user's notification preferences.
        
        GET: Retrieve preferences
        PUT: Update preferences
        """
        user = request.user
        
        try:
            preference = NotificationPreference.objects.get(user=user)
        except NotificationPreference.DoesNotExist:
            # Create default preference if doesn't exist
            preference = NotificationPreference.objects.create(user=user)
        
        if request.method == 'GET':
            serializer = self.get_serializer(preference)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            serializer = self.get_serializer(preference, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
