# ERROR MESSAGE STANDARDIZATION - API RESPONSES

## Overview

All permission denial error messages have been standardized to provide:
- **Descriptive information** - Users understand what went wrong
- **Security** - No sensitive information leakage
- **Consistency** - All errors follow the same format
- **Actionability** - Users know how to fix the issue

---

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| **401** | Unauthorized | Missing/invalid authentication credentials |
| **403** | Forbidden | Authenticated but lacks permission |
| **400** | Bad Request | Invalid data or validation error |
| **404** | Not Found | Resource doesn't exist (also used for info hiding) |

---

## 401 UNAUTHORIZED - Authentication Issues

### Missing Credentials
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Invalid/Expired Token
```json
{
  "detail": "Given token is invalid or has expired."
}
```

### Malformed Token
```json
{
  "detail": "Token is malformed or invalid."
}
```

### Session Expired
```json
{
  "detail": "Authentication session has expired. Please login again."
}
```

---

## 403 FORBIDDEN - Patient Operations

### Cannot Create Record for Another User
**Scenario:** Patient attempts to create patient record for another user
```
POST /api/patients/
Authorization: Bearer <token>
Body: { "user": 42, ... }

Response: 403 Forbidden
```
```json
{
  "detail": "You can only create a patient record for yourself."
}
```

### Cannot Modify Another Patient's Record
**Scenario:** Patient attempts to update another patient's record
```
PATCH /api/patients/5/
Authorization: Bearer <token>
Body: { "phone_number": "..." }

Response: 403 Forbidden
```
```json
{
  "detail": "You can only modify your own patient record."
}
```

### Cannot Delete Patient Records
**Scenario:** Non-admin user attempts to delete a patient record
```
DELETE /api/patients/5/
Authorization: Bearer <user_token>

Response: 403 Forbidden
```
```json
{
  "detail": "Patient records cannot be deleted by non-admin users."
}
```

### Duplicate Patient Profile
**Scenario:** User attempts to create duplicate profile (2nd profile for same user)
```
POST /api/patients/
Authorization: Bearer <token>
Body: { "user": 1, ... }

Response: 400 Bad Request
```
```json
{
  "detail": "Patient profile already exists for this user."
}
```

### Patient Access Denied
**Scenario:** Patient attempts to access another patient's record
```
GET /api/patients/5/
Authorization: Bearer <other_patient_token>

Response: 403 Forbidden OR 404 Not Found
```
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## 403 FORBIDDEN - Doctor Operations

### Cannot Create Record for Another User
**Scenario:** Doctor attempts to create doctor record for another user
```
POST /api/doctors/
Authorization: Bearer <token>
Body: { "user": 42, ... }

Response: 403 Forbidden
```
```json
{
  "detail": "You can only create a doctor record for yourself."
}
```

### Cannot Modify Another Doctor's Record
**Scenario:** Doctor attempts to modify another doctor's record
```
PATCH /api/doctors/5/
Authorization: Bearer <token>
Body: { "is_available": false }

Response: 403 Forbidden
```
```json
{
  "detail": "You can only modify your own doctor record."
}
```

### Cannot Delete Doctor Records
**Scenario:** Non-admin user attempts to delete a doctor record
```
DELETE /api/doctors/5/
Authorization: Bearer <user_token>

Response: 403 Forbidden
```
```json
{
  "detail": "Doctor records cannot be deleted by non-admin users."
}
```

### Duplicate Doctor Profile
**Scenario:** User attempts to create duplicate doctor profile
```
POST /api/doctors/
Authorization: Bearer <token>
Body: { "user": 1, ... }

Response: 400 Bad Request
```
```json
{
  "detail": "Doctor profile already exists for this user."
}
```

### Doctor Access Denied
**Scenario:** Patient attempts to access doctor record not in their appointments
```
GET /api/doctors/5/
Authorization: Bearer <patient_token>

Response: 403 Forbidden OR 404 Not Found
```
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## 403 FORBIDDEN - Appointment Operations

### Cannot Create Appointments for Others
**Scenario:** Patient attempts to create appointment for another patient
```
POST /api/appointments/
Authorization: Bearer <patient1_token>
Body: { "patient": 2, "doctor": 1 }

Response: 403 Forbidden
```
```json
{
  "detail": "You can only create appointments for yourself."
}
```

### Cannot Modify Completed Appointments
**Scenario:** Doctor attempts to modify a completed appointment
```
PATCH /api/appointments/15/
Authorization: Bearer <doctor_token>
Body: { "diagnosis": "New diagnosis" }

Response: 403 Forbidden
```
```json
{
  "detail": "Completed appointments cannot be modified."
}
```

### Cannot Delete Appointments Directly
**Scenario:** User attempts to delete an appointment
```
DELETE /api/appointments/10/
Authorization: Bearer <token>

Response: 403 Forbidden
```
```json
{
  "detail": "Appointments cannot be deleted. Update status to 'Cancelled' instead."
}
```

### Cannot Mark Appointment as Completed
**Scenario:** Patient attempts to mark their own appointment as completed
```
PATCH /api/appointments/10/update_status/
Authorization: Bearer <patient_token>
Body: { "status": "Completed" }

Response: 403 Forbidden
```
```json
{
  "detail": "Only the assigned doctor can mark an appointment as completed."
}
```

### Appointment Access Denied
**Scenario:** Doctor attempts to access appointment with different doctor
```
GET /api/appointments/99/
Authorization: Bearer <doctor1_token>

Response: 403 Forbidden OR 404 Not Found
```
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## 400 BAD REQUEST - Validation Errors

