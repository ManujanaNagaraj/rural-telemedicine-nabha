"""
Notification Service Module

Handles notification creation and delivery for appointment and medicine events.
Designed for low-bandwidth rural environments with extensible architecture
for future SMS/Email gateway integration.
"""

from django.utils import timezone
from django.contrib.auth.models import User
from .models import Notification, NotificationPreference


class NotificationService:
    """
    Service class for notification management and delivery.
    
    Provides methods to:
    - Create notifications for various events
    - Filter based on user preferences
    - Check quiet hours
    - Support future SMS/Email delivery
    """
    
    @staticmethod
    def create_notification(
        user,
        title,
        message,
        notification_type='SYSTEM',
        appointment=None,
        medicine=None,
        pharmacy=None
    ):
        """
        Create a notification for a user.
        
        Args:
            user (User): User to receive the notification
            title (str): Short notification title
            message (str): Detailed notification message
            notification_type (str): Type (APPOINTMENT, MEDICINE, PHARMACY, SYSTEM)
            appointment (Appointment, optional): Associated appointment
            medicine (Medicine, optional): Associated medicine
            pharmacy (Pharmacy, optional): Associated pharmacy
            
        Returns:
            Notification: Created notification object
        """
        # Check user notification preferences
        try:
            prefs = user.notification_preferences
            if not prefs.is_notification_enabled(notification_type):
                return None  # User has disabled this notification type
        except NotificationPreference.DoesNotExist:
            # User hasn't set preferences, create default
            prefs = NotificationPreference.objects.create(user=user)
        
        # Create notification
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            appointment=appointment,
            medicine=medicine,
            pharmacy=pharmacy
        )
        
        return notification
    
    @staticmethod
    def notify_appointment_created(appointment):
        """
        Notify patient and doctor when appointment is created (PENDING state).
        
        Args:
            appointment (Appointment): The created appointment
        """
        # Notify patient
        NotificationService.create_notification(
            user=appointment.patient.user,
            title="Appointment Scheduled",
            message=f"Your appointment with Dr. {appointment.doctor.user.first_name} "
                    f"{appointment.doctor.user.last_name} has been scheduled for "
                    f"{appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}.",
            notification_type='APPOINTMENT',
            appointment=appointment
        )
        
        # Notify doctor
        NotificationService.create_notification(
            user=appointment.doctor.user,
            title="New Appointment Assigned",
            message=f"Patient {appointment.patient.user.first_name} {appointment.patient.user.last_name} "
                    f"has booked an appointment for {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}.",
            notification_type='APPOINTMENT',
            appointment=appointment
        )
    
    @staticmethod
    def notify_appointment_confirmed(appointment):
        """
        Notify patient when appointment is confirmed.
        
        Args:
            appointment (Appointment): The confirmed appointment
        """
        NotificationService.create_notification(
            user=appointment.patient.user,
            title="Appointment Confirmed",
            message=f"Your appointment with Dr. {appointment.doctor.user.first_name} "
                    f"{appointment.doctor.user.last_name} on "
                    f"{appointment.appointment_date.strftime('%Y-%m-%d %H:%M')} has been confirmed.",
            notification_type='APPOINTMENT',
            appointment=appointment
        )
    
    @staticmethod
    def notify_appointment_completed(appointment):
        """
        Notify patient when appointment is completed.
        
        Args:
            appointment (Appointment): The completed appointment
        """
        message = f"Your appointment with Dr. {appointment.doctor.user.first_name} " \
                  f"{appointment.doctor.user.last_name} on " \
                  f"{appointment.appointment_date.strftime('%Y-%m-%d %H:%M')} has been completed."
        
        if appointment.prescription:
            message += f"\n\nPrescription: {appointment.prescription}"
        
        NotificationService.create_notification(
            user=appointment.patient.user,
            title="Appointment Completed",
            message=message,
            notification_type='APPOINTMENT',
            appointment=appointment
        )
    
    @staticmethod
    def notify_appointment_cancelled(appointment, reason=""):
        """
        Notify patient and doctor when appointment is cancelled.
        
        Args:
            appointment (Appointment): The cancelled appointment
            reason (str, optional): Cancellation reason
        """
        cancel_reason = f" Reason: {reason}" if reason else ""
        
        # Notify patient
        NotificationService.create_notification(
            user=appointment.patient.user,
            title="Appointment Cancelled",
            message=f"Your appointment with Dr. {appointment.doctor.user.first_name} "
                    f"{appointment.doctor.user.last_name} on "
                    f"{appointment.appointment_date.strftime('%Y-%m-%d %H:%M')} has been cancelled.{cancel_reason}",
            notification_type='APPOINTMENT',
            appointment=appointment
        )
        
        # Notify doctor
        NotificationService.create_notification(
            user=appointment.doctor.user,
            title="Appointment Cancelled",
            message=f"The appointment with patient {appointment.patient.user.first_name} "
                    f"{appointment.patient.user.last_name} on "
                    f"{appointment.appointment_date.strftime('%Y-%m-%d %H:%M')} has been cancelled.{cancel_reason}",
            notification_type='APPOINTMENT',
            appointment=appointment
        )
    
    @staticmethod
    def notify_appointment_no_show(appointment):
        """
        Notify patient when appointment is marked as no-show.
        
        Args:
            appointment (Appointment): The no-show appointment
        """
        NotificationService.create_notification(
            user=appointment.patient.user,
            title="Appointment Marked as No-Show",
            message=f"Your appointment with Dr. {appointment.doctor.user.first_name} "
                    f"{appointment.doctor.user.last_name} on "
                    f"{appointment.appointment_date.strftime('%Y-%m-%d %H:%M')} was marked as no-show.",
            notification_type='APPOINTMENT',
            appointment=appointment
        )
    
    @staticmethod
    def notify_low_inventory(pharmacy, medicine, quantity, threshold):
        """
        Notify pharmacy/admin when medicine inventory falls below threshold.
        
        Args:
            pharmacy (Pharmacy): The pharmacy
            medicine (Medicine): The medicine with low stock
            quantity (int): Current quantity
            threshold (int): Threshold value
        """
        # Find pharmacy admins (users linked to pharmacy)
        # For now, notify system admins
        admin_users = User.objects.filter(is_staff=True)
        
        for admin in admin_users:
            NotificationService.create_notification(
                user=admin,
                title="Low Stock Alert",
                message=f"Medicine '{medicine.name}' at pharmacy '{pharmacy.name}' ({pharmacy.location}) "
                        f"has fallen below threshold. Current stock: {quantity} units (Threshold: {threshold} units).",
                notification_type='PHARMACY',
                pharmacy=pharmacy,
                medicine=medicine
            )
    
    @staticmethod
    def notify_inventory_restocked(pharmacy, medicine, new_quantity):
        """
        Notify relevant users when medicine is restocked.
        
        Args:
            pharmacy (Pharmacy): The pharmacy
            medicine (Medicine): The restocked medicine
            new_quantity (int): New quantity
        """
        # Notify admins about restock
        admin_users = User.objects.filter(is_staff=True)
        
        for admin in admin_users:
            NotificationService.create_notification(
                user=admin,
                title="Inventory Restocked",
                message=f"Medicine '{medicine.name}' at pharmacy '{pharmacy.name}' ({pharmacy.location}) "
                        f"has been restocked. New quantity: {new_quantity} units.",
                notification_type='PHARMACY',
                pharmacy=pharmacy,
                medicine=medicine
            )
    
    @staticmethod
    def get_user_unread_count(user):
        """Get count of unread notifications for a user."""
        return Notification.objects.filter(user=user, is_read=False).count()
    
    @staticmethod
    def get_user_notifications(
        user,
        notification_type=None,
        is_read=None,
        limit=50
    ):
        """
        Get notifications for a user with optional filtering.
        
        Args:
            user (User): The user
            notification_type (str, optional): Filter by type
            is_read (bool, optional): Filter by read status
            limit (int): Maximum notifications to return
            
        Returns:
            QuerySet: Filtered notifications
        """
        queryset = Notification.objects.filter(user=user).order_by('-created_at')
        
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read)
        
        return queryset[:limit]
    
    @staticmethod
    def is_in_quiet_hours(user):
        """
        Check if current time is within user's quiet hours.
        
        Args:
            user (User): The user
            
        Returns:
            bool: True if in quiet hours, False otherwise
        """
        try:
            prefs = user.notification_preferences
            if not prefs.quiet_hours_enabled:
                return False
            
            current_time = timezone.now().time()
            return (prefs.quiet_hours_start <= current_time <= prefs.quiet_hours_end)
        except NotificationPreference.DoesNotExist:
            return False
