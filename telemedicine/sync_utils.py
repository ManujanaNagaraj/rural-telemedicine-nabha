"""
Offline Sync utilities and conflict handling for rural healthcare.

This module provides:
1. Conflict detection and resolution strategies
2. Sync timestamp validation
3. Error handling for sync operations
4. Metadata management for incremental sync
"""

from datetime import datetime
from django.utils import timezone
from django.db import models
from rest_framework import status
from rest_framework.exceptions import ValidationError


class SyncConflictError(Exception):
    """
    Exception raised when sync conflict is detected.
    Server-authoritative conflicts are rejected.
    """
    def __init__(self, error_code, message, conflict_type=None, 
                 server_version=None, client_version=None, suggested_action=None):
        self.error_code = error_code
        self.message = message
        self.conflict_type = conflict_type or 'UNKNOWN'
        self.server_version = server_version
        self.client_version = client_version
        self.suggested_action = suggested_action or 'REFRESH'
        super().__init__(self.message)


class SyncValidator:
    """
    Validates sync requests and timestamps.
    Ensures data consistency for offline-first sync.
    """
    
    @staticmethod
    def validate_sync_timestamp(timestamp):
        """
        Validate that a sync timestamp is valid.
        
        Args:
            timestamp: ISO format datetime string or datetime object
            
        Returns:
            datetime object
            
        Raises:
            ValidationError: If timestamp is invalid or in the future
        """
        try:
            if isinstance(timestamp, str):
                # Parse ISO format timestamp
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            
            # Ensure it's timezone-aware
            if dt.tzinfo is None:
                dt = timezone.make_aware(dt)
            
            # Timestamp cannot be in the future
            if dt > timezone.now():
                raise ValidationError({
                    'last_sync_timestamp': 'Sync timestamp cannot be in the future.'
                })
            
            return dt
        except (ValueError, TypeError) as e:
            raise ValidationError({
                'last_sync_timestamp': f'Invalid timestamp format. Use ISO 8601 format. Error: {str(e)}'
            })
    
    @staticmethod
    def validate_update_request(instance, client_last_synced_at, current_user):
        """
        Validate update request for conflict detection.
        Implements server-authoritative conflict resolution.
        
        Args:
            instance: The model instance being updated
            client_last_synced_at: Client's last_synced_at timestamp
            current_user: The user making the update
            
        Raises:
            SyncConflictError: If a conflict is detected
        """
        # Get server-side last_synced_at
        server_last_synced_at = instance.last_synced_at
        
        # If record has been modified since client's last sync, it's a conflict
        if server_last_synced_at and client_last_synced_at:
            if client_last_synced_at < server_last_synced_at:
                raise SyncConflictError(
                    error_code='STALE_UPDATE',
                    message='Record has been modified since your last sync. Your changes may conflict.',
                    conflict_type='VERSION_MISMATCH',
                    server_version=server_last_synced_at,
                    client_version=client_last_synced_at,
                    suggested_action='REFRESH'
                )


class SyncMetadataManager:
    """
    Manages sync metadata for models.
    Tracks last_synced_at timestamps for incremental sync.
    """
    
    @staticmethod
    def mark_synced(instance, user=None):
        """
        Mark instance as synced by updating last_synced_at.
        
        Args:
            instance: Model instance to mark as synced
            user: User who triggered the sync (optional)
        """
        instance.last_synced_at = timezone.now()
        instance.save(update_fields=['last_synced_at'])
    
    @staticmethod
    def get_updated_records(model_class, since_timestamp, user=None, limit=100):
        """
        Get records updated since a given timestamp.
        Implements incremental sync support.
        
        Args:
            model_class: Django model class
            since_timestamp: Only return records updated after this time
            user: Filter by user (optional)
            limit: Maximum number of records to return
            
        Returns:
            QuerySet of updated records
        """
        queryset = model_class.objects.filter(updated_at__gt=since_timestamp)
        
        # Apply user filter if applicable and user is provided
        if user and hasattr(model_class, '_apply_user_filter'):
            queryset = model_class._apply_user_filter(queryset, user)
        
        return queryset.order_by('updated_at')[:limit]
    
    @staticmethod
    def get_sync_status(queryset, last_sync_timestamp):
        """
        Get sync status for a set of records.
        
        Args:
            queryset: QuerySet of records
            last_sync_timestamp: Last sync timestamp
            
        Returns:
            dict with sync status information
        """
        count = queryset.count()
        latest = queryset.latest('updated_at').updated_at if count > 0 else None
        
        return {
            'records_synced': count,
            'last_sync': last_sync_timestamp,
            'latest_update': latest,
            'status': 'success' if count > 0 else 'no_updates'
        }


class ConflictResolutionStrategy:
    """
    Implements server-authoritative conflict resolution.
    For rural healthcare, server is the source of truth.
    """
    
    STRATEGY = 'server-authoritative'
    
    @staticmethod
    def resolve_conflict(instance, update_data, client_last_synced_at):
        """
        Resolve conflict using server-authoritative strategy.
        
        Rules:
        1. Server data always wins
        2. Stale client updates are rejected
        3. Clear error messages guide clients to refresh
        
        Args:
            instance: Current server instance
            update_data: Data from client
            client_last_synced_at: When client last synced
            
        Returns:
            Resolved data dict or raises SyncConflictError
        """
        # Check if client is behind
        if instance.last_synced_at and client_last_synced_at:
            if client_last_synced_at < instance.last_synced_at:
                # Client is behind - reject update
                raise SyncConflictError(
                    error_code='STALE_UPDATE',
                    message='Your local changes are based on stale data. Please refresh and try again.',
                    conflict_type='UPDATE',
                    server_version=instance.last_synced_at,
                    client_version=client_last_synced_at,
                    suggested_action='REFRESH'
                )
        
        # No conflict - update data
        return update_data
    
    @staticmethod
    def get_resolution_message():
        """
        Get message explaining the conflict resolution strategy.
        """
        return {
            'strategy': 'Server-Authoritative',
            'description': 'Server data is the source of truth for rural healthcare.',
            'conflict_handling': 'Stale client updates are rejected to maintain data integrity.',
            'resolution': 'Clients must refresh when conflicts occur.'
        }
