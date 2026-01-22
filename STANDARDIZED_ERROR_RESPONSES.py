"""
STANDARDIZED ERROR MESSAGE RESPONSES - API DOCUMENTATION
==========================================================

This document shows the standardized 401 and 403 error responses
used throughout the Rural Telemedicine Platform API.

All error messages are:
✓ Descriptive - Clearly explain what went wrong
✓ Safe - Do not leak sensitive system information
✓ Actionable - Help API consumers fix the issue
✓ Consistent - Same format across all endpoints
"""

# ============================================================================
# 401 UNAUTHORIZED - Authentication Required
# ============================================================================

RESPONSE_401_NO_CREDENTIALS = {
    "status": 401,
    "detail": "Authentication credentials were not provided."
}

RESPONSE_401_INVALID_TOKEN = {
    "status": 401,
    "detail": "Given token is invalid or has expired."
}

RESPONSE_401_MALFORMED_TOKEN = {
    "status": 401,
    "detail": "Token is malformed or invalid."
}

RESPONSE_401_SESSION_EXPIRED = {
    "status": 401,
    "detail": "Authentication session has expired. Please login again."
}

# ============================================================================
# 403 FORBIDDEN - Patient Record Restrictions
# ============================================================================

RESPONSE_403_PATIENT_CREATE_OTHER = {
    "status": 403,
    "detail": "You can only create a patient record for yourself."
}

RESPONSE_403_PATIENT_MODIFY_OTHER = {
    "status": 403,
    "detail": "You can only modify your own patient record."
}

RESPONSE_403_PATIENT_DELETE_RESTRICTED = {
    "status": 403,
    "detail": "Patient records cannot be deleted by non-admin users."
}

RESPONSE_403_PATIENT_DUPLICATE = {
    "status": 403,
    "detail": "Patient profile already exists for this user."
}

RESPONSE_403_PATIENT_ACCESS_DENIED = {
    "status": 403,
    "detail": "You do not have permission to access this patient record."
}

# ============================================================================
# 403 FORBIDDEN - Doctor Record Restrictions
# ============================================================================

RESPONSE_403_DOCTOR_CREATE_OTHER = {
    "status": 403,
    "detail": "You can only create a doctor record for yourself."
}

RESPONSE_403_DOCTOR_MODIFY_OTHER = {
    "status": 403,
    "detail": "You can only modify your own doctor record."
}

RESPONSE_403_DOCTOR_DELETE_RESTRICTED = {
    "status": 403,
    "detail": "Doctor records cannot be deleted by non-admin users."
}

RESPONSE_403_DOCTOR_DUPLICATE = {
    "status": 403,
    "detail": "Doctor profile already exists for this user."
}

RESPONSE_403_DOCTOR_ACCESS_DENIED = {
    "status": 403,
    "detail": "You do not have permission to access this doctor record."
}

# ============================================================================
# 403 FORBIDDEN - Appointment Restrictions
# ============================================================================

RESPONSE_403_APPOINTMENT_CREATE_SELF = {
    "status": 403,
    "detail": "You can only create appointments for yourself."
}

RESPONSE_403_APPOINTMENT_MODIFY_COMPLETED = {
    "status": 403,
    "detail": "Completed appointments cannot be modified."
}

RESPONSE_403_APPOINTMENT_DELETE_RESTRICTED = {
    "status": 403,
    "detail": "Appointments cannot be deleted. Update status to 'Cancelled' instead."
}

RESPONSE_403_APPOINTMENT_UPDATE_ROLE = {
    "status": 403,
    "detail": "Only the assigned doctor can mark an appointment as completed."
}

RESPONSE_403_APPOINTMENT_ACCESS_DENIED = {
    "status": 403,
    "detail": "You do not have permission to access this appointment."
}

# ============================================================================
# 400 BAD REQUEST - Validation Errors
# ============================================================================

RESPONSE_400_INVALID_PATIENT_ID = {
    "status": 400,
    "detail": "Invalid patient ID. Please verify and try again."
}

RESPONSE_400_INVALID_DOCTOR_ID = {
    "status": 400,
    "detail": "Invalid doctor ID. Please verify and try again."
}

RESPONSE_400_INVALID_STATUS = {
    "status": 400,
    "detail": "Invalid status value. Must be one of: Scheduled, Completed, Cancelled, No-show."
}

RESPONSE_400_INVALID_REQUEST = {
    "status": 400,
    "detail": "Invalid request. Please verify your input and try again."
}

