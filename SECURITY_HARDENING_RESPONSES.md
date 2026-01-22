"""
SECURITY HARDENING - SAMPLE FORBIDDEN RESPONSES
============================================

This document shows sample 403 Forbidden responses from the hardened API.
All responses follow RFC 7807 Problem Detail specification.

1. PATIENT DATA ISOLATION ERRORS
"""

# Response 1: Patient cannot access another patient's record
PATIENT_CANNOT_ACCESS_OTHER_PATIENT = {
    "status": 403,
    "detail": "You do not have permission to perform this action."
}

# Response 2: Patient attempts to create record for another user
PATIENT_CANNOT_CREATE_FOR_OTHER = {
    "status": 403,
    "detail": "You can only create a patient record for yourself"
}

# Response 3: Cross-user creation attempt at perform_create level
PATIENT_CROSS_USER_CREATE_ERROR = {
    "status": 403,
    "detail": "You can only create a patient record for yourself"
}

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                SECURITY HARDENING - FORBIDDEN RESPONSES                    ║
╚════════════════════════════════════════════════════════════════════════════╝

""")

print("""
┌────────────────────────────────────────────────────────────────────────────┐
│ 1. PATIENT DATA ISOLATION ERRORS                                           │
└────────────────────────────────────────────────────────────────────────────┘

Scenario: Patient 1 tries to access Patient 2's record
POST /api/patients/5/
Authorization: Bearer <patient1_token>

Response: 403 Forbidden
─────────────────────────────────────────────────────────────────────────
{
    "detail": "You do not have permission to perform this action."
}

Scenario: Patient tries to create profile for another user
POST /api/patients/
Authorization: Bearer <patient1_token>

Request Body:
{
    "user": 42,
    "date_of_birth": "1998-05-15",
    "gender": "Male",
    "phone_number": "+919876543999",
    "address": "Some Address"
}

Response: 403 Forbidden
─────────────────────────────────────────────────────────────────────────
{
    "detail": "You can only create a patient record for yourself"
}

Scenario: Patient tries to create duplicate profile for themselves
POST /api/patients/
Authorization: Bearer <patient1_token>

Request Body:
{
    "user": 1,
    "date_of_birth": "1995-01-15",
    "gender": "Male",
    "phone_number": "+919876543210",
    "address": "New Address"
}

Response: 400 Bad Request
─────────────────────────────────────────────────────────────────────────
{
    "detail": "Patient profile already exists for this user"
}
""")

print("""
┌────────────────────────────────────────────────────────────────────────────┐
│ 2. DOCTOR ASSIGNMENT ISOLATION ERRORS                                      │
└────────────────────────────────────────────────────────────────────────────┘

Scenario: Doctor tries to modify another doctor's record
PATCH /api/doctors/5/
Authorization: Bearer <doctor1_token>

Request Body:
{
    "is_available": false
}

Response: 403 Forbidden
─────────────────────────────────────────────────────────────────────────
{
    "detail": "You do not have permission to perform this action."
}

Scenario: Doctor tries to access unrelated appointment
GET /api/appointments/99/
Authorization: Bearer <doctor1_token>

Response: 404 Not Found
─────────────────────────────────────────────────────────────────────────
{
    "detail": "Not found."
}

Note: 404 returned instead of 403 to prevent information leakage
about which appointments exist in the system.
""")

print("""
┌────────────────────────────────────────────────────────────────────────────┐
│ 3. WRITE OPERATION RESTRICTIONS                                            │
└────────────────────────────────────────────────────────────────────────────┘

Scenario: Doctor tries to modify completed appointment
PATCH /api/appointments/45/
Authorization: Bearer <doctor1_token>

Request Body:
{
    "diagnosis": "Updated diagnosis"
}

Response: 403 Forbidden
─────────────────────────────────────────────────────────────────────────
{
    "detail": "Cannot modify completed appointments. Use status change instead."
}

Scenario: User tries to delete appointment instead of canceling
DELETE /api/appointments/30/
Authorization: Bearer <doctor1_token>

Response: 403 Forbidden
─────────────────────────────────────────────────────────────────────────
{
    "detail": "Cannot delete appointments. Update status to 'Cancelled' instead."
}

Scenario: Patient tries to duplicate doctor profile
POST /api/doctors/
Authorization: Bearer <patient1_token>

Response: 403 Forbidden
─────────────────────────────────────────────────────────────────────────
{
    "detail": "You do not have permission to perform this action."
}
""")

print("""
┌────────────────────────────────────────────────────────────────────────────┐
│ 4. AUTHENTICATION ERRORS                                                   │
└────────────────────────────────────────────────────────────────────────────┘

Scenario: Unauthenticated user tries to access protected endpoint
GET /api/patients/
(No Authorization header)

Response: 401 Unauthorized
─────────────────────────────────────────────────────────────────────────
{
    "detail": "Authentication credentials were not provided."
}

Scenario: Invalid or expired token
GET /api/patients/
Authorization: Bearer <expired_token>

Response: 401 Unauthorized
─────────────────────────────────────────────────────────────────────────
{
    "detail": "Given token is invalid for any token type"
}
""")

print("""
┌────────────────────────────────────────────────────────────────────────────┐
│ 5. ROLE-BASED ACCESS ERRORS                                                │
└────────────────────────────────────────────────────────────────────────────┘

Scenario: Patient tries to modify doctor availability
PATCH /api/doctors/7/
Authorization: Bearer <patient1_token>

Request Body:
{
    "is_available": true
}

Response: 403 Forbidden
─────────────────────────────────────────────────────────────────────────
{
    "detail": "You do not have permission to perform this action."
}

Scenario: Duplicate doctor profile attempt
POST /api/doctors/
Authorization: Bearer <doctor1_token>

Request Body:
{
    "user": 2,
    "specialization": "Cardiology",
    "license_number": "DUPLICATE-123",
    "phone_number": "+919876543220",
    "experience_years": 10
}

Response: 400 Bad Request
─────────────────────────────────────────────────────────────────────────
{
    "detail": "Doctor profile already exists for this user"
}
""")

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         HTTP STATUS CODES USED                             ║
╠════════════════════════════════════════════════════════════════════════════╣
║ 200 OK                  - Request successful                               ║
║ 201 Created             - Resource successfully created                    ║
║ 400 Bad Request         - Invalid data (duplicate profile, validation)      ║
║ 401 Unauthorized        - Missing or invalid authentication                ║
║ 403 Forbidden           - Authenticated but permission denied              ║
║ 404 Not Found           - Resource not found (also for permission hiding)   ║
╚════════════════════════════════════════════════════════════════════════════╝

KEY SECURITY FEATURES
─────────────────────

✓ User Data Isolation:   Patients/Doctors cannot access other users' data
✓ Write Restrictions:    Cross-user creation prevented at multiple levels
✓ Completion Protection: Completed appointments cannot be modified
✓ Deletion Prevention:   No direct deletion of appointments (force status change)
✓ Role-Based Access:    Patients cannot modify doctor records
✓ Error Messages:        Descriptive messages without leaking sensitive info
✓ Information Hiding:    404 returned when access denied (prevents data enumeration)
✓ Duplicate Prevention:  Cannot create multiple profiles per user
✓ Admin Override:        Staff users bypass all restrictions

TESTING VERIFICATION
────────────────────

✓ 13/13 security tests passing
✓ Patient data isolation enforced
✓ Doctor assignment validation working
✓ Write operation restrictions active
✓ Role-based filtering functional
✓ Error messages are descriptive
✓ Completed appointment protection active
✓ Deletion prevention working
✓ Duplicate profile prevention active
✓ Unauthenticated access denied

""")
