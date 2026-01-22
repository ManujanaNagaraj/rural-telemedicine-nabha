# Enhanced Appointment Workflow Implementation
## Rural Telemedicine Platform – Nabha

**Status**: ✅ COMPLETE  
**Date**: 2026-01-22  
**Focus**: Production-ready appointment lifecycle management

---

## 📋 **FILES MODIFIED**

| File | Changes |
|------|---------|
| [telemedicine/models.py](telemedicine/models.py) | Enhanced Appointment model with status lifecycle, audit fields, and state transition methods |
| [telemedicine/serializers.py](telemedicine/serializers.py) | Added comprehensive validation serializers for appointments and status updates |
| [telemedicine/views.py](telemedicine/views.py) | Enhanced AppointmentViewSet with new endpoints for confirm, complete, cancel, and slot availability |
| **NEW**: [telemedicine/appointment_service.py](telemedicine/appointment_service.py) | Core business logic for appointment validation, conflict detection, and availability checking |

---

## 🎯 **KEY FEATURES IMPLEMENTED**

### 1. **Appointment Status Lifecycle**

```
PENDING → CONFIRMED → COMPLETED
   ↓
CANCELLED (anytime)
   ↓
NO_SHOW (from CONFIRMED only)
```

| Status | Meaning | Can Transition To |
|--------|---------|------------------|
| **PENDING** | Initial state, awaiting confirmation | CONFIRMED, CANCELLED |
| **CONFIRMED** | Doctor confirmed the appointment | COMPLETED, CANCELLED, NO_SHOW |
| **COMPLETED** | Appointment finished | (Terminal) |
| **CANCELLED** | Appointment cancelled with reason | (Terminal) |
| **NO_SHOW** | Patient didn't show up | (Terminal) |

### 2. **Doctor Availability Validation**

```python
# Prevents double booking by checking:
- Existing appointments within slot duration
- Only counts PENDING and CONFIRMED appointments
- Respects doctor's is_available flag
- Raises clear error messages
```

### 3. **Patient Constraints**

```python
# Prevents patient conflicts:
- No overlapping appointments
- Cannot book in the past
- Validates across all active appointments
- Clear error messaging
```

### 4. **Automatic Doctor Assignment** (Optional)

```python
AppointmentService.auto_assign_doctor(specialization="Cardiology")
# Returns doctor with:
# - is_available = True
# - Fewest appointments in next 7 days
# - Optional specialization matching
```

### 5. **Cancellation Logic with Reason Tracking**

```python
appointment.cancel(
    reason="Doctor is unavailable",
    cancelled_by="DOCTOR"  # or "PATIENT" or "ADMIN"
)
# Tracks: cancelled_reason, cancelled_by, cancelled_at
```

### 6. **Audit Fields**

```
- created_at: When appointment was created
- updated_at: Last modification timestamp
- confirmed_at: When appointment was confirmed
- completed_at: When appointment was completed
- cancelled_at: When appointment was cancelled
```

---

## 🔧 **CORE MODULES**

### **Appointment Model Enhancements** (`models.py`)

```python
class Appointment(models.Model):
    # Status lifecycle management
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No-show'),
    ]
    
    # State transition methods
    def confirm()           # PENDING → CONFIRMED
    def complete()          # CONFIRMED → COMPLETED
    def cancel()            # Any → CANCELLED
    def mark_no_show()      # CONFIRMED → NO_SHOW
    
    # Validation methods
    def can_be_confirmed()
    def can_be_completed()
    def can_be_cancelled()
```

### **Appointment Service** (`appointment_service.py`)

```python
class AppointmentService:
    # Validation
    validate_appointment_date()
    validate_new_appointment()
    validate_appointment_update()
    
    # Conflict detection
    check_doctor_availability()
    check_patient_overlapping_appointments()
    
    # Auto-assignment
    auto_assign_doctor()
    
    # Utility
    get_available_slots()
    get_appointment_timeline()
```

### **Enhanced Serializers** (`serializers.py`)

```python
- AppointmentSerializer: Full validation on create/update
- AppointmentStatusUpdateSerializer: State transition validation
- AppointmentAvailableSlotsSerializer: Request validation
```

---

## 🚀 **API ENDPOINTS**