### Invalid Status Value
**Scenario:** Attempting to update appointment with invalid status
```
PATCH /api/appointments/10/update_status/
Authorization: Bearer <doctor_token>
Body: { "status": "InvalidStatus" }

Response: 400 Bad Request
```
```json
{
  "detail": "Invalid status value. Must be one of: Scheduled, Completed, Cancelled, No-show."
}
```

### Invalid Patient ID
**Scenario:** Appointment created with non-existent patient
```
POST /api/appointments/
Authorization: Bearer <token>
Body: { "patient": 999, "doctor": 1 }

Response: 400 Bad Request
```
```json
{
  "detail": "Invalid patient ID. Please verify and try again."
}
```

### Invalid Doctor ID
**Scenario:** Appointment created with non-existent doctor
```
POST /api/appointments/
Authorization: Bearer <token>
Body: { "patient": 1, "doctor": 999 }

Response: 400 Bad Request
```
```json
{
  "detail": "Invalid doctor ID. Please verify and try again."
}
```

### Invalid Request
**Scenario:** Malformed or invalid request
```
POST /api/appointments/
Authorization: Bearer <token>
Body: { /* invalid data */ }

Response: 400 Bad Request
```
```json
{
  "detail": "Invalid request. Please verify your input and try again."
}
```

---

## Error Message Categories

### Patient Record Messages
- ✅ `PATIENT_CREATE_OTHER` - Cannot create for others
- ✅ `PATIENT_MODIFY_OTHER` - Cannot modify others' records
- ✅ `PATIENT_DELETE_RESTRICTED` - Deletion restricted
- ✅ `PATIENT_DUPLICATE` - Duplicate profile exists
- ✅ `PATIENT_ACCESS_DENIED` - Access denied

### Doctor Record Messages
- ✅ `DOCTOR_CREATE_OTHER` - Cannot create for others
- ✅ `DOCTOR_MODIFY_OTHER` - Cannot modify others' records
- ✅ `DOCTOR_DELETE_RESTRICTED` - Deletion restricted
- ✅ `DOCTOR_DUPLICATE` - Duplicate profile exists
- ✅ `DOCTOR_ACCESS_DENIED` - Access denied

### Appointment Messages
- ✅ `APPOINTMENT_CREATE_SELF` - Cannot create for others
- ✅ `APPOINTMENT_MODIFY_COMPLETED` - Cannot modify completed
- ✅ `APPOINTMENT_DELETE_RESTRICTED` - Must use status change
- ✅ `APPOINTMENT_UPDATE_ROLE` - Only doctor can complete
- ✅ `APPOINTMENT_ACCESS_DENIED` - Access denied

### Authentication Messages
- ✅ `AUTH_CREDENTIALS_REQUIRED` - No credentials provided
- ✅ `AUTH_INVALID_TOKEN` - Token invalid/expired
- ✅ `AUTH_MALFORMED_TOKEN` - Token format error
- ✅ `AUTH_SESSION_EXPIRED` - Session expired

### Validation Messages
- ✅ `INVALID_PATIENT_ID` - Patient not found
- ✅ `INVALID_DOCTOR_ID` - Doctor not found
- ✅ `INVALID_STATUS` - Invalid status value
- ✅ `INVALID_REQUEST` - Invalid request format

---

## Best Practices Implemented

### ✅ Descriptive but Safe
- Messages explain what went wrong
- No sensitive information leaked
- No database/system details exposed

### ✅ Consistent Format
- All messages follow same structure
- Standardized error response format
- Predictable error handling

### ✅ Actionable Guidance
- Users know how to resolve the issue
- Alternative actions suggested (e.g., use status change instead of delete)
- Clear requirements stated

### ✅ Security-First
- 404 responses used when appropriate to hide info
- No stack traces or internal errors exposed
- User data isolation strictly enforced

### ✅ Centralized Management
- All messages in `error_messages.py`
- Easy to maintain and update
- Single source of truth for error text

---

## Usage in Code

### Using ErrorMessages in Views

```python
from .error_messages import ErrorMessages

# In a permission check
if patient.user != request.user:
    raise PermissionDenied(
        detail=ErrorMessages.PATIENT_MODIFY_OTHER
    )

# In validation
if Patient.objects.filter(user=user).exists():
    raise ValidationError(
        detail=ErrorMessages.PATIENT_DUPLICATE
    )

# In status response
return Response(
    {'detail': ErrorMessages.INVALID_STATUS},
    status=status.HTTP_400_BAD_REQUEST
)
```

### Response Helpers

```python
# Generate 403 response
response = ErrorMessages.get_forbidden_response(
    ErrorMessages.PATIENT_CREATE_OTHER
)
# Returns: {"status": 403, "detail": "..."}

# Generate 401 response
response = ErrorMessages.get_unauthorized_response(
    ErrorMessages.AUTH_INVALID_TOKEN
)
# Returns: {"status": 401, "detail": "..."}

# Generate 400 response
response = ErrorMessages.get_validation_error_response(
    ErrorMessages.INVALID_PATIENT_ID
)
# Returns: {"status": 400, "detail": "..."}
```

---

## Testing Error Responses

All error messages are tested in `telemedicine/tests_security_hardening.py`:

```python
# Test permission error message
response = client.post('/api/patients/', 
    {'user': other_user.id})
assert response.status_code == 403
assert 'yourself' in response.data['detail'].lower()
```

---

## Summary

| Feature | Benefit |
|---------|---------|
| Standardized Messages | Consistent API experience |
| Centralized Definition | Easy to maintain and update |
| Security-First Design | No information leakage |
| Clear Guidance | Users know how to fix issues |
| Comprehensive Coverage | All error scenarios handled |

All error messages are now standardized, secure, and consistent across the entire API.
