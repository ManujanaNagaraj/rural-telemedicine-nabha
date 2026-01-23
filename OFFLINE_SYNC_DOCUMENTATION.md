# Rural Telemedicine Platform – Offline Sync & Caching Guide

## Executive Summary

This document describes the offline-first backend design for the **Nabha Rural Telemedicine Platform**. The system enables reliable data sync for healthcare workers in low-connectivity areas through incremental sync, conflict detection, and lightweight caching.

---

## 1. Architecture Overview

### Design Philosophy

- **Server-Authoritative**: The server is the source of truth for all data
- **Stateless Backend**: No session storage; each request is independent
- **Incremental Sync**: Only sync changed records to minimize bandwidth
- **Conflict Detection**: Detect and reject stale updates with clear guidance
- **Lightweight Caching**: ETag/Last-Modified headers for conditional requests

### Core Concepts

#### Sync Metadata
Every synced model includes three timestamps:
- **`created_at`**: When record was first created (immutable)
- **`updated_at`**: When record was last modified (updated on every change)
- **`last_synced_at`**: When record was last successfully synced by a client

#### Conflict Resolution Strategy
- **Rule**: Server data always wins; client must refresh if behind
- **Error Code**: `STALE_UPDATE` (HTTP 409 Conflict)
- **Client Action**: Request fresh data and retry

---

## 2. Sync Metadata Fields

### Added to All Models

```python
# In Patient, Doctor, Appointment, Pharmacy, Medicine, PharmacyInventory
created_at = models.DateTimeField(auto_now_add=True, db_index=True)
updated_at = models.DateTimeField(auto_now=True, db_index=True)
last_synced_at = models.DateTimeField(null=True, blank=True, db_index=True)
```

### Why Indexing?
- **`updated_at`**: Indexed for efficient incremental sync queries
- **`last_synced_at`**: Indexed for sync status tracking
- **`created_at`**: Indexed for sorting and audit queries

---

## 3. Incremental Sync APIs

### Endpoint: Get Updated Records