### **1. Create Appointment**
```
POST /api/appointments/

Request Body:
{
  "patient": 1,
  "doctor": 2,
  "appointment_date": "2026-01-25T14:30:00Z",
  "symptoms": "Fever and cough"
}

Response (201 Created):
{
  "id": 5,
  "patient": 1,
  "patient_name": "John Doe",
  "doctor": 2,
  "doctor_name": "Dr. Sarah Smith",
  "doctor_specialization": "General Medicine",
  "appointment_date": "2026-01-25T14:30:00Z",
  "status": "PENDING",
  "symptoms": "Fever and cough",
  "diagnosis": "",
  "prescription": "",
  "notes": "",
  "cancelled_reason": "",
  "cancelled_by": "",
  "created_at": "2026-01-22T10:00:00Z",
  "updated_at": "2026-01-22T10:00:00Z",
  "confirmed_at": null,
  "completed_at": null,
  "cancelled_at": null
}

Error Response (400):
{
  "appointment_date": [
    "Appointment date cannot be in the past."
  ]
}
```

### **2. Get All My Appointments**
```
GET /api/appointments/my_appointments/
GET /api/appointments/my_appointments/?status=CONFIRMED
GET /api/appointments/my_appointments/?upcoming=true

Response (200 OK):
[
  {
    "id": 5,
    "patient": 1,
    "patient_name": "John Doe",
    "doctor": 2,
    "doctor_name": "Dr. Sarah Smith",
    "doctor_specialization": "General Medicine",
    "appointment_date": "2026-01-25T14:30:00Z",
    "status": "PENDING",
    "symptoms": "Fever and cough",
    "diagnosis": "",
    "prescription": "",
    "notes": "",
    "created_at": "2026-01-22T10:00:00Z",
    "updated_at": "2026-01-22T10:00:00Z",
    "confirmed_at": null,
    "completed_at": null,
    "cancelled_at": null
  }
]
```

### **3. Confirm Appointment (Doctor/Admin)**
```
POST /api/appointments/5/confirm/

Response (200 OK):
{
  "id": 5,
  "status": "CONFIRMED",
  "confirmed_at": "2026-01-22T10:05:00Z",
  ...
}

Error Response (400):
{
  "detail": "Cannot confirm appointment with status 'COMPLETED'"
}
```

### **4. Complete Appointment (Doctor/Admin)**
```
POST /api/appointments/5/complete/

Request Body (Optional - can include notes):
{
  "diagnosis": "Common Cold",
  "prescription": "Rest, fluids, paracetamol",
  "notes": "Patient advised to rest for 3 days"
}

Response (200 OK):
{
  "id": 5,
  "status": "COMPLETED",
  "diagnosis": "Common Cold",
  "prescription": "Rest, fluids, paracetamol",
  "notes": "Patient advised to rest for 3 days",
  "completed_at": "2026-01-25T14:45:00Z",
  ...
}

Error Response (403):
{
  "detail": "Only the assigned doctor or admin can complete this appointment."
}
```

### **5. Cancel Appointment**
```
POST /api/appointments/5/cancel/

Request Body:
{
  "reason": "Doctor is unavailable",
  "cancelled_by": "DOCTOR"
}

Response (200 OK):
{
  "id": 5,
  "status": "CANCELLED",
  "cancelled_reason": "Doctor is unavailable",
  "cancelled_by": "DOCTOR",
  "cancelled_at": "2026-01-22T10:10:00Z",
  ...
}

Error Response (400):
{
  "detail": "Cannot cancel appointment with status 'COMPLETED'"
}
```

### **6. Mark as No-Show (Doctor/Admin)**
```
POST /api/appointments/5/no_show/

Response (200 OK):
{
  "id": 5,
  "status": "NO_SHOW",
  ...
}
```

### **7. Get Available Slots for Doctor**
```
GET /api/appointments/available_slots/?doctor_id=2&date=2026-01-25&num_slots=8

Response (200 OK):
{
  "doctor_id": 2,
  "doctor_name": "Dr. Sarah Smith",
  "date": "2026-01-25",
  "available_slots": [
    "2026-01-25T09:00:00Z",
    "2026-01-25T09:30:00Z",
    "2026-01-25T10:00:00Z",
    "2026-01-25T10:30:00Z",
    "2026-01-25T14:00:00Z",
    "2026-01-25T14:30:00Z",
    "2026-01-25T15:00:00Z",
    "2026-01-25T15:30:00Z"
  ],
  "total_slots_available": 8
}
```

### **8. Update Appointment** (Partial Update)
```
PATCH /api/appointments/5/

Request Body:
{
  "symptoms": "Updated symptoms description"
}

Response (200 OK):
{
  "id": 5,
  "symptoms": "Updated symptoms description",
  ...
}

Error Response (403):
{
  "detail": "Cannot modify appointments with status COMPLETED."
}
```

---

## 📊 **SAMPLE API WORKFLOWS**

### **Workflow 1: Complete Appointment Lifecycle**

