"""
SAMPLE FORBIDDEN RESPONSES - Error Message Standardization
Demonstrates standardized 401/403/400 error responses
"""

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   STANDARDIZED ERROR RESPONSES - SAMPLES                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

""")

print("""
┌──────────────────────────────────────────────────────────────────────────────┐
│ 401 UNAUTHORIZED - Authentication Required                                   │
└──────────────────────────────────────────────────────────────────────────────┘

Scenario 1: No credentials provided
  Request:  GET /api/patients/
  Auth:     (none)

Response:
  Status: 401 Unauthorized
  Body:
  {
    "detail": "Authentication credentials were not provided."
  }

Scenario 2: Invalid or expired token
  Request:  GET /api/patients/
  Auth:     Bearer expired_or_invalid_token

Response:
  Status: 401 Unauthorized
  Body:
  {
    "detail": "Given token is invalid or has expired."
  }

Scenario 3: Malformed token
  Request:  GET /api/patients/
  Auth:     Bearer malformed.token

Response:
  Status: 401 Unauthorized
  Body:
  {
    "detail": "Token is malformed or invalid."
  }
""")

print("""
┌──────────────────────────────────────────────────────────────────────────────┐
│ 403 FORBIDDEN - Patient Operations                                           │
└──────────────────────────────────────────────────────────────────────────────┘

Scenario 1: Patient creates profile for another user
  Request:  POST /api/patients/
  Auth:     Bearer patient1_token
  Body:
  {
    "user": 42,
    "date_of_birth": "1998-05-15",
    "gender": "Male",
    "phone_number": "+919876543999",
    "address": "Some Address"
  }

Response:
  Status: 403 Forbidden
  Body:
  {
    "detail": "You can only create a patient record for yourself."
  }

Scenario 2: Patient attempts to modify another patient's record
  Request:  PATCH /api/patients/5/
  Auth:     Bearer patient1_token
  Body:
  {
    "phone_number": "+919999999999"
  }

Response:
  Status: 403 Forbidden
  Body:
  {
    "detail": "You can only modify your own patient record."
  }

Scenario 3: Non-admin attempts to delete patient record
  Request:  DELETE /api/patients/5/
  Auth:     Bearer patient_token

Response:
  Status: 403 Forbidden
  Body:
  {
    "detail": "Patient records cannot be deleted by non-admin users."
  }
""")

print("""
┌──────────────────────────────────────────────────────────────────────────────┐
│ 400 BAD REQUEST - Duplicate Profile                                          │
└──────────────────────────────────────────────────────────────────────────────┘

Scenario: Patient attempts to create duplicate profile
  Request:  POST /api/patients/
  Auth:     Bearer patient_token
  Body:
  {
    "user": 1,
    "date_of_birth": "1995-01-15",
    "gender": "Male",
    "phone_number": "+919876543230",
    "address": "Different Address"
  }

Response:
  Status: 400 Bad Request
  Body:
  {
    "detail": "Patient profile already exists for this user."
  }
""")

print("""
┌──────────────────────────────────────────────────────────────────────────────┐
│ 403 FORBIDDEN - Doctor Operations                                            │
└──────────────────────────────────────────────────────────────────────────────┘

Scenario 1: Doctor creates profile for another user
  Request:  POST /api/doctors/
  Auth:     Bearer doctor1_token
  Body:
  {
    "user": 42,
    "specialization": "Cardiology",
    "license_number": "DOC-999",
    "phone_number": "+919876543999",
    "experience_years": 10
  }

Response:
  Status: 403 Forbidden
  Body:
  {
    "detail": "You can only create a doctor record for yourself."
  }

Scenario 2: Doctor attempts to modify another doctor's record
  Request:  PATCH /api/doctors/5/
  Auth:     Bearer doctor1_token
  Body:
  {
    "is_available": false
  }

Response:
  Status: 403 Forbidden
  Body:
  {
    "detail": "You can only modify your own doctor record."
  }
""")

print("""
┌──────────────────────────────────────────────────────────────────────────────┐
│ 403 FORBIDDEN - Appointment Operations                                       │
└──────────────────────────────────────────────────────────────────────────────┘

Scenario 1: Doctor attempts to modify completed appointment
  Request:  PATCH /api/appointments/45/
  Auth:     Bearer doctor_token
  Body:
  {
    "diagnosis": "Updated diagnosis"
  }