**Request:**
```
GET /api/patients/sync/?last_sync_timestamp=2024-01-20T10:00:00Z
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
| Parameter | Type | Required | Example |
|-----------|------|----------|---------|
| `last_sync_timestamp` | ISO 8601 datetime | No | `2024-01-20T10:00:00Z` |
| `pharmacy_id` | Integer | No (inventory only) | `5` |

**Response Headers:**
```
X-Last-Sync: 2024-01-21T14:30:45Z
X-Records-Synced: 3
X-Sync-Strategy: server-authoritative
ETag: "abc123def456"
```

**Response Body:**
```json
[
  {
    "id": 1,
    "phone_number": "+91-9876543210",
    "address": "Village, District, State",
    "gender": "Male",
    "created_at": "2024-01-10T08:00:00Z",
    "updated_at": "2024-01-20T14:15:30Z",
    "last_synced_at": null
  }
]
```

### Sync Endpoints

| Endpoint | Purpose | Bandwidth Optimized |
|----------|---------|-------------------|
| `GET /api/patients/sync/` | Get updated patient records | Yes (minimal fields) |
| `GET /api/appointments/sync/` | Get updated appointments | Yes |
| `GET /api/pharmacy-inventory/sync/` | Get medicine availability | Yes |
| `GET /api/sync/status/` | Get sync strategy & endpoints | Yes |

---

## 4. Conflict Handling Strategy

### Server-Authoritative Conflict Resolution

**Principle**: In rural healthcare, server data is the source of truth.

### Conflict Detection

```
Client's last_synced_at < Server's last_synced_at
→ CONFLICT DETECTED → Return 409 Conflict
```

### Example Conflict Scenario

**Sequence:**
1. Client syncs appointment at `2024-01-20T10:00:00Z`
2. Another user updates appointment on server at `2024-01-20T11:00:00Z`
3. Client tries to update with old timestamp → REJECTED

**Client Request:**
```json
PUT /api/appointments/1/sync_update/
{
  "client_last_synced_at": "2024-01-20T10:00:00Z",
  "status": "CONFIRMED"
}
```

**Server Response (409 Conflict):**
```json
{
  "error_code": "STALE_UPDATE",
  "message": "Record has been modified since your last sync. Your changes may conflict.",
  "conflict_type": "VERSION_MISMATCH",
  "server_version": "2024-01-20T11:00:00Z",
  "client_version": "2024-01-20T10:00:00Z",
  "suggested_action": "REFRESH"
}
```

### Client Resolution Steps

1. **Fetch Fresh Data**: `GET /api/appointments/1/`
2. **Merge Changes**: Manually apply client changes to fresh server data
3. **Retry Update**: Send new request with current `last_synced_at`

---

## 5. Lightweight Caching Support

### ETag Implementation

**Purpose**: Reduce bandwidth for unchanged data

#### Example Flow

**First Request:**
```
GET /api/appointments/sync/?last_sync_timestamp=2024-01-20T10:00:00Z
Response: [appointment data...]
ETag: "abc123xyz"
```

**Subsequent Request (with ETag):**
```
GET /api/appointments/sync/?last_sync_timestamp=2024-01-20T10:00:00Z
If-None-Match: "abc123xyz"
```

**Server Response (no change):**
```
HTTP 304 Not Modified
(No response body, saves bandwidth)
```

**Server Response (data changed):**
```
HTTP 200 OK
[updated appointment data...]
ETag: "def456uvw"
```

### Header Reference

| Header | Purpose | Example |
|--------|---------|---------|
| `ETag` | Response data hash | `"abc123xyz"` |
| `If-None-Match` | Check if ETag matches | `"abc123xyz"` |
| `Last-Modified` | Record modification time | `2024-01-20T14:30:45Z` |
| `If-Modified-Since` | Fetch if modified since | `2024-01-20T10:00:00Z` |

---

## 6. Validation & Error Handling

### Timestamp Validation

**Valid Format**: ISO 8601 with timezone
```
2024-01-20T10:00:00Z
2024-01-20T10:00:00+05:30
2024-01-20T10:00:00-00:00
```

**Invalid Requests**:
```
// Missing timezone
GET /api/patients/sync/?last_sync_timestamp=2024-01-20T10:00:00
Response: 400 Bad Request
{
  "last_sync_timestamp": "Invalid timestamp format. Use ISO 8601 format."
}

// Future timestamp
GET /api/patients/sync/?last_sync_timestamp=2099-01-20T10:00:00Z
Response: 400 Bad Request
{
  "last_sync_timestamp": "Sync timestamp cannot be in the future."
}
```

### Sync-Related Error Codes

| Error Code | HTTP Status | Meaning | Action |
|-----------|-----------|---------|--------|
| `STALE_UPDATE` | 409 | Record modified since last sync | REFRESH |
| `INVALID_TIMESTAMP` | 400 | Timestamp format invalid | Fix timestamp |
| `VALIDATION_ERROR` | 400 | Update data validation failed | Fix data |
| `UNAUTHORIZED` | 401 | Authentication required | Authenticate |
| `FORBIDDEN` | 403 | No access to record | Check permissions |

---

## 7. Sync Workflow for Offline-First Clients

### Initial Sync (First Time)

```
1. Client: GET /api/sync/status/
   → Learn sync strategy & endpoints

2. Client: GET /api/appointments/sync/
   → Download all appointments (no last_sync_timestamp)

3. Client: GET /api/pharmacy-inventory/sync/
   → Download medicine availability

4. Client: Store X-Last-Sync header value locally
   → Use as next sync timestamp
```

### Incremental Sync (After Going Online)

```
1. Client stored last sync time: 2024-01-20T10:00:00Z

2. Client goes offline, makes local changes

3. Client goes online, initiates sync:
   GET /api/appointments/sync/?last_sync_timestamp=2024-01-20T10:00:00Z
   → Get only updated appointments (since last sync)

4. If conflict detected (409):
   - GET /api/appointments/1/ (refresh)
   - PUT /api/appointments/1/sync_update/ (retry with fresh data)

5. Update local_sync_timestamp from X-Last-Sync header
```

### Conflict Resolution Workflow

```
┌─────────────┐
│ Client Update Request │
└────────┬────────┘
         │
         ↓
┌──────────────────┐
│ Check last_synced_at? │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ↓         ↓
  OLD      CURRENT
    │         │
    ↓         ↓
┌─────────┐ ┌──────────┐
│CONFLICT │ │ALLOWED   │
│409      │ │200/PUT   │
└─────────┘ └──────────┘
```

---

## 8. Implementation Details

### Sync Serializers (Minimal Fields)

**Purpose**: Reduce payload size for low-bandwidth areas

```python
# PatientSyncSerializer
fields = ['id', 'phone_number', 'address', 'gender', 
          'created_at', 'updated_at', 'last_synced_at']

# AppointmentSyncSerializer
fields = ['id', 'patient_id', 'doctor_id', 'appointment_date',
          'status', 'symptoms', 'diagnosis', 'prescription',
          'created_at', 'updated_at', 'last_synced_at']

# PharmacyInventorySyncSerializer
fields = ['id', 'pharmacy_id', 'medicine_id', 'quantity_available',
          'created_at', 'last_updated', 'last_synced_at']
```

### Conflict Handling Code

```python
# From sync_utils.py
from .sync_utils import SyncValidator, SyncConflictError

# Validate timestamp format
last_sync = SyncValidator.validate_sync_timestamp(timestamp_str)

# Check for conflicts on update
try:
    SyncValidator.validate_update_request(
        appointment,
        client_last_synced_at,
        request.user
    )
except SyncConflictError as e:
    # Return 409 with conflict details
    return Response(e.__dict__, status=status.HTTP_409_CONFLICT)
```

---

## 9. Sample API Requests & Responses

### Example 1: Initial Sync

**Request:**
```bash
curl -X GET "http://api.nabha.local/api/appointments/sync/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**Response:**
```json
[
  {
    "id": 101,
    "patient_id": 5,
    "doctor_id": 12,
    "appointment_date": "2024-01-25T14:00:00Z",
    "status": "PENDING",
    "symptoms": "Fever, headache",
    "diagnosis": null,
    "prescription": null,
    "created_at": "2024-01-15T09:30:00Z",
    "updated_at": "2024-01-15T09:30:00Z",
    "last_synced_at": null
  },
  {
    "id": 102,
    "patient_id": 5,
    "doctor_id": 13,
    "appointment_date": "2024-01-28T10:00:00Z",
    "status": "CONFIRMED",
    "symptoms": "Cough",
    "diagnosis": "Bronchitis",
    "prescription": "Amoxicillin 500mg",
    "created_at": "2024-01-10T14:15:00Z",
    "updated_at": "2024-01-20T11:45:00Z",
    "last_synced_at": null
  }
]
```

### Example 2: Incremental Sync (Changes Only)

**Request:**
```bash
curl -X GET "http://api.nabha.local/api/appointments/sync/?last_sync_timestamp=2024-01-15T09:30:00Z" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**Response:** (Only updated record)
```json
[
  {
    "id": 102,
    "patient_id": 5,
    "doctor_id": 13,
    "appointment_date": "2024-01-28T10:00:00Z",
    "status": "CONFIRMED",
    "symptoms": "Cough",
    "diagnosis": "Bronchitis (Updated)",
    "prescription": "Amoxicillin 500mg",
    "created_at": "2024-01-10T14:15:00Z",
    "updated_at": "2024-01-20T11:45:00Z",
    "last_synced_at": null
  }
]
```

### Example 3: Conditional Request with ETag

**First Request (Get ETag):**
```bash
curl -X GET "http://api.nabha.local/api/pharmacy-inventory/sync/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -i
```

**Response Headers:**
```
HTTP/1.1 200 OK
ETag: "7d8f4a2b9c1e3f5h"
X-Last-Sync: 2024-01-21T15:30:00Z
X-Records-Synced: 15
X-Sync-Strategy: server-authoritative
```

**Subsequent Request (with ETag):**
```bash
curl -X GET "http://api.nabha.local/api/pharmacy-inventory/sync/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "If-None-Match: \"7d8f4a2b9c1e3f5h\"" \
  -i
```

**Response (No Changes):**
```
HTTP/1.1 304 Not Modified
```

### Example 4: Conflict Resolution

**Client Update Request (Stale Data):**
```bash
curl -X PUT "http://api.nabha.local/api/appointments/102/sync_update/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "client_last_synced_at": "2024-01-15T09:30:00Z",
    "status": "COMPLETED",
    "diagnosis": "Bronchitis - Recovered"
  }'
```

**Response (409 Conflict):**
```json
{
  "error_code": "STALE_UPDATE",
  "message": "Record has been modified since your last sync. Your changes may conflict.",
  "conflict_type": "VERSION_MISMATCH",
  "server_version": "2024-01-20T11:45:00Z",
  "client_version": "2024-01-15T09:30:00Z",
  "suggested_action": "REFRESH"
}
```

**Client Resolution: Fetch Fresh Data**
```bash
curl -X GET "http://api.nabha.local/api/appointments/102/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**Fresh Data Response:**
```json
{
  "id": 102,
  "patient_id": 5,
  "doctor_id": 13,
  "appointment_date": "2024-01-28T10:00:00Z",
  "status": "CONFIRMED",
  "diagnosis": "Bronchitis (Updated)",
  "last_synced_at": "2024-01-20T11:45:00Z"
}
```

**Retry Update (with Fresh Timestamp):**
```bash
curl -X PUT "http://api.nabha.local/api/appointments/102/sync_update/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "client_last_synced_at": "2024-01-20T11:45:00Z",
    "diagnosis": "Bronchitis - Recovered"
  }'
```

**Success Response:**
```json
{
  "id": 102,
  "status": "CONFIRMED",
  "diagnosis": "Bronchitis - Recovered",
  "updated_at": "2024-01-21T16:00:00Z",
  "last_synced_at": "2024-01-21T16:00:00Z"
}
```

---

## 10. Benefits for Rural Healthcare

### Bandwidth Optimization
- **Incremental Sync**: Only download changed records (~80% reduction)
- **ETag Caching**: Skip downloads if data unchanged (~50% reduction)
- **Minimal Fields**: Only essential data in sync serializers (~40% reduction)
- **Combined**: Up to 95% bandwidth savings vs full sync

### Low-Connectivity Support
- **Offline-First**: Work offline, sync when connection available
- **Conflict Detection**: Clear error messages guide resolution
- **Server-Authoritative**: No complex merge logic needed
- **Retry-Friendly**: Simple "refresh and retry" workflow

### Data Integrity
- **Audit Trail**: created_at, updated_at, last_synced_at track history
- **Version Control**: Conflicts detected via last_synced_at
- **Server-Side Truth**: No need to sync deletes, reparenting
- **Clear Errors**: Specific error codes for different scenarios

---

## 11. Deployment Checklist

- [ ] Run database migrations: `python manage.py migrate`
- [ ] Create database indexes on timestamp fields
- [ ] Test sync endpoints with JWT authentication
- [ ] Configure CORS for mobile clients
- [ ] Set up monitoring for sync conflicts
- [ ] Document API in Swagger/OpenAPI
- [ ] Train team on conflict resolution workflow
- [ ] Load test sync endpoints under high volume

---

## 12. Future Enhancements

1. **Batch Operations**: Support batch updates for multiple records
2. **Selective Sync**: Let clients choose which fields to sync
3. **Delta Compression**: Send only changed fields, not full records
4. **Push Notifications**: Alert clients of critical changes
5. **Offline Queue**: Store failed syncs locally for retry
6. **Bandwidth Estimation**: Predict sync time before download

---

## Appendix: Quick Reference

### Sync Status Endpoint

**Request:**
```
GET /api/sync/status/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "server_time": "2024-01-21T16:30:00Z",
  "sync_strategy": {
    "strategy": "Server-Authoritative",
    "description": "Server data is the source of truth for rural healthcare.",
    "conflict_handling": "Stale client updates are rejected to maintain data integrity.",
    "resolution": "Clients must refresh when conflicts occur."
  },
  "sync_endpoints": {
    "patients": "/api/patients/sync/",
    "appointments": "/api/appointments/sync/",
    "pharmacy_inventory": "/api/pharmacy-inventory/sync/"
  }
}
```

---

**Document Version**: 1.0  
**Last Updated**: January 21, 2024  
**Author**: Backend Engineering Team  
**Project**: Nabha Rural Telemedicine Platform