```bash
# Step 1: Patient books appointment (PENDING)
POST /api/appointments/
{
  "patient": 1,
  "doctor": 2,
  "appointment_date": "2026-01-25T14:30:00Z",
  "symptoms": "Fever, cough, headache"
}
Response: status=PENDING, id=5

# Step 2: Doctor confirms (PENDING → CONFIRMED)
POST /api/appointments/5/confirm/
Response: status=CONFIRMED, confirmed_at=2026-01-22T10:05:00Z

# Step 3: Patient checks status
GET /api/appointments/my_appointments/?status=CONFIRMED
Response: [Appointment with id=5, status=CONFIRMED]

# Step 4: Appointment time arrives, doctor completes it
POST /api/appointments/5/complete/
{
  "diagnosis": "Viral fever",
  "prescription": "Rest and hydration",
  "notes": "Follow up if symptoms persist"
}
Response: status=COMPLETED, completed_at=2026-01-25T14:45:00Z
```

### **Workflow 2: Cancellation by Patient**

```bash
# Patient cancels pending appointment
POST /api/appointments/5/cancel/
{
  "reason": "Unable to attend due to emergency",
  "cancelled_by": "PATIENT"
}
Response: status=CANCELLED, cancelled_reason="Unable to attend..."
```

### **Workflow 3: Doctor Availability Check**

```bash
# Get available slots before booking
GET /api/appointments/available_slots/?doctor_id=2&date=2026-01-25&num_slots=8
Response: 
{
  "available_slots": [
    "2026-01-25T09:00:00Z",
    "2026-01-25T09:30:00Z",
    ...
  ],
  "total_slots_available": 8
}

# Book appointment in available slot
POST /api/appointments/
{
  "patient": 1,
  "doctor": 2,
  "appointment_date": "2026-01-25T09:00:00Z",
  "symptoms": "Regular checkup"
}
Response: success
```

### **Workflow 4: Double Booking Prevention**

```bash
# First appointment
POST /api/appointments/
{
  "patient": 1,
  "doctor": 2,
  "appointment_date": "2026-01-25T14:30:00Z",
  "symptoms": "Fever"
}
Response: success, id=5

# Try to book overlapping slot for same doctor
POST /api/appointments/
{
  "patient": 3,
  "doctor": 2,
  "appointment_date": "2026-01-25T14:30:00Z",
  "symptoms": "Cough"
}
Response: 400 error
{
  "detail": "Dr. Sarah Smith is not available at this time. Another appointment is already scheduled (ID: 5)."
}
```

---

## 🔒 **PERMISSION MATRIX**

| Action | Patient | Doctor | Admin | Notes |
|--------|---------|--------|-------|-------|
| Create Appointment | ✅ (self) | ❌ | ✅ | Patient can only create for self |
| View Appointment | ✅ (own) | ✅ (assigned) | ✅ (all) | Strict filtering applied |
| Confirm | ❌ | ✅ (assigned) | ✅ | Doctor confirms |
| Complete | ❌ | ✅ (assigned) | ✅ | Doctor marks as done |
| Cancel | ✅ (own, PENDING/CONFIRMED) | ✅ (assigned) | ✅ (any) | Patient can cancel pending |
| Mark No-Show | ❌ | ✅ (assigned) | ✅ | Doctor marks when patient absent |
| View Slots | ✅ | ✅ | ✅ | All can check availability |

---

## 🧪 **VALIDATION EXAMPLES**

### **Error: Appointment in the Past**
```json
POST /api/appointments/
{
  "patient": 1,
  "doctor": 2,
  "appointment_date": "2026-01-20T14:30:00Z"
}

Response (400):
{
  "appointment_date": [
    "Appointment date cannot be in the past. Current time: 2026-01-22T10:00:00Z"
  ]
}
```

### **Error: Doctor Not Available**
```json
Response (400):
{
  "detail": "Dr. Sarah Smith is currently not available for appointments."
}
```

### **Error: Double Booking**
```json
Response (400):
{
  "detail": "Dr. Sarah Smith is not available at this time. Another appointment is already scheduled (ID: 5)."
}
```

### **Error: Patient Overlap**
```json
Response (400):
{
  "detail": "Patient already has an appointment at this time (ID: 3). Cannot book overlapping appointments."
}
```

### **Error: Invalid State Transition**
```json
POST /api/appointments/5/confirm/  # Appointment already COMPLETED

Response (400):
{
  "detail": "Cannot confirm appointment with status 'COMPLETED'"
}
```

---

## 📈 **AUDIT TRAIL EXAMPLE**

