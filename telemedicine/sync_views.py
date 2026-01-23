"""
Sync API views for offline-first capabilities.

Provides endpoints for incremental sync with conflict handling,
caching support, and rural-friendly optimization.
"""

from datetime import datetime
from django.utils import timezone
from django.views.decorators.http import condition
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import Patient, Doctor, Appointment, Pharmacy, Medicine, PharmacyInventory
from .sync_serializers import (
    PatientSyncSerializer, DoctorSyncSerializer, AppointmentSyncSerializer,
    PharmacySyncSerializer, MedicineSyncSerializer, PharmacyInventorySyncSerializer,
    SyncMetadataSerializer, SyncConflictErrorSerializer
)
from .sync_utils import (
    SyncValidator, SyncMetadataManager, ConflictResolutionStrategy,
    SyncConflictError
)
import hashlib


class SyncMixin:
    """
    Mixin providing sync capabilities to ViewSets.
    Adds incremental sync, ETag caching, and conflict handling.
    """
    
    def get_last_sync_timestamp(self):
        """
        Extract and validate last_sync_timestamp from query parameters.
        
        Returns:
            datetime object or None if not provided
        """
        last_sync_str = self.request.query_params.get('last_sync_timestamp')
        
        if not last_sync_str:
            return None
        
        try:
            return SyncValidator.validate_sync_timestamp(last_sync_str)
        except ValidationError as e:
            raise ValidationError(e.detail)
    
    def get_sync_queryset(self):
        """
        Filter queryset for incremental sync.
        Only returns records updated since last sync.
        
        Returns:
            Filtered queryset
        """
        queryset = self.get_queryset()
        last_sync = self.get_last_sync_timestamp()
        
        if last_sync:
            queryset = queryset.filter(updated_at__gt=last_sync)
        
        return queryset
    
    def add_sync_headers(self, response):
        """
        Add sync-related headers to response.
        
        Headers:
        - X-Last-Sync: Server's current time (for client to track)
        - X-Records-Synced: Number of records in response
        - X-Sync-Strategy: Conflict resolution strategy
        """
        response['X-Last-Sync'] = timezone.now().isoformat()
        response['X-Sync-Strategy'] = ConflictResolutionStrategy.STRATEGY
        
        if hasattr(response, 'data') and isinstance(response.data, list):
            response['X-Records-Synced'] = len(response.data)
        
        return response
    
    def generate_etag(self, data):
        """
        Generate ETag for response data.
        Used for conditional requests to reduce bandwidth.
        """
        if isinstance(data, (list, dict)):
            import json
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def handle_conditional_request(self, etag):
        """
        Handle If-None-Match header for conditional requests.
        Returns 304 Not Modified if ETag matches.
        """
        if_none_match = self.request.META.get('HTTP_IF_NONE_MATCH')
        
        if if_none_match and if_none_match == etag:
            return Response(status=status.HTTP_304_NOT_MODIFIED)
        
        return None


