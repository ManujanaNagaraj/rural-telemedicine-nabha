"""
Appointment Service Module

This module provides business logic for appointment management:
- Validation of appointments
- Conflict detection
- Doctor availability checking
- Appointment lifecycle management

This ensures all appointment operations are consistent and testable.
"""

from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Appointment, Doctor


class AppointmentValidationError(ValidationError):
    """Custom exception for appointment validation errors."""
    pass


class AppointmentService:
    """
    Service class for appointment business logic.
    
    Handles:
    - Double booking prevention
    - Patient overlapping appointment detection
    - Doctor availability validation
    - Appointment state transitions
    - Audit trail management
    """
    
    # Appointment slot duration (in minutes)
    SLOT_DURATION_MINUTES = 30
    
    @staticmethod
    def get_slot_duration():
        """Get appointment slot duration as timedelta."""
        return timedelta(minutes=AppointmentService.SLOT_DURATION_MINUTES)
    
    @staticmethod
    def validate_appointment_date(appointment_date):
        """
        Validate that appointment date is in the future.
        
        Args:
            appointment_date (datetime): Proposed appointment datetime
            
        Raises:
            AppointmentValidationError: If date is in the past
        """
        if appointment_date < timezone.now():
            raise AppointmentValidationError(
                "Appointment date cannot be in the past. "
                f"Current time: {timezone.now().isoformat()}"
            )
    
    @staticmethod
    def check_doctor_availability(doctor, appointment_date, exclude_appointment_id=None):
        """
        Check if doctor is available at the given time slot.
        
        Args:
            doctor (Doctor): The doctor to check
            appointment_date (datetime): Proposed appointment datetime
            exclude_appointment_id (int, optional): Appointment ID to exclude from check
            
        Returns:
            bool: True if doctor is available, False otherwise
            
        Raises:
            AppointmentValidationError: If doctor is not available or has conflicts
        """
        if not doctor.is_available:
            raise AppointmentValidationError(
                f"Dr. {doctor.user.first_name} {doctor.user.last_name} is currently not available for appointments."
            )
        
        slot_duration = AppointmentService.get_slot_duration()
        slot_start = appointment_date
        slot_end = appointment_date + slot_duration
        
        # Query for overlapping appointments with this doctor
        conflicting_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__lt=slot_end,
            appointment_date__gte=slot_start - slot_duration,
            status__in=['PENDING', 'CONFIRMED']  # Only active appointments conflict
        )
        
        # Exclude the current appointment if updating
        if exclude_appointment_id:
            conflicting_appointments = conflicting_appointments.exclude(id=exclude_appointment_id)
        
        if conflicting_appointments.exists():
            conflict = conflicting_appointments.first()
            raise AppointmentValidationError(
                f"Dr. {doctor.user.first_name} {doctor.user.last_name} is not available at this time. "
                f"Another appointment is already scheduled (ID: {conflict.id})."
            )
        
        return True
    
    @staticmethod
    def check_patient_overlapping_appointments(patient, appointment_date):
        """
        Check if patient has overlapping appointments.
        
        Args:
            patient (Patient): The patient to check
            appointment_date (datetime): Proposed appointment datetime
            
        Raises:
            AppointmentValidationError: If patient has overlapping appointments
        """
        slot_duration = AppointmentService.get_slot_duration()
        slot_start = appointment_date
        slot_end = appointment_date + slot_duration
        
        # Query for overlapping appointments for this patient
        overlapping_appointments = Appointment.objects.filter(
            patient=patient,
            appointment_date__lt=slot_end,
            appointment_date__gte=slot_start - slot_duration,
            status__in=['PENDING', 'CONFIRMED']  # Only active appointments overlap
        )
        
        if overlapping_appointments.exists():
            conflict = overlapping_appointments.first()
            raise AppointmentValidationError(
                f"Patient already has an appointment at this time (ID: {conflict.id}). "
                f"Cannot book overlapping appointments."
            )
    
    @staticmethod
    def validate_new_appointment(patient, doctor, appointment_date):
        """
        Comprehensive validation for new appointment creation.
        
        Args:
            patient (Patient): The patient
            doctor (Doctor): The doctor
            appointment_date (datetime): Proposed appointment datetime
            
        Raises:
            AppointmentValidationError: If any validation fails
        """
        # Validate date is in future
        AppointmentService.validate_appointment_date(appointment_date)
        
        # Check doctor availability
        AppointmentService.check_doctor_availability(doctor, appointment_date)
        
        # Check for patient conflicts
        AppointmentService.check_patient_overlapping_appointments(patient, appointment_date)
    
    @staticmethod
    def validate_appointment_update(appointment, appointment_date):
        """
        Validation for updating existing appointment date/time.
        
        Args:
            appointment (Appointment): The appointment being updated
            appointment_date (datetime): New proposed appointment datetime
            
        Raises:
            AppointmentValidationError: If any validation fails
        """
        # Validate date is in future
        AppointmentService.validate_appointment_date(appointment_date)
        
        # Check doctor availability (excluding current appointment)
        AppointmentService.check_doctor_availability(
            appointment.doctor,
            appointment_date,
            exclude_appointment_id=appointment.id
        )
        
        # Check for patient conflicts (excluding current appointment)
        slot_duration = AppointmentService.get_slot_duration()
        slot_start = appointment_date
        slot_end = appointment_date + slot_duration
        
        overlapping_appointments = Appointment.objects.filter(
            patient=appointment.patient,
            appointment_date__lt=slot_end,
            appointment_date__gte=slot_start - slot_duration,
            status__in=['PENDING', 'CONFIRMED']
        ).exclude(id=appointment.id)
        
        if overlapping_appointments.exists():
            conflict = overlapping_appointments.first()
            raise AppointmentValidationError(
                f"Patient already has an appointment at this time (ID: {conflict.id}). "
                f"Cannot book overlapping appointments."
            )
    
    @staticmethod
    def get_available_slots(doctor, date, num_slots=8):
        """
        Get available time slots for a doctor on a given date.
        
        Args:
            doctor (Doctor): The doctor
            date (date): The date to check
            num_slots (int): Number of slots to return
            
        Returns:
            list: List of available datetime slots for the doctor
        """
        if not doctor.is_available:
            return []
        
        available_slots = []
        slot_duration = AppointmentService.get_slot_duration()
        
        # Start from 9 AM on the given date
        current_time = timezone.make_aware(
            timezone.datetime.combine(date, timezone.datetime.min.time().replace(hour=9))
        )
        
        # Check until 5 PM (17:00)
        end_time = timezone.make_aware(
            timezone.datetime.combine(date, timezone.datetime.min.time().replace(hour=17))
        )
        
        while current_time <= end_time and len(available_slots) < num_slots:
            # Check if slot is available
            conflicting = Appointment.objects.filter(
                doctor=doctor,
                appointment_date__lt=current_time + slot_duration,
                appointment_date__gte=current_time,
                status__in=['PENDING', 'CONFIRMED']
            ).exists()
            
            if not conflicting:
                available_slots.append(current_time)
            
            current_time += slot_duration
        
        return available_slots
    
    @staticmethod
    def auto_assign_doctor(specialization=None):
        """
        Auto-assign a doctor based on availability and specialization.
        
        Args:
            specialization (str, optional): Preferred specialization
            
        Returns:
            Doctor: An available doctor, or None if none available
        """
        query = Doctor.objects.filter(is_available=True)
        
        if specialization:
            # Try to find a doctor with matching specialization
            query = query.filter(specialization=specialization)
        
        # Get the doctor with fewest appointments in next 7 days
        from django.db.models import Count
        query = query.annotate(
            appointment_count=Count('appointments', 
                filter=timezone.Q(
                    appointments__appointment_date__gte=timezone.now(),
                    appointments__appointment_date__lte=timezone.now() + timedelta(days=7),
                    appointments__status__in=['PENDING', 'CONFIRMED']
                )
            )
        ).order_by('appointment_count')
        
        return query.first()
    
    @staticmethod
    def get_appointment_timeline(appointment):
        """
        Get the timeline of an appointment from creation to completion/cancellation.
        
        Args:
            appointment (Appointment): The appointment
            
        Returns:
            dict: Timeline events with timestamps
        """
        timeline = {
            'created_at': appointment.created_at,
            'updated_at': appointment.updated_at,
            'confirmed_at': appointment.confirmed_at,
            'completed_at': appointment.completed_at,
            'cancelled_at': appointment.cancelled_at,
        }
        return {k: v for k, v in timeline.items() if v is not None}