```json
{
  "id": 5,
  "patient": 1,
  "doctor": 2,
  "status": "COMPLETED",
  "created_at": "2026-01-22T09:00:00Z",
  "updated_at": "2026-01-25T15:00:00Z",
  "confirmed_at": "2026-01-22T10:05:00Z",
  "completed_at": "2026-01-25T14:50:00Z",
  "cancelled_at": null
}
```

Timeline shows:
1. Created: 2026-01-22T09:00:00Z (status: PENDING)
2. Confirmed: 2026-01-22T10:05:00Z (status: CONFIRMED)
3. Completed: 2026-01-25T14:50:00Z (status: COMPLETED)

---

## ✨ **SUCCESS CHECKLIST**

✅ Appointment status lifecycle implemented (PENDING → CONFIRMED → COMPLETED)  
✅ Doctor availability validation (prevents double booking)  
✅ Patient constraint validation (no overlaps, no past dates)  
✅ State transition validation with clear error messages  
✅ Cancellation logic with reason tracking  
✅ API enhancements (confirm, complete, cancel, no_show, available_slots)  
✅ Audit fields (created_at, updated_at, confirmed_at, completed_at, cancelled_at)  
✅ Comprehensive serializers with validation  
✅ Business logic in dedicated service module  
✅ Role-based permission enforcement  
✅ Proper HTTP status codes  
✅ Clear error messages  

---

## 📋 **SUGGESTED GIT COMMIT BREAKDOWN**

This implementation can be split into **4 logical commits**:

### **Commit 1: Core Model Enhancement**
```
commit: "feat(appointments): Add status lifecycle and audit fields to Appointment model"

Files:
  telemedicine/models.py

Description:
Enhanced Appointment model with:
- New status choices (PENDING, CONFIRMED, COMPLETED, CANCELLED, NO_SHOW)
- State transition methods (confirm, complete, cancel, mark_no_show)
- Audit fields (confirmed_at, completed_at, cancelled_at)
- Cancellation tracking (cancelled_reason, cancelled_by)
- Validation logic (clean method)
- Database indexes for performance
```

### **Commit 2: Business Logic Service**
```
commit: "feat(appointments): Implement AppointmentService for business logic"

Files:
  telemedicine/appointment_service.py

Description:
New service module with:
- Doctor availability validation
- Patient overlap detection
- Appointment date validation
- Auto-doctor assignment logic
- Available slots retrieval
- Audit trail retrieval
- Comprehensive error handling
```

### **Commit 3: API Enhancement**
```
commit: "feat(api): Enhance appointment endpoints with new actions and validation"

Files:
  telemedicine/views.py
  telemedicine/serializers.py

Description:
Enhanced AppointmentViewSet with new endpoints:
- POST /confirm/ - Confirm pending appointment
- POST /complete/ - Mark appointment as completed
- POST /cancel/ - Cancel with reason tracking
- POST /no_show/ - Mark patient as no-show
- GET /available_slots/ - Get doctor's available slots
- Enhanced serializers with comprehensive validation
- Improved error handling and permissions
```

### **Commit 4: Documentation**
```
commit: "docs(appointments): Add comprehensive appointment workflow documentation"

Files:
  APPOINTMENT_WORKFLOW_DOCUMENTATION.md

Description:
Complete documentation including:
- Appointment lifecycle diagram
- API endpoint specifications
- Sample requests and responses
- Permission matrix
- Validation error examples
- Audit trail example
- Workflow examples
- Deployment notes
```

---

## 🚀 **DEPLOYMENT NOTES**

### **Database Migration Required**
```bash
# After deploying changes:
python manage.py makemigrations telemedicine
python manage.py migrate
```

### **New Fields in Appointment Table**
- `confirmed_at` (DateTimeField, nullable)
- `completed_at` (DateTimeField, nullable)
- `cancelled_at` (DateTimeField, nullable)
- `cancelled_reason` (CharField, max_length=255)
- `cancelled_by` (CharField, choices)

### **Backward Compatibility**
- Old status values ('Scheduled') should be mapped to 'PENDING'
- Data migration may be needed for existing records

---

## 🎓 **KEY LEARNING POINTS**

1. **Service Layer Pattern**: Business logic separated into dedicated service class
2. **State Machine Pattern**: Clear state transitions with validation
3. **Audit Trail**: Complete tracking of status changes with timestamps
4. **Comprehensive Validation**: Multiple layers of validation for data integrity
5. **Permission-Based Access**: Role-based access control at endpoint level
6. **Clear Error Messages**: User-friendly error messages for debugging
7. **Idempotent Operations**: Operations that can be safely retried

---

**End of Documentation**