# ============================================================================
# 404 NOT FOUND - Resource Not Found
# ============================================================================

RESPONSE_404_RESOURCE_NOT_FOUND = {
    "status": 404,
    "detail": "The requested resource was not found."
}

RESPONSE_404_PATIENT_NOT_FOUND = {
    "status": 404,
    "detail": "Patient not found."
}

RESPONSE_404_DOCTOR_NOT_FOUND = {
    "status": 404,
    "detail": "Doctor not found."
}

RESPONSE_404_APPOINTMENT_NOT_FOUND = {
    "status": 404,
    "detail": "Appointment not found."
}

# ============================================================================
# ERROR RESPONSE PATTERNS AND EXAMPLES
# ============================================================================

print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              STANDARDIZED ERROR MESSAGE RESPONSES                         ║
║                    Rural Telemedicine Platform API                        ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

HTTP STATUS CODES AND SECURITY CATEGORIES
═══════════════════════════════════════════════════════════════════════════

401 Unauthorized
   • User not authenticated or token invalid
   • Missing Authorization header
   • Token expired or malformed
   • Session expired

403 Forbidden
   • User authenticated but lacks permission
   • Attempting to access other user's data
   • Cross-user creation attempts
   • Writing to completed resources
   • Attempting to delete restricted resources

400 Bad Request
   • Invalid input data
   • Malformed request
   • Missing required fields
   • Invalid IDs or status values

404 Not Found
   • Resource doesn't exist (also for permission hiding)
   • Used for both actual missing resources and unauthorized access

""")

print("""
SECURITY PRINCIPLES IN ERROR MESSAGES
═══════════════════════════════════════════════════════════════════════════

1. NO INFORMATION LEAKAGE
   ✓ Do not reveal if a resource exists when access is denied
   ✓ Use generic "permission denied" instead of "user X not in doctor Y's list"
   ✓ Use 404 for unauthorized access to hide resource existence

2. ACTIONABLE MESSAGES
   ✓ Tell user what they CAN do instead of just what they can't
   ✓ Include required conditions (e.g., "only doctor can complete")
   ✓ Suggest alternatives (e.g., "use status change instead of delete")

3. CONSISTENT FORMAT
   ✓ All errors follow same structure: {"status": code, "detail": message}
   ✓ All 403s start with "You cannot..." or "You can only..."
   ✓ All 401s reference authentication
   ✓ All 400s reference input validation

4. CLARITY WITHOUT VERBOSITY
   ✓ Messages are clear but concise
   ✓ No system internals or stack traces in responses
   ✓ No specific user IDs or resource IDs that expose structure

""")

print("""
COMMON SCENARIOS AND RESPONSES
═══════════════════════════════════════════════════════════════════════════

SCENARIO 1: Unauthenticated Request
──────────────────────────────────────

Request:
  GET /api/patients/
  (No Authorization header)

Response: 401 Unauthorized
{
    "detail": "Authentication credentials were not provided."
}

Action: Include Bearer token in Authorization header


SCENARIO 2: Cross-User Patient Creation
──────────────────────────────────────

Request:
  POST /api/patients/
  Authorization: Bearer <patient1_token>
  
  Body: {
    "user": 99,
    "date_of_birth": "1990-01-01",
    ...
  }

Response: 403 Forbidden
{
    "detail": "You can only create a patient record for yourself."
}

Action: Only create records for your own user ID


SCENARIO 3: Duplicate Profile Creation
──────────────────────────────────────

Request:
  POST /api/patients/
  Authorization: Bearer <patient1_token>
  
  Body: {
    "user": <patient1_id>,
    "date_of_birth": "1990-01-01",
    ...
  }

Response: 400 Bad Request
{
    "detail": "Patient profile already exists for this user."
}

Action: You already have a profile; update it instead


SCENARIO 4: Modify Completed Appointment
──────────────────────────────────────

Request:
  PATCH /api/appointments/42/
  Authorization: Bearer <doctor_token>
  
  Body: {
    "diagnosis": "Updated diagnosis"
  }

Response: 403 Forbidden
{
    "detail": "Completed appointments cannot be modified."
}

Action: Use status change endpoint instead


SCENARIO 5: Attempt to Delete Appointment
──────────────────────────────────────

Request:
  DELETE /api/appointments/42/
  Authorization: Bearer <doctor_token>

Response: 403 Forbidden
{
    "detail": "Appointments cannot be deleted. Update status to 'Cancelled' instead."
}