Response:
  Status: 403 Forbidden
  Body:
  {
    "detail": "Completed appointments cannot be modified."
  }

Scenario 2: User attempts to delete appointment instead of canceling
  Request:  DELETE /api/appointments/30/
  Auth:     Bearer token

Response:
  Status: 403 Forbidden
  Body:
  {
    "detail": "Appointments cannot be deleted. Update status to 'Cancelled' instead."
  }

Scenario 3: Patient attempts to mark appointment as completed
  Request:  PATCH /api/appointments/10/update_status/
  Auth:     Bearer patient_token
  Body:
  {
    "status": "Completed"
  }

Response:
  Status: 403 Forbidden
  Body:
  {
    "detail": "Only the assigned doctor can mark an appointment as completed."
  }

Scenario 4: Patient creates appointment for another patient
  Request:  POST /api/appointments/
  Auth:     Bearer patient1_token
  Body:
  {
    "patient": 2,
    "doctor": 1
  }

Response:
  Status: 403 Forbidden
  Body:
  {
    "detail": "You can only create appointments for yourself."
  }
""")

print("""
┌──────────────────────────────────────────────────────────────────────────────┐
│ 400 BAD REQUEST - Validation Errors                                          │
└──────────────────────────────────────────────────────────────────────────────┘

Scenario 1: Invalid appointment status
  Request:  PATCH /api/appointments/10/update_status/
  Auth:     Bearer doctor_token
  Body:
  {
    "status": "InvalidStatus"
  }

Response:
  Status: 400 Bad Request
  Body:
  {
    "detail": "Invalid status value. Must be one of: Scheduled, Completed, Cancelled, No-show."
  }

Scenario 2: Invalid patient ID
  Request:  POST /api/appointments/
  Auth:     Bearer token
  Body:
  {
    "patient": 999,
    "doctor": 1
  }

Response:
  Status: 400 Bad Request
  Body:
  {
    "detail": "Invalid patient ID. Please verify and try again."
  }

Scenario 3: Invalid doctor ID
  Request:  POST /api/appointments/
  Auth:     Bearer token
  Body:
  {
    "patient": 1,
    "doctor": 999
  }

Response:
  Status: 400 Bad Request
  Body:
  {
    "detail": "Invalid doctor ID. Please verify and try again."
  }
""")

print("""
┌──────────────────────────────────────────────────────────────────────────────┐
│ 404 NOT FOUND - Resource or Access Denied                                    │
└──────────────────────────────────────────────────────────────────────────────┘

Scenario 1: Patient attempts to access another patient's record
  Request:  GET /api/patients/5/
  Auth:     Bearer patient1_token

Response:
  Status: 404 Not Found OR 403 Forbidden
  Body:
  {
    "detail": "Not found."
  }
  OR
  {
    "detail": "You do not have permission to perform this action."
  }

Note: 404 is returned instead of 403 to prevent information leakage
      (avoids revealing that the resource exists but access is denied)

Scenario 2: Doctor attempts to access unrelated appointment
  Request:  GET /api/appointments/99/
  Auth:     Bearer doctor1_token

Response:
  Status: 404 Not Found OR 403 Forbidden
  Body:
  {
    "detail": "Not found."
  }
""")

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ERROR MESSAGE STANDARDIZATION SUMMARY                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║ All error messages are now:                                                 ║
║  ✓ Descriptive but safe (no info leakage)                                   ║
║  ✓ Standardized across all endpoints                                        ║
║  ✓ Centralized in error_messages.py                                         ║
║  ✓ Actionable (users know how to resolve)                                   ║
║  ✓ Consistent (same format for all errors)                                  ║
║  ✓ Tested (security tests verify messages)                                  ║
║                                                                              ║
║ Status Codes Used:                                                           ║
║  401 Unauthorized    - Missing or invalid authentication                    ║
║  403 Forbidden       - Permission denied                                    ║
║  400 Bad Request     - Invalid data or validation error                     ║
║  404 Not Found       - Resource not found (also for info hiding)            ║
║                                                                              ║
║ Message Categories:                                                          ║
║  • Authentication (4 messages)                                              ║
║  • Patient Operations (5 messages)                                          ║
║  • Doctor Operations (5 messages)                                           ║
║  • Appointment Operations (5 messages)                                      ║
║  • Validation Errors (4 messages)                                           ║
║                                                                              ║
║ Total: 23 standardized error messages                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
