from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

from .models import Patient, Doctor, Appointment
from .serializers import PatientSerializer, DoctorSerializer, AppointmentSerializer
from .permissions import (
    IsOwnPatientRecord, IsOwnDoctorRecord, IsAppointmentParticipant
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
    ViewSet for Patient management with authentication and permissions.
    - Patients can only access their own records
    - Doctors can view patients for their appointments
    - Admin has full access
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnPatientRecord]
    
    def get_queryset(self):
        """Filter queryset based on user type"""
        user = self.request.user
        
        # Admin can see all
        if user and user.is_staff:
            return Patient.objects.all()
        
        # Patients can only see their own record
        if user and hasattr(user, 'patient'):
            return Patient.objects.filter(user=user)
        
        # Doctors can see patients for their appointments
        if user and hasattr(user, 'doctor'):
            doctor = user.doctor
            patient_ids = Appointment.objects.filter(
                doctor=doctor
            ).values_list('patient_id', flat=True).distinct()
            return Patient.objects.filter(id__in=patient_ids)
        
        return Patient.objects.none()
    
    def perform_create(self, serializer):
        """Only allow creation of own patient record"""
        serializer.save()


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Doctor management with authentication and permissions.
    - Doctors can only access their own records
    - Patients can view doctors they have appointments with
    - Admin has full access
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnDoctorRecord]
    
    def get_queryset(self):
        """Filter queryset based on user type"""
        user = self.request.user
        
        # Admin can see all
        if user and user.is_staff:
            return Doctor.objects.all()
        
        # Doctors can only see their own record
        if user and hasattr(user, 'doctor'):
            return Doctor.objects.filter(user=user)
        
        # Patients can see doctors they have appointments with
        if user and hasattr(user, 'patient'):
            patient = user.patient
            doctor_ids = Appointment.objects.filter(
                patient=patient
            ).values_list('doctor_id', flat=True).distinct()
            return Doctor.objects.filter(id__in=doctor_ids)
        
        # Available doctors visible to all authenticated users
        return Doctor.objects.filter(is_available=True)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get list of available doctors"""
        doctors = Doctor.objects.filter(is_available=True)
        serializer = self.get_serializer(doctors, many=True)
        return Response(serializer.data)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Appointment management with role-based access.
    - Patients can only access their own appointments
    - Doctors can only access their assigned appointments
    - Admin has full access
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsAppointmentParticipant]
    
    def get_queryset(self):
        """Filter appointments based on user type"""
        user = self.request.user
        
        # Admin can see all
        if user and user.is_staff:
            return Appointment.objects.all()
        
        # Patients can only see their own appointments
        if user and hasattr(user, 'patient'):
            return Appointment.objects.filter(patient__user=user)
        
        # Doctors can only see their assigned appointments
        if user and hasattr(user, 'doctor'):
            return Appointment.objects.filter(doctor__user=user)
        
        return Appointment.objects.none()
    
    @action(detail=False, methods=['get'])
    def my_appointments(self, request):
        """Get current user's appointments"""
        appointments = self.get_queryset()
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update appointment status"""
        appointment = self.get_object()
        status_value = request.data.get('status')
        
        if status_value not in ['Scheduled', 'Completed', 'Cancelled', 'No-show']:
            return Response(
                {'detail': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = status_value
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