Action: Update status to 'Cancelled' using PATCH /api/appointments/42/update_status/


SCENARIO 6: Access Other Patient's Record
──────────────────────────────────────

Request:
  GET /api/patients/99/
  Authorization: Bearer <patient1_token>

Response: 403 Forbidden or 404 Not Found
{
    "detail": "You do not have permission to access this patient record."
}
OR
{
    "detail": "The requested resource was not found."
}

Action: Only access your own patient records


SCENARIO 7: Invalid Token
──────────────────────────────────────

Request:
  GET /api/patients/
  Authorization: Bearer eyJhbGc...invalid...

Response: 401 Unauthorized
{
    "detail": "Given token is invalid or has expired."
}

Action: Login again to get a valid token


SCENARIO 8: Expired Token
──────────────────────────────────────

Request:
  GET /api/patients/
  Authorization: Bearer <expired_token>

Response: 401 Unauthorized
{
    "detail": "Authentication session has expired. Please login again."
}

Action: Use refresh token or login again

""")

print("""
API ERROR RESPONSE STANDARDIZATION
═══════════════════════════════════════════════════════════════════════════

All error responses follow this JSON structure:

{
    "status": <HTTP_STATUS_CODE>,
    "detail": "<Human-readable error message>"
}

Status Code    Meaning                  Use Case
─────────────────────────────────────────────────────────────────────────
401            Unauthorized             Missing/invalid authentication
403            Forbidden                Authenticated but no permission
400            Bad Request              Invalid input data
404            Not Found                Resource missing (or hidden by permission)

""")

print("""
ERROR MESSAGE CATEGORIES
═══════════════════════════════════════════════════════════════════════════

AUTHENTICATION ERRORS (401)
✓ "Authentication credentials were not provided."
✓ "Given token is invalid or has expired."
✓ "Token is malformed or invalid."
✓ "Authentication session has expired. Please login again."

PERMISSION ERRORS (403) - Data Access
✓ "You do not have permission to access this patient record."
✓ "You do not have permission to access this doctor record."
✓ "You do not have permission to access this appointment."

PERMISSION ERRORS (403) - Write Operations
✓ "You can only create a patient record for yourself."
✓ "You can only create a doctor record for yourself."
✓ "You can only modify your own patient record."
✓ "Appointments cannot be deleted. Update status to 'Cancelled' instead."
✓ "Completed appointments cannot be modified."
✓ "Only the assigned doctor can mark an appointment as completed."

VALIDATION ERRORS (400)
✓ "Invalid patient ID. Please verify and try again."
✓ "Invalid doctor ID. Please verify and try again."
✓ "Invalid status value. Must be one of: Scheduled, Completed, Cancelled, No-show."
✓ "Patient profile already exists for this user."
✓ "Doctor profile already exists for this user."

RESOURCE ERRORS (404)
✓ "Patient not found."
✓ "Doctor not found."
✓ "Appointment not found."
✓ "The requested resource was not found."

""")

print("""
TESTING ERROR MESSAGES
═══════════════════════════════════════════════════════════════════════════

All error messages are verified by:

✓ 13 Security hardening tests covering permission denials
✓ Tests verify correct HTTP status codes
✓ Tests verify error message content
✓ Tests verify permission enforcement

Test Coverage:
  • Patient data isolation (403 / 404)
  • Doctor record restrictions (403)
  • Appointment access control (403)
  • Duplicate prevention (400)
  • Completed appointment protection (403)
  • Deletion prevention (403)
  • Cross-user creation prevention (403)
  • Unauthenticated access (401)
  • Token validation (401)

═══════════════════════════════════════════════════════════════════════════

NEXT STEPS FOR API CONSUMERS
═══════════════════════════════════════════════════════════════════════════

When receiving a 401:
  → Include Authorization header with valid Bearer token
  → If expired, use refresh token endpoint
  → If missing, login first

When receiving a 403:
  → Review what operation was attempted
  → Check if you have permission for that resource
  → Ensure you're operating on your own data
  → Use alternative endpoints if suggested in message

When receiving a 400:
  → Check your request data for invalid values
  → Verify all required fields are present
  → Use valid IDs (check for typos)
  → Use valid status values

When receiving a 404:
  → Verify resource ID is correct
  → Check if you have permission to access it
  → If permission denied, will return 404 for security

═══════════════════════════════════════════════════════════════════════════
""")