class PatientSyncViewSet(viewsets.ModelViewSet, SyncMixin):
    """
    Sync endpoint for Patient records.
    Supports incremental sync with conflict handling.
    
    Endpoints:
    - GET /api/patients/sync/ - Get updated patient records since last sync
    - GET /api/patients/sync/?last_sync_timestamp=2024-01-20T10:00:00Z
    """
    
    serializer_class = PatientSyncSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return patient records accessible by user."""
        user = self.request.user
        
        if user.is_staff:
            return Patient.objects.all()
        
        if hasattr(user, 'patient'):
            return Patient.objects.filter(user=user)
        
        # Doctors can see patients they have appointments with
        if hasattr(user, 'doctor'):
            from .models import Appointment
            patient_ids = Appointment.objects.filter(
                doctor__user=user
            ).values_list('patient_id', flat=True).distinct()
            return Patient.objects.filter(id__in=patient_ids)
        
        return Patient.objects.none()
    
    @action(detail=False, methods=['get'])
    def sync(self, request):
        """
        Get updated patient records for incremental sync.
        
        Query Parameters:
        - last_sync_timestamp: ISO format datetime (e.g., 2024-01-20T10:00:00Z)
        
        Response Headers:
        - X-Last-Sync: Current server timestamp
        - X-Records-Synced: Number of records returned
        - X-Sync-Strategy: Conflict resolution strategy
        - ETag: Hash of response data for conditional requests
        
        Example:
            GET /api/patients/sync/?last_sync_timestamp=2024-01-20T10:00:00Z
        """
        try:
            queryset = self.get_sync_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            # Generate ETag
            etag = self.generate_etag(serializer.data)
            
            # Check conditional request
            conditional_response = self.handle_conditional_request(etag)
            if conditional_response:
                return conditional_response
            
            # Create response
            response = Response(serializer.data, status=status.HTTP_200_OK)
            response = self.add_sync_headers(response)
            response['ETag'] = f'"{etag}"'
            
            return response
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class AppointmentSyncViewSet(viewsets.ModelViewSet, SyncMixin):
    """
    Sync endpoint for Appointment records.
    Supports incremental sync with conflict detection.
    
    Endpoints:
    - GET /api/appointments/sync/ - Get updated appointments since last sync
    - GET /api/appointments/sync/?last_sync_timestamp=2024-01-20T10:00:00Z
    """
    
    serializer_class = AppointmentSyncSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return appointments accessible by user."""
        user = self.request.user
        
        if user.is_staff:
            return Appointment.objects.all()
        
        if hasattr(user, 'patient'):
            return Appointment.objects.filter(patient__user=user)
        
        if hasattr(user, 'doctor'):
            return Appointment.objects.filter(doctor__user=user)
        
        return Appointment.objects.none()
    
    @action(detail=False, methods=['get'])
    def sync(self, request):
        """
        Get updated appointments for incremental sync.
        
        Query Parameters:
        - last_sync_timestamp: ISO format datetime
        
        Response includes:
        - Updated appointment records
        - Sync metadata (last_sync, records_synced)
        - Conflict resolution strategy
        
        Example:
            GET /api/appointments/sync/?last_sync_timestamp=2024-01-20T10:00:00Z
        """
        try:
            queryset = self.get_sync_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            etag = self.generate_etag(serializer.data)
            conditional_response = self.handle_conditional_request(etag)
            if conditional_response:
                return conditional_response
            
            response = Response(serializer.data, status=status.HTTP_200_OK)
            response = self.add_sync_headers(response)
            response['ETag'] = f'"{etag}"'
            
            return response
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put'])
    def sync_update(self, request, pk=None):
        """
        Update appointment with conflict detection.
        
        Checks for conflicts based on last_synced_at.
        Server-authoritative: Server data always wins.
        
        Body Parameters:
        - client_last_synced_at: When client last synced this record (ISO format)
        - ... (other appointment fields)
        
        Returns:
        - 200 OK: Update successful
        - 409 CONFLICT: Conflict detected, includes conflict details
        - 400 BAD_REQUEST: Invalid timestamp
        
        Example Body:
        {
            "client_last_synced_at": "2024-01-20T10:00:00Z",
            "status": "CONFIRMED",
            "diagnosis": "Updated diagnosis"
        }
        """
        appointment = self.get_object()
        
        try:
            # Get client's last sync timestamp
            client_last_synced = request.data.get('client_last_synced_at')
            
            if client_last_synced:
                client_last_synced = SyncValidator.validate_sync_timestamp(client_last_synced)
                
                # Check for conflicts
                SyncValidator.validate_update_request(
                    appointment,
                    client_last_synced,
                    request.user
                )
            
            # No conflict, proceed with update
            serializer = self.get_serializer(appointment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                
                # Mark as synced
                SyncMetadataManager.mark_synced(appointment, request.user)
                
                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK
                )
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except SyncConflictError as e:
            error_data = {
                'error_code': e.error_code,
                'message': e.message,
                'conflict_type': e.conflict_type,
                'server_version': e.server_version.isoformat() if e.server_version else None,
                'client_version': e.client_version.isoformat() if e.client_version else None,
                'suggested_action': e.suggested_action
            }
            return Response(error_data, status=status.HTTP_409_CONFLICT)
        
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class PharmacyInventorySyncViewSet(viewsets.ModelViewSet, SyncMixin):
    """
    Sync endpoint for Pharmacy Inventory records.
    Critical for rural medicine availability tracking.
    
    Supports incremental sync to minimize bandwidth usage.
    """
    
    serializer_class = PharmacyInventorySyncSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return all active pharmacy inventory."""
        return PharmacyInventory.objects.filter(pharmacy__is_active=True)
    
    @action(detail=False, methods=['get'])
    def sync(self, request):
        """
        Get updated pharmacy inventory for incremental sync.
        
        Query Parameters:
        - last_sync_timestamp: ISO format datetime
        - pharmacy_id: Optional filter by pharmacy
        
        Returns:
        - List of medicine availability records
        - Optimized for low-bandwidth transmission
        
        Example:
            GET /api/pharmacy-inventory/sync/?last_sync_timestamp=2024-01-20T10:00:00Z
            GET /api/pharmacy-inventory/sync/?pharmacy_id=5
        """
        try:
            queryset = self.get_sync_queryset()
            
            # Optional pharmacy filter
            pharmacy_id = request.query_params.get('pharmacy_id')
            if pharmacy_id:
                queryset = queryset.filter(pharmacy_id=pharmacy_id)
            
            serializer = self.get_serializer(queryset, many=True)
            
            etag = self.generate_etag(serializer.data)
            conditional_response = self.handle_conditional_request(etag)
            if conditional_response:
                return conditional_response
            
            response = Response(serializer.data, status=status.HTTP_200_OK)
            response = self.add_sync_headers(response)
            response['ETag'] = f'"{etag}"'
            
            return response
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def sync_status(request):
    """
    Get overall sync status and strategy information.
    
    Useful for clients to understand conflict resolution approach.
    
    Returns:
    - Server time
    - Supported sync parameters
    - Conflict resolution strategy
    
    Example:
        GET /api/sync/status/
    """
    strategy_info = ConflictResolutionStrategy.get_resolution_message()
    
    return Response({
        'server_time': timezone.now().isoformat(),
        'sync_strategy': strategy_info,
        'supported_parameters': {
            'last_sync_timestamp': 'ISO 8601 datetime (e.g., 2024-01-20T10:00:00Z)',
            'pharmacy_id': 'Optional pharmacy filter for inventory sync'
        },
        'sync_endpoints': {
            'patients': '/api/patients/sync/',
            'appointments': '/api/appointments/sync/',
            'pharmacy_inventory': '/api/pharmacy-inventory/sync/',
            'doctors': '/api/doctors/sync/'
        },
        'headers': {
            'X-Last-Sync': 'Server time for next sync',
            'X-Records-Synced': 'Number of records returned',
            'ETag': 'For conditional requests (If-None-Match)',
            'X-Sync-Strategy': 'Conflict resolution approach'
        },
        'conflict_handling': {
            'strategy': 'Server-Authoritative',
            'error_code': 'STALE_UPDATE',
            'http_status': 409,
            'suggested_action': 'REFRESH'
        }
    })
