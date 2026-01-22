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


class Pharmacy(models.Model):
    """
    Pharmacy model for rural healthcare supply chain.
    
    Represents a pharmacy/chemist shop in the village/area.
    Can be offline or online, with local medicine inventory.
    """
    
    name = models.CharField(
        max_length=255,
        help_text="Name of the pharmacy"
    )
    location = models.CharField(
        max_length=255,
        help_text="Village name / area / region"
    )
    contact_number = models.CharField(
        max_length=15,
        help_text="Contact phone number"
    )
    address = models.TextField(
        help_text="Detailed address for rural location"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this pharmacy is currently operational"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.location})"
    
    def get_available_medicines(self):
        """Get all medicines available in this pharmacy (quantity > 0)."""
        return self.inventory.filter(quantity_available__gt=0)


class Medicine(models.Model):
    """
    Medicine/medication model for healthcare supply chain.
    
    Stores medicine information including name, description,
    and whether prescription is required.
    """
    
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Medicine name (e.g., Paracetamol, Aspirin)"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description, dosage info, uses"
    )
    is_prescription_required = models.BooleanField(
        default=False,
        help_text="Whether prescription is required to purchase"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_prescription_required']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_available_pharmacies(self):
        """Get all pharmacies that have this medicine in stock."""
        return Pharmacy.objects.filter(
            inventory__medicine=self,
            inventory__quantity_available__gt=0,
            is_active=True
        ).distinct()


class PharmacyInventory(models.Model):
    """
    Pharmacy inventory model for medicine availability tracking.
    
    Links pharmacy + medicine with quantity and last update timestamp.
    Designed for rural areas with low internet - can sync when online.
    """
    
    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        related_name='inventory',
        help_text="The pharmacy that stocks this medicine"
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='pharmacy_inventory',
        help_text="The medicine being stocked"
    )
    quantity_available = models.PositiveIntegerField(
        default=0,
        help_text="Current quantity available (units)"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="When the quantity was last updated"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['pharmacy', 'medicine']
        ordering = ['-last_updated']
        indexes = [
            models.Index(fields=['pharmacy', 'quantity_available']),
            models.Index(fields=['medicine', 'quantity_available']),
            models.Index(fields=['last_updated']),
        ]
    
    def __str__(self):
        return f"{self.medicine.name} @ {self.pharmacy.name}: {self.quantity_available} units"
    
    def clean(self):
        """Validate inventory data."""
        if self.quantity_available < 0:
            raise ValidationError("Quantity available cannot be negative.")
    
    def save(self, *args, **kwargs):
        """Ensure validation runs before saving."""
        self.clean()
        super().save(*args, **kwargs)
    
    def is_available(self):
        """Check if medicine is available at this pharmacy."""
        return self.quantity_available > 0
    
    def update_quantity(self, quantity, reason=""):
        """
        Update inventory quantity.
        
        Args:
            quantity (int): New quantity (must be >= 0)
            reason (str): Reason for update (optional)
            
        Raises:
            ValidationError: If quantity is negative
        """
        if quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        
        self.quantity_available = quantity
        self.save()
    
    def add_stock(self, quantity):
        """Add to existing stock."""
        if quantity < 0:
            raise ValidationError("Cannot add negative quantity.")
        self.quantity_available += quantity
        self.save()
    
    def remove_stock(self, quantity):
        """Remove from stock, ensuring quantity doesn't go negative."""
        if quantity < 0:
            raise ValidationError("Cannot remove negative quantity.")
        if self.quantity_available < quantity:
            raise ValidationError(
                f"Cannot remove {quantity} units. Only {self.quantity_available} available."
            )
        self.quantity_available -= quantity
        self.save()


class Notification(models.Model):
    """
    Notification model for healthcare alerts and reminders.
    
    Supports multiple notification types:
    - APPOINTMENT: Appointment-related notifications
    - MEDICINE: Medicine availability and alerts
    - SYSTEM: System-level notifications
    
    Designed for low-bandwidth rural environments.
    Text-only payloads suitable for SMS gateway integration.
    """
    
    # Notification types
    NOTIFICATION_TYPES = [
        ('APPOINTMENT', 'Appointment'),
        ('MEDICINE', 'Medicine'),
        ('PHARMACY', 'Pharmacy'),
        ('SYSTEM', 'System'),
    ]
    
    # Core fields
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who receives the notification (patient/doctor/admin)"
    )
    title = models.CharField(
        max_length=255,
        help_text="Notification title (short summary)"
    )
    message = models.TextField(
        help_text="Notification message (detailed content)"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='SYSTEM',
        help_text="Type of notification for filtering and routing"
    )
    
    # Status tracking
    is_read = models.BooleanField(
        default=False,
        help_text="Whether user has read this notification"
    )
    
    # Reference fields (for audit and relationship tracking)
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Associated appointment (if applicable)"
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Associated medicine (if applicable)"
    )
    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Associated pharmacy (if applicable)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True, help_text="When notification was marked as read")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def get_summary(self):
        """Get notification summary for low-bandwidth transmission."""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
        }


class NotificationPreference(models.Model):
    """
    User notification preferences for controlling alert delivery.
    
    Allows users to:
    - Enable/disable specific notification types
    - Choose delivery methods (in-app, SMS, etc.)
    - Set quiet hours for notifications
    """
    
    DELIVERY_METHODS = [
        ('IN_APP', 'In-app notification'),
        ('SMS', 'SMS (future)'),
        ('EMAIL', 'Email (future)'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Type preferences
    appointment_notifications = models.BooleanField(default=True)
    medicine_notifications = models.BooleanField(default=True)
    pharmacy_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    
    # Delivery preferences
    preferred_delivery = models.CharField(
        max_length=20,
        choices=DELIVERY_METHODS,
        default='IN_APP'
    )
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Start of quiet hours (HH:MM format)"
    )
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text="End of quiet hours (HH:MM format)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
    
    def is_notification_enabled(self, notification_type):
        """Check if notification type is enabled."""
        preference_map = {
            'APPOINTMENT': self.appointment_notifications,
            'MEDICINE': self.medicine_notifications,
            'PHARMACY': self.pharmacy_notifications,
            'SYSTEM': self.system_notifications,
        }
        return preference_map.get(notification_type, True)
