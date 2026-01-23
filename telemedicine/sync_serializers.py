"""
Sync serializers for offline-first capabilities.

These serializers are optimized for sync operations:
- Minimal field selection to reduce bandwidth
- Include sync metadata (updated_at, last_synced_at)
- Suitable for low-bandwidth rural environments
"""

from rest_framework import serializers
from .models import Patient, Doctor, Appointment, Pharmacy, Medicine, PharmacyInventory


class PatientSyncSerializer(serializers.ModelSerializer):
    """
    Lightweight Patient serializer for sync operations.
    Includes only essential fields and sync metadata.
    """
    class Meta:
        model = Patient
        fields = [
            'id', 'phone_number', 'address', 'gender',
            'created_at', 'updated_at', 'last_synced_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_synced_at']


class DoctorSyncSerializer(serializers.ModelSerializer):
    """
    Lightweight Doctor serializer for sync operations.
    Includes only essential fields and sync metadata.
    """
    class Meta:
        model = Doctor
        fields = [
            'id', 'specialization', 'phone_number', 'is_available',
            'created_at', 'updated_at', 'last_synced_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_synced_at']


class AppointmentSyncSerializer(serializers.ModelSerializer):
    """
    Lightweight Appointment serializer for sync operations.
    Includes essential appointment info and sync metadata.
    """
    patient_id = serializers.IntegerField(source='patient.id', read_only=True)
    doctor_id = serializers.IntegerField(source='doctor.id', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient_id', 'doctor_id',
            'appointment_date', 'status',
            'symptoms', 'diagnosis', 'prescription',
            'created_at', 'updated_at', 'last_synced_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_synced_at']


class PharmacySyncSerializer(serializers.ModelSerializer):
    """
    Lightweight Pharmacy serializer for sync operations.
    Includes location and availability info.
    """
    class Meta:
        model = Pharmacy
        fields = [
            'id', 'name', 'location', 'contact_number',
            'is_active', 'created_at', 'updated_at', 'last_synced_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_synced_at']


class MedicineSyncSerializer(serializers.ModelSerializer):
    """
    Lightweight Medicine serializer for sync operations.
    Includes essential medicine info.
    """
    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'is_prescription_required',
            'created_at', 'updated_at', 'last_synced_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_synced_at']


class PharmacyInventorySyncSerializer(serializers.ModelSerializer):
    """
    Lightweight PharmacyInventory serializer for sync operations.
    Critical for medicine availability in rural areas.
    """
    pharmacy_id = serializers.IntegerField(source='pharmacy.id', read_only=True)
    medicine_id = serializers.IntegerField(source='medicine.id', read_only=True)
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    pharmacy_name = serializers.CharField(source='pharmacy.name', read_only=True)
    
    class Meta:
        model = PharmacyInventory
        fields = [
            'id', 'pharmacy_id', 'pharmacy_name',
            'medicine_id', 'medicine_name',
            'quantity_available',
            'created_at', 'last_updated', 'last_synced_at'
        ]
        read_only_fields = ['id', 'created_at', 'last_updated', 'last_synced_at']


class SyncMetadataSerializer(serializers.Serializer):
    """
    Serializer for sync metadata response.
    Returns sync status and next sync instructions.
    """
    last_sync = serializers.DateTimeField(help_text="Last successful sync timestamp")
    next_sync_recommended = serializers.DateTimeField(help_text="Recommended time for next sync")
    records_synced = serializers.IntegerField(help_text="Number of records synced")
    status = serializers.CharField(help_text="Sync status: success, partial, or error")
    message = serializers.CharField(allow_blank=True, help_text="Additional sync information")


class SyncConflictErrorSerializer(serializers.Serializer):
    """
    Serializer for sync conflict errors.
    Provides clear error information for conflict resolution.
    """
    error_code = serializers.CharField(help_text="Error code: STALE_UPDATE, CONFLICT, VALIDATION_ERROR")
    message = serializers.CharField(help_text="Detailed error message")
    conflict_type = serializers.CharField(help_text="Type of conflict: UPDATE, DELETE, VERSION_MISMATCH")
    server_version = serializers.DateTimeField(help_text="Server-side last_synced_at timestamp")
    client_version = serializers.DateTimeField(help_text="Client-side last_synced_at timestamp")
    suggested_action = serializers.CharField(help_text="Recommended action: REFRESH, RETRY, MANUAL_MERGE")
