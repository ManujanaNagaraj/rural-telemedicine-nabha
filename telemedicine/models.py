from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    emergency_contact = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=15)
    experience_years = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} - {self.specialization}"

class Appointment(models.Model):
    """
    Enhanced Appointment model with production-ready lifecycle management.
    
    Status Flow: PENDING → CONFIRMED → COMPLETED
                          → CANCELLED (anytime)
    """
    
    # Status choices with clear lifecycle
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),           # Initial state - awaiting confirmation
        ('CONFIRMED', 'Confirmed'),       # Doctor confirmed the appointment
        ('COMPLETED', 'Completed'),       # Appointment completed
        ('CANCELLED', 'Cancelled'),       # Appointment cancelled
        ('NO_SHOW', 'No-show'),          # Patient did not show up
    ]
    
    # Core appointment data
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField(
        help_text="Date and time of the appointment. Cannot be in the past."
    )
    
    # Status management
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="Appointment status: PENDING→CONFIRMED→COMPLETED or CANCELLED"
    )
    
    # Medical information
    symptoms = models.TextField(blank=True, help_text="Patient-reported symptoms")
    diagnosis = models.TextField(blank=True, help_text="Doctor's diagnosis")
    prescription = models.TextField(blank=True, help_text="Prescribed treatment")
    notes = models.TextField(blank=True, help_text="General appointment notes")
    
    # Cancellation tracking
    cancelled_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reason for cancellation (if applicable)"
    )
    cancelled_by = models.CharField(
        max_length=20,
        choices=[('PATIENT', 'Patient'), ('DOCTOR', 'Doctor'), ('ADMIN', 'Admin')],
        blank=True,
        help_text="User type who cancelled the appointment"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text="When appointment was confirmed")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When appointment was completed")
    cancelled_at = models.DateTimeField(null=True, blank=True, help_text="When appointment was cancelled")
    
    class Meta:
        ordering = ['-appointment_date']
        indexes = [
            models.Index(fields=['patient', 'appointment_date']),
            models.Index(fields=['doctor', 'appointment_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Appointment: {self.patient} with {self.doctor} on {self.appointment_date} ({self.status})"
    
    def clean(self):
        """Validate appointment data."""
        # Cannot book in the past
        if self.appointment_date and self.appointment_date < timezone.now():
            raise ValidationError("Appointment date cannot be in the past.")
    
    def save(self, *args, **kwargs):
        """Ensure validation runs before saving."""
        self.clean()
        super().save(*args, **kwargs)
    
    def can_be_confirmed(self):
        """Check if appointment can transition to CONFIRMED."""
        return self.status == 'PENDING'
    
    def can_be_completed(self):
        """Check if appointment can transition to COMPLETED."""
        return self.status == 'CONFIRMED'
    
    def can_be_cancelled(self):
        """Check if appointment can be cancelled."""
        return self.status in ['PENDING', 'CONFIRMED']
    
    def confirm(self):
        """Confirm the appointment (PENDING → CONFIRMED)."""
        if not self.can_be_confirmed():
            raise ValidationError(f"Cannot confirm appointment with status '{self.status}'")
        self.status = 'CONFIRMED'
        self.confirmed_at = timezone.now()
        self.save()
    
    def complete(self):
        """Mark appointment as completed (CONFIRMED → COMPLETED)."""
        if not self.can_be_completed():
            raise ValidationError(f"Cannot complete appointment with status '{self.status}'")
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
    
    def cancel(self, reason='', cancelled_by='ADMIN'):
        """Cancel the appointment with reason tracking."""
        if not self.can_be_cancelled():
            raise ValidationError(f"Cannot cancel appointment with status '{self.status}'")
        self.status = 'CANCELLED'
        self.cancelled_reason = reason
        self.cancelled_by = cancelled_by
        self.cancelled_at = timezone.now()
        self.save()
    
    def mark_no_show(self):
        """Mark appointment as no-show (CONFIRMED → NO_SHOW)."""
        if self.status != 'CONFIRMED':
            raise ValidationError(f"Can only mark confirmed appointments as no-show")
        self.status = 'NO_SHOW'
        self.save()
