from rest_framework import serializers
from .models import Patient, Doctor, Appointment
from .appointment_service import AppointmentService, AppointmentValidationError


class PatientSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'date_of_birth', 'gender', 'phone_number', 'address', 'emergency_contact'
        ]
        read_only_fields = ['id', 'username', 'email', 'first_name', 'last_name']


class DoctorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = Doctor
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'specialization', 'license_number', 'phone_number', 
            'experience_years', 'is_available'
        ]
        read_only_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'license_number']


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Appointment model with enhanced validation and audit fields.
    
    Features:
    - Automatic validation of appointment dates and doctor availability
    - Nested patient and doctor information
    - Clear error messages for invalid state transitions
    - Comprehensive audit trail fields
    """
    
    # Nested read-only fields for better API responses
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    doctor_specialization = serializers.CharField(source='doctor.specialization', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient', 'patient_name',
            'doctor', 'doctor_name', 'doctor_specialization',
            'appointment_date',
            'status',
            'symptoms', 'diagnosis', 'prescription', 'notes',
            'cancelled_reason', 'cancelled_by',
            'created_at', 'updated_at',
            'confirmed_at', 'completed_at', 'cancelled_at'
        ]
        read_only_fields = [
            'id', 'patient_name', 'doctor_name', 'doctor_specialization',
            'cancelled_reason', 'cancelled_by',
            'created_at', 'updated_at',
            'confirmed_at', 'completed_at', 'cancelled_at'
        ]
    
    def validate_appointment_date(self, value):
        """Validate appointment date is in the future."""
        try:
            AppointmentService.validate_appointment_date(value)
        except AppointmentValidationError as e:
            raise serializers.ValidationError(str(e))
        return value
    
    def validate(self, data):
        """
        Comprehensive validation for appointment creation/update.
        
        Checks:
        - Doctor availability
        - Patient overlapping appointments
        - Date/time validity
        """
        if self.instance:
            # Update scenario
            appointment = self.instance
            appointment_date = data.get('appointment_date', appointment.appointment_date)
            doctor = data.get('doctor', appointment.doctor)
            
            if appointment_date != appointment.appointment_date:
                try:
                    AppointmentService.validate_appointment_update(appointment, appointment_date)
                except AppointmentValidationError as e:
                    raise serializers.ValidationError({'appointment_date': str(e)})
        else:
            # Create scenario
            patient = data.get('patient')
            doctor = data.get('doctor')
            appointment_date = data.get('appointment_date')
            
            if patient and doctor and appointment_date:
                try:
                    AppointmentService.validate_new_appointment(patient, doctor, appointment_date)
                except AppointmentValidationError as e:
                    raise serializers.ValidationError(str(e))
        
        return data


class AppointmentStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for appointment status updates.
    
    Handles state transitions with validation:
    - PENDING → CONFIRMED
    - CONFIRMED → COMPLETED
    - Any state → CANCELLED (with reason)
    """
    
    status = serializers.ChoiceField(choices=['CONFIRMED', 'COMPLETED', 'CANCELLED', 'NO_SHOW'])
    cancelled_reason = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Required when status is CANCELLED"
    )
    cancelled_by = serializers.ChoiceField(
        choices=['PATIENT', 'DOCTOR', 'ADMIN'],
        required=False,
        help_text="Required when status is CANCELLED"
    )
    
    def validate(self, data):
        """Validate status transition."""
        status = data.get('status')
        
        if status == 'CANCELLED':
            if not data.get('cancelled_reason'):
                raise serializers.ValidationError(
                    {'cancelled_reason': 'Reason is required when cancelling an appointment.'}
                )
            if not data.get('cancelled_by'):
                raise serializers.ValidationError(
                    {'cancelled_by': 'Cancelled_by is required when cancelling an appointment.'}
                )
        
        return data


class AppointmentAvailableSlotsSerializer(serializers.Serializer):
    """Serializer for requesting available appointment slots."""
    doctor_id = serializers.IntegerField(required=False)
    specialization = serializers.CharField(max_length=100, required=False)
    date = serializers.DateField()
    num_slots = serializers.IntegerField(default=8, min_value=1, max_value=20)
    
    def validate(self, data):
        """Ensure either doctor_id or specialization is provided."""
        if not data.get('doctor_id') and not data.get('specialization'):
            raise serializers.ValidationError(
                "Either doctor_id or specialization must be provided."
            )
        return data