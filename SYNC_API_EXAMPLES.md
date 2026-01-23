# SYNC API - Sample Requests & Responses

## Full Working Examples for Offline-First Sync

This document provides complete, copy-paste ready examples for all sync operations.

---

## 1. Sync Status Endpoint

### 1.1 Get Overall Sync Information

**Request:**
```bash
curl -X GET "http://localhost:8000/api/sync/status/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
{
  "server_time": "2024-01-21T16:45:30.123456Z",
  "sync_strategy": {
    "strategy": "Server-Authoritative",
    "description": "Server data is the source of truth for rural healthcare.",
    "conflict_handling": "Stale client updates are rejected to maintain data integrity.",
    "resolution": "Clients must refresh when conflicts occur."
  },
  "supported_parameters": {
    "last_sync_timestamp": "ISO 8601 datetime (e.g., 2024-01-20T10:00:00Z)",
    "pharmacy_id": "Optional pharmacy filter for inventory sync"
  },
  "sync_endpoints": {
    "patients": "/api/patients/sync/",
    "appointments": "/api/appointments/sync/",
    "pharmacy_inventory": "/api/pharmacy-inventory/sync/",
    "doctors": "/api/doctors/sync/"
  },
  "headers": {
    "X-Last-Sync": "Server time for next sync",
    "X-Records-Synced": "Number of records returned",
    "ETag": "For conditional requests (If-None-Match)",
    "X-Sync-Strategy": "Conflict resolution approach"
  },
  "conflict_handling": {
    "strategy": "Server-Authoritative",
    "error_code": "STALE_UPDATE",
    "http_status": 409,
    "suggested_action": "REFRESH"
  }
}
```

---

## 2. Patient Sync Examples

### 2.1 Initial Patient Sync (Full Download)

**Use Case**: First-time patient sync, no previous data

**Request:**
```bash
curl -X GET "http://localhost:8000/api/patients/sync/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -v
```

**Response Headers:**
```
HTTP/1.1 200 OK
Date: Sun, 21 Jan 2024 16:45:30 GMT
Content-Type: application/json
X-Last-Sync: 2024-01-21T16:45:30Z
X-Records-Synced: 2
X-Sync-Strategy: server-authoritative
ETag: "a1b2c3d4e5f6g7h8"
Content-Length: 1250
```

**Response Body:**
```json
[
  {
    "id": 1,
    "phone_number": "+91-9876543210",
    "address": "Village Gram, Taluka Taluka, District Sangli, State Maharashtra 415001",
    "gender": "Male",
    "created_at": "2024-01-10T08:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z",
    "last_synced_at": null
  },
  {
    "id": 2,
    "phone_number": "+91-9123456789",
    "address": "Village Warna, Taluka Taluka, District Satara, State Maharashtra 415402",
    "gender": "Female",
    "created_at": "2024-01-12T10:15:00Z",
    "updated_at": "2024-01-18T11:20:00Z",
    "last_synced_at": null
  }
]
```

### 2.2 Incremental Patient Sync

**Use Case**: Get only changed patient records since last sync

**Request:**
```bash
curl -X GET "http://localhost:8000/api/patients/sync/?last_sync_timestamp=2024-01-15T14:30:00Z" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -v
```

**Response:**
```json
[
  {
    "id": 2,
    "phone_number": "+91-9123456789",
    "address": "Village Warna, Taluka Taluka, District Satara, State Maharashtra 415402",
    "gender": "Female",
    "created_at": "2024-01-12T10:15:00Z",
    "updated_at": "2024-01-18T11:20:00Z",
    "last_synced_at": null
  }
]
```

### 2.3 Conditional Patient Sync (With ETag)

**Use Case**: Skip download if data hasn't changed

**First Request:**
```bash
curl -X GET "http://localhost:8000/api/patients/sync/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -v
```

**Response:**
```
HTTP/1.1 200 OK
ETag: "x9y8z7w6v5u4t3s2"
X-Last-Sync: 2024-01-21T16:45:30Z

[patient data...]
```

**Subsequent Request (With If-None-Match):**
```bash
curl -X GET "http://localhost:8000/api/patients/sync/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "If-None-Match: \"x9y8z7w6v5u4t3s2\"" \
  -v
```

**Response (Data Unchanged):**
```
HTTP/1.1 304 Not Modified

(No body - saves bandwidth)
```

---

## 3. Appointment Sync Examples

### 3.1 Full Appointment Sync

**Use Case**: Download all appointments on initial sync

**Request:**
```bash
curl -X GET "http://localhost:8000/api/appointments/sync/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Accept: application/json"
```

**Response:**
```json
[
  {
    "id": 101,
    "patient_id": 1,
    "doctor_id": 10,
    "appointment_date": "2024-01-25T14:00:00Z",
    "status": "PENDING",
    "symptoms": "Fever, body pain, weakness for 3 days",
    "diagnosis": null,
    "prescription": null,
    "created_at": "2024-01-20T09:30:00Z",
    "updated_at": "2024-01-20T09:30:00Z",
    "last_synced_at": null
  },
  {
    "id": 102,
    "patient_id": 1,
    "doctor_id": 11,
    "appointment_date": "2024-01-22T10:30:00Z",
    "status": "CONFIRMED",
    "symptoms": "Persistent cough, difficulty breathing",
    "diagnosis": "Mild pneumonia, viral infection",
    "prescription": "Amoxicillin 500mg 3x daily, Cough syrup",
    "created_at": "2024-01-10T15:45:00Z",
    "updated_at": "2024-01-18T13:20:00Z",
    "last_synced_at": null
  },
  {
    "id": 103,
    "patient_id": 2,
    "doctor_id": 12,
    "appointment_date": "2024-01-28T15:00:00Z",
    "status": "COMPLETED",
    "symptoms": "Dizziness, high BP reading",
    "diagnosis": "Hypertension, need monitoring",
    "prescription": "Amlodipine 5mg once daily",
    "created_at": "2024-01-05T11:00:00Z",
    "updated_at": "2024-01-19T16:15:00Z",
    "last_synced_at": null
  }
]
```

### 3.2 Incremental Appointment Sync

**Use Case**: Only get appointments changed since last sync

**Request:**
```bash
curl -X GET "http://localhost:8000/api/appointments/sync/?last_sync_timestamp=2024-01-18T13:20:00Z" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
[
  {
    "id": 103,
    "patient_id": 2,
    "doctor_id": 12,
    "appointment_date": "2024-01-28T15:00:00Z",
    "status": "COMPLETED",
    "symptoms": "Dizziness, high BP reading",
    "diagnosis": "Hypertension, need monitoring",
    "prescription": "Amlodipine 5mg once daily",
    "created_at": "2024-01-05T11:00:00Z",
    "updated_at": "2024-01-19T16:15:00Z",
    "last_synced_at": null
  }
]
```

### 3.3 Update Appointment (Success Case)

**Use Case**: Update appointment with current data (no conflict)

**Request:**
```bash
curl -X PUT "http://localhost:8000/api/appointments/101/sync_update/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "client_last_synced_at": "2024-01-20T09:30:00Z",
    "status": "CONFIRMED",
    "diagnosis": "Common cold with mild fever",
    "prescription": "Rest, fluids, Paracetamol 500mg"
  }'
```

**Response (200 Success):**
```json
{
  "id": 101,
  "patient_id": 1,
  "doctor_id": 10,
  "appointment_date": "2024-01-25T14:00:00Z",
  "status": "CONFIRMED",
  "symptoms": "Fever, body pain, weakness for 3 days",
  "diagnosis": "Common cold with mild fever",
  "prescription": "Rest, fluids, Paracetamol 500mg",
  "created_at": "2024-01-20T09:30:00Z",
  "updated_at": "2024-01-21T16:50:15Z",
  "last_synced_at": "2024-01-21T16:50:15Z"
}
```

### 3.4 Update Appointment (Conflict Case)

**Use Case**: Client tries to update with stale timestamp

**Request:**
```bash
curl -X PUT "http://localhost:8000/api/appointments/102/sync_update/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "client_last_synced_at": "2024-01-10T15:45:00Z",
    "status": "COMPLETED",
    "prescription": "Different prescription"
  }'
```

**Response (409 Conflict):**
```json
{
  "error_code": "STALE_UPDATE",
  "message": "Record has been modified since your last sync. Your changes may conflict.",
  "conflict_type": "VERSION_MISMATCH",
  "server_version": "2024-01-18T13:20:00Z",
  "client_version": "2024-01-10T15:45:00Z",
  "suggested_action": "REFRESH"
}
```

---

## 4. Pharmacy Inventory Sync Examples

### 4.1 Full Inventory Sync

**Use Case**: Download all medicine availability data

**Request:**
```bash
curl -X GET "http://localhost:8000/api/pharmacy-inventory/sync/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Accept: application/json"
```

**Response:**
```json
[
  {
    "id": 1,
    "pharmacy_id": 5,
    "pharmacy_name": "Gram Medical Store, Warna",
    "medicine_id": 15,
    "medicine_name": "Paracetamol 500mg",
    "quantity_available": 250,
    "created_at": "2024-01-15T08:00:00Z",
    "last_updated": "2024-01-20T14:30:00Z",
    "last_synced_at": null
  },
  {
    "id": 2,
    "pharmacy_id": 5,
    "pharmacy_name": "Gram Medical Store, Warna",
    "medicine_id": 18,
    "medicine_name": "Amoxicillin 500mg",
    "quantity_available": 120,
    "created_at": "2024-01-15T08:00:00Z",
    "last_updated": "2024-01-19T16:20:00Z",
    "last_synced_at": null
  },
  {
    "id": 3,
    "pharmacy_id": 6,
    "pharmacy_name": "Village Care Pharmacy, Gram",
    "medicine_id": 15,
    "medicine_name": "Paracetamol 500mg",
    "quantity_available": 0,
    "created_at": "2024-01-16T09:00:00Z",
    "last_updated": "2024-01-21T10:15:00Z",
    "last_synced_at": null
  },
  {
    "id": 4,
    "pharmacy_id": 6,
    "pharmacy_name": "Village Care Pharmacy, Gram",
    "medicine_id": 22,
    "medicine_name": "Amlodipine 5mg",
    "quantity_available": 85,
    "created_at": "2024-01-16T09:00:00Z",
    "last_updated": "2024-01-18T12:45:00Z",
    "last_synced_at": null
  }
]
```

### 4.2 Incremental Inventory Sync

**Use Case**: Get only inventory updates since last sync

**Request:**
```bash
curl -X GET "http://localhost:8000/api/pharmacy-inventory/sync/?last_sync_timestamp=2024-01-19T16:20:00Z" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
[
  {
    "id": 3,
    "pharmacy_id": 6,
    "pharmacy_name": "Village Care Pharmacy, Gram",
    "medicine_id": 15,
    "medicine_name": "Paracetamol 500mg",
    "quantity_available": 0,
    "created_at": "2024-01-16T09:00:00Z",
    "last_updated": "2024-01-21T10:15:00Z",
    "last_synced_at": null
  }
]
```

### 4.3 Inventory Sync for Specific Pharmacy

**Use Case**: Get inventory for one pharmacy only

**Request:**
```bash
curl -X GET "http://localhost:8000/api/pharmacy-inventory/sync/?pharmacy_id=5" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response:**
```json
[
  {
    "id": 1,
    "pharmacy_id": 5,
    "pharmacy_name": "Gram Medical Store, Warna",
    "medicine_id": 15,
    "medicine_name": "Paracetamol 500mg",
    "quantity_available": 250,
    "created_at": "2024-01-15T08:00:00Z",
    "last_updated": "2024-01-20T14:30:00Z",
    "last_synced_at": null
  },
  {
    "id": 2,
    "pharmacy_id": 5,
    "pharmacy_name": "Gram Medical Store, Warna",
    "medicine_id": 18,
    "medicine_name": "Amoxicillin 500mg",
    "quantity_available": 120,
    "created_at": "2024-01-15T08:00:00Z",
    "last_updated": "2024-01-19T16:20:00Z",
    "last_synced_at": null
  }
]
```

---

## 5. Error Response Examples

### 5.1 Invalid Timestamp Format

**Request:**
```bash
curl -X GET "http://localhost:8000/api/appointments/sync/?last_sync_timestamp=2024-01-20" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response (400 Bad Request):**
```json
{
  "last_sync_timestamp": "Invalid timestamp format. Use ISO 8601 format. Error: time data '2024-01-20' does not match format '%Y-%m-%d'"
}
```

### 5.2 Future Timestamp

**Request:**
```bash
curl -X GET "http://localhost:8000/api/patients/sync/?last_sync_timestamp=2099-01-20T10:00:00Z" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Response (400 Bad Request):**
```json
{
  "last_sync_timestamp": "Sync timestamp cannot be in the future."
}
```

### 5.3 Unauthorized Access

**Request (No Token):**
```bash
curl -X GET "http://localhost:8000/api/appointments/sync/"
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 5.4 Invalid Token

**Request (Expired/Invalid Token):**
```bash
curl -X GET "http://localhost:8000/api/appointments/sync/" \
  -H "Authorization: Bearer invalid.token.here"
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Given token not valid for any token type"
}
```

---

## 6. Complete Client Sync Workflow Example

### Scenario: Mobile Worker in Rural Area

#### Phase 1: Initial Sync (Online)

```bash
# 1. Get sync status and learn about the system
curl -X GET "http://api.nabha.local/api/sync/status/" \
  -H "Authorization: Bearer <token>"

# 2. Download all patient data
curl -X GET "http://api.nabha.local/api/patients/sync/" \
  -H "Authorization: Bearer <token>" \
  > patient_sync.json
# Save X-Last-Sync header: 2024-01-21T16:45:30Z

# 3. Download all appointments
curl -X GET "http://api.nabha.local/api/appointments/sync/" \
  -H "Authorization: Bearer <token>" \
  > appointment_sync.json
# Save X-Last-Sync header: 2024-01-21T16:45:30Z

# 4. Download medicine availability
curl -X GET "http://api.nabha.local/api/pharmacy-inventory/sync/" \
  -H "Authorization: Bearer <token>" \
  > inventory_sync.json
# Save X-Last-Sync header: 2024-01-21T16:45:30Z

# Device goes OFFLINE
# Worker makes local changes to appointment 102
```

#### Phase 2: Offline Work

```
Worker updates appointment 102 locally:
- Status: CONFIRMED
- Diagnosis: "Pneumonia, mild case"
```

#### Phase 3: Reconnect (Online Again)

```bash
# 1. Try to upload changes with client's old timestamp
curl -X PUT "http://api.nabha.local/api/appointments/102/sync_update/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "client_last_synced_at": "2024-01-21T16:45:30Z",
    "status": "CONFIRMED",
    "diagnosis": "Pneumonia, mild case"
  }'

# SUCCESS (200 OK) - No conflict
# Response includes: last_synced_at: "2024-01-21T17:15:45Z"
```

#### Phase 4: Next Sync Cycle

```bash
# 1. Check for updates since last sync
curl -X GET "http://api.nabha.local/api/appointments/sync/?last_sync_timestamp=2024-01-21T17:15:45Z" \
  -H "Authorization: Bearer <token>"

# 2. Check inventory updates
curl -X GET "http://api.nabha.local/api/pharmacy-inventory/sync/?last_sync_timestamp=2024-01-21T17:15:45Z" \
  -H "Authorization: Bearer <token>"

# 3. Use ETag for conditional request to save bandwidth
curl -X GET "http://api.nabha.local/api/patients/sync/" \
  -H "Authorization: Bearer <token>" \
  -H "If-None-Match: \"x9y8z7w6v5u4t3s2\""

# Response: 304 Not Modified (data unchanged)
```

---

## 7. Sync Response Headers Quick Reference

Every sync response includes these helpful headers:

| Header | Example Value | Meaning |
|--------|--------------|---------|
| `X-Last-Sync` | `2024-01-21T16:45:30Z` | When server processed this sync |
| `X-Records-Synced` | `15` | Number of records in response |
| `X-Sync-Strategy` | `server-authoritative` | Conflict resolution approach |
| `ETag` | `"a1b2c3d4e5f6"` | Data hash for conditional requests |
| `Cache-Control` | `private, no-cache` | Browser caching instructions |

**Use in client:**
```javascript
// JavaScript example
const response = await fetch('/api/appointments/sync/');
const lastSync = response.headers.get('X-Last-Sync');
localStorage.setItem('last_sync_timestamp', lastSync);
```

---

## 8. Testing Sync Endpoints

### Using Postman

1. **Set up Bearer Token**
   - Type: Bearer Token
   - Token: `<your_jwt_token>`

2. **Create Collection:**
   - GET `/api/sync/status/`
   - GET `/api/appointments/sync/`
   - GET `/api/appointments/sync/?last_sync_timestamp=2024-01-21T16:00:00Z`
   - PUT `/api/appointments/1/sync_update/`

3. **Check Response Headers:**
   - Click "Headers" tab after request
   - Look for `X-Last-Sync`, `ETag`, `X-Records-Synced`

### Using curl Test Script

```bash
#!/bin/bash

TOKEN="your_jwt_token_here"
API="http://localhost:8000/api"

echo "=== Testing Sync Endpoints ==="

echo "\n1. Sync Status"
curl -s -X GET "$API/sync/status/" \
  -H "Authorization: Bearer $TOKEN" | jq .

echo "\n2. Full Appointment Sync"
curl -s -X GET "$API/appointments/sync/" \
  -H "Authorization: Bearer $TOKEN" | jq .

echo "\n3. Incremental Sync (last 2 hours)"
TIMESTAMP=$(date -u -d '2 hours ago' '+%Y-%m-%dT%H:%M:%SZ')
curl -s -X GET "$API/appointments/sync/?last_sync_timestamp=$TIMESTAMP" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

**Document Version**: 1.0  
**Last Updated**: January 21, 2024  
**For Testing**: Use with real JWT tokens obtained from `/api/auth/token/` endpoint
