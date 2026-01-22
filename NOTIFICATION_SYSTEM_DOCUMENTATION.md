# Notification & Alert System Documentation

## Overview

The Notification System provides comprehensive alerting for appointments and healthcare events in the rural telemedicine platform. It supports multiple notification types with user-controlled preferences and quiet hours.

**Supported Notification Types:**
- `APPOINTMENT_CREATED` - When appointment is scheduled
- `APPOINTMENT_CONFIRMED` - When doctor confirms appointment
- `APPOINTMENT_COMPLETED` - When appointment is finished
- `APPOINTMENT_CANCELLED` - When appointment is cancelled
- `APPOINTMENT_NO_SHOW` - When appointment marked as no-show
- `INVENTORY_LOW` - When medicine stock falls below threshold
- `INVENTORY_RESTOCKED` - When out-of-stock medicine becomes available
- `SYSTEM` - Administrative/system messages

## Architecture

### Models

#### 1. **Notification Model**
Stores individual notifications for users.

**Fields:**
- `user` - Foreign key to User
- `title` - Notification title (max 255 chars)
- `message` - Full notification text
- `notification_type` - Type of notification (choices above)
- `is_read` - Boolean flag for read status
- `read_at` - Timestamp of when marked as read
- `related_appointment` - Optional FK to Appointment
- `related_medicine` - Optional FK to Medicine
- `created_at` - Timestamp of creation

**Methods:**
- `mark_as_read()` - Marks notification as read with timestamp
- `get_absolute_url()` - Returns notification detail URL

#### 2. **NotificationPreference Model**
Stores user preferences for notifications.

**Fields:**
- `user` - Foreign key to User (one-to-one)
- `appointment_notifications` - Boolean, default True
- `inventory_notifications` - Boolean, default True
- `system_notifications` - Boolean, default True
- `quiet_hours_start` - Time when notifications are muted (HH:MM format)
- `quiet_hours_end` - Time when notifications resume
- `enable_quiet_hours` - Boolean to enable/disable quiet hours
- `created_at` - Timestamp of creation
- `updated_at` - Timestamp of last update

### Service Layer

#### **NotificationService Class**

Handles notification creation and delivery logic with extensibility for SMS/Email gateways.

**Key Methods:**

1. **notify_appointment_created(appointment)**
   - Notifies patient when appointment is created
   - Title: "Appointment Scheduled"
   - Message: "Your appointment with Dr. {doctor_name} is scheduled for {date} {time}"

2. **notify_appointment_confirmed(appointment)**
   - Notifies both patient and doctor when appointment is confirmed
   - Title: "Appointment Confirmed"
   - Message: "Your appointment on {date} at {time} is confirmed"

3. **notify_appointment_completed(appointment)**
   - Notifies both users when appointment is completed
   - Title: "Appointment Completed"
   - Message: "Your appointment on {date} has been completed"

4. **notify_appointment_cancelled(appointment, reason="")**
   - Notifies both users when appointment is cancelled
   - Title: "Appointment Cancelled"
   - Message includes cancellation reason if provided

5. **notify_appointment_no_show(appointment)**
   - Notifies both users when appointment is marked as no-show
   - Title: "Appointment Marked as No-Show"

6. **notify_low_inventory(medicine, current_stock)**
   - Notifies pharmacy admins when stock falls below threshold
   - Title: "Low Medicine Stock Alert"
   - Message: "{medicine_name} stock is low ({current_stock} units remaining)"

7. **notify_inventory_restocked(medicine)**
   - Notifies interested patients when medicine becomes available
   - Title: "Medicine Now Available"
   - Message: "{medicine_name} is now in stock at {pharmacy_name}"

**Helper Methods:**
- `get_user_notifications(user, limit=50)` - Retrieve user's recent notifications
- `get_user_unread_count(user)` - Count unread notifications
- `is_in_quiet_hours(user)` - Check if notification should be muted
- `_should_notify_user(user, notification_type)` - Check user preferences

## API Endpoints

### 1. List Notifications
```http
GET /api/notifications/
Authorization: Bearer {token}
```

**Query Parameters:**
- `type` - Filter by notification type (e.g., `?type=APPOINTMENT_CONFIRMED`)
- `is_read` - Filter by read status (e.g., `?is_read=false`)

**Response (200 OK):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 2,
      "title": "Appointment Confirmed",
      "message": "Your appointment with Dr. Smith on 2025-01-25 at 10:00 AM is confirmed",
      "notification_type": "APPOINTMENT_CONFIRMED",
      "is_read": false,
      "read_at": null,
      "related_appointment": 5,
      "related_medicine": null,
      "created_at": "2025-01-20T14:30:00Z"
    }
  ]
}
```

### 2. Get Unread Count
```http
GET /api/notifications/unread_count/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "username": "patient_user",
  "unread_count": 3
}
```

### 3. Mark Notification as Read
```http
PATCH /api/notifications/{id}/mark_read/
Authorization: Bearer {token}
Content-Type: application/json

{
  "is_read": true
}
```

**Response (200 OK):**
```json
{
  "detail": "Notification marked as read.",
  "notification": {
    "id": 1,
    "is_read": true,
    "read_at": "2025-01-20T14:35:00Z",
    ...
  }
}
```

### 4. Mark All as Read
```http
POST /api/notifications/mark_all_as_read/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "detail": "Marked 3 notifications as read.",
  "notifications_marked": 3
}
```

### 5. Get Notification Preferences
```http
GET /api/notification-preferences/my_preferences/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 2,
  "appointment_notifications": true,
  "inventory_notifications": true,
  "system_notifications": false,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "enable_quiet_hours": true,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-20T12:00:00Z"
}
```

### 6. Update Notification Preferences
```http
PUT /api/notification-preferences/my_preferences/
Authorization: Bearer {token}
Content-Type: application/json

{
  "appointment_notifications": true,
  "inventory_notifications": false,
  "system_notifications": true,
  "quiet_hours_start": "23:00",
  "quiet_hours_end": "07:00",
  "enable_quiet_hours": true
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 2,
  "appointment_notifications": true,
  "inventory_notifications": false,
  "system_notifications": true,
  "quiet_hours_start": "23:00",
  "quiet_hours_end": "07:00",
  "enable_quiet_hours": true,
  "updated_at": "2025-01-20T14:40:00Z"
}
```

## Integration with Appointment Workflow

Notifications are automatically triggered during appointment state transitions:

### Workflow 1: Appointment Confirmed
```
POST /api/appointments/{id}/confirm/

TRIGGERS:
- notify_appointment_confirmed(appointment)
  ├─ Creates notification for patient
  └─ Creates notification for doctor
```

### Workflow 2: Appointment Completed
```
POST /api/appointments/{id}/complete/

TRIGGERS:
- notify_appointment_completed(appointment)
  ├─ Notifies patient: "Appointment Completed"
  └─ Notifies doctor: "Appointment Completed"
```

### Workflow 3: Appointment Cancelled
```
POST /api/appointments/{id}/cancel/
{
  "reason": "Doctor is unavailable",
  "cancelled_by": "DOCTOR"
}

TRIGGERS:
- notify_appointment_cancelled(appointment, "Doctor is unavailable")
  ├─ Notifies patient with cancellation reason
  └─ Notifies doctor
```

### Workflow 4: Appointment No-Show
```
POST /api/appointments/{id}/no_show/

TRIGGERS:
- notify_appointment_no_show(appointment)
  ├─ Alerts patient about missed appointment
  └─ Alerts doctor about no-show
```

## Quiet Hours Implementation

Users can configure quiet hours to prevent notifications during off-hours (e.g., 10 PM - 8 AM).

**Example Flow:**
```python
# User preferences:
quiet_hours_start: "22:00"  # 10 PM
quiet_hours_end: "08:00"    # 8 AM
enable_quiet_hours: True

# At 11 PM: Notification is muted (stored but not delivered)
# At 9 AM: Notification is delivered
```

**Note:** The quiet hours feature currently stores notifications and delivers them outside quiet hours. Future enhancement: SMS/Email gateway integration can respect these times.

## Access Control

### Permissions

**NotificationViewSet:**
- Only authenticated users can access
- Users can only view their own notifications
- Users can only mark their own notifications as read
- Admin users can view system-wide notifications

**NotificationPreferenceViewSet:**
- Only authenticated users can access
- Users can only modify their own preferences
- Each user has a default preference profile

### Example Error Responses

**User accessing another user's notification:**
```json
{
  "detail": "Not found."
}
```

**Trying to mark another user's notification as read:**
```json
{
  "detail": "You can only mark your own notifications as read."
}
```

## Data Flow Diagram

```
Appointment State Change
        ↓
AppointmentViewSet.confirm/complete/cancel/no_show()
        ↓
NotificationService.notify_appointment_*()
        ↓
Check User Preferences:
  - appointment_notifications enabled?
  - In quiet hours?
  - Notification type allowed?
        ↓
Create Notification Model
  - Set user
  - Set title, message
  - Set notification_type
  - Link to appointment
        ↓
Store in Database
        ↓
Future: Trigger SMS/Email Gateway
(Currently deferred to async task queue)
```

## Implementation Notes

### Low-Bandwidth Design
- Minimal JSON payloads in notification list responses
- Pagination support to limit data transfer
- No nested object serialization (only IDs)

### Rural Compatibility
- Notifications stored offline-first in database
- Sync when connectivity available
- Quiet hours reduce data usage during peak hours

### Extensibility
- NotificationService designed for SMS/Email integration
- Gateway logic can be added without changing views/models
- Async task queue ready for email/SMS delivery

### Future Enhancements
1. **SMS Gateway Integration**: Twilio/AWS SNS for SMS delivery
2. **Email Gateway Integration**: SendGrid/AWS SES for email delivery
3. **Push Notifications**: Firebase Cloud Messaging for mobile apps
4. **Notification Templates**: Customizable message templates by organization
5. **Bulk Notification Campaigns**: Reach multiple users with one action
6. **Notification Analytics**: Track delivery, read rates, engagement

## Testing the Notification System

### Test Scenario 1: Create and Confirm Appointment
```bash
# 1. Login as patient
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "patient1", "password": "pass123"}'

# 2. Create appointment
curl -X POST http://localhost:8000/api/appointments/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 3. Login as doctor
# 4. Confirm appointment
curl -X POST http://localhost:8000/api/appointments/1/confirm/ \
  -H "Authorization: Bearer {doctor_token}"

# 5. Check patient's notifications
curl -X GET http://localhost:8000/api/notifications/ \
  -H "Authorization: Bearer {patient_token}"
```

### Test Scenario 2: Configure Quiet Hours
```bash
# Update notification preferences
curl -X PUT http://localhost:8000/api/notification-preferences/my_preferences/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "enable_quiet_hours": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00"
  }'

# Verify preferences
curl -X GET http://localhost:8000/api/notification-preferences/my_preferences/ \
  -H "Authorization: Bearer {token}"
```

## Common Workflows

### Workflow: Patient Disables Appointment Notifications
```
1. GET /api/notification-preferences/my_preferences/
2. PUT /api/notification-preferences/my_preferences/ with appointment_notifications=false
3. Future appointment confirmations won't create APPOINTMENT_CONFIRMED notifications
```

### Workflow: Check Unread Notifications and Mark as Read
```
1. GET /api/notifications/unread_count/
   → Returns: {"unread_count": 3}
2. GET /api/notifications/?is_read=false
   → Returns list of unread notifications
3. POST /api/notifications/mark_all_as_read/
   → Marks all as read
4. GET /api/notifications/unread_count/
   → Returns: {"unread_count": 0}
```

### Workflow: Filter Appointment Notifications
```
1. GET /api/notifications/?type=APPOINTMENT_CONFIRMED
   → Returns only appointment confirmation notifications
2. PATCH /api/notifications/{id}/mark_read/
   → Mark specific notification as read
```

## Summary

The Notification System provides:
- ✅ Real-time alerts for appointment state changes
- ✅ User-controlled preferences and quiet hours
- ✅ Role-based access control (users see only their notifications)
- ✅ Type-based filtering and statistics
- ✅ Low-bandwidth design for rural environments
- ✅ Extensible architecture for SMS/Email integration
- ✅ Comprehensive API with full CRUD capabilities
- ✅ Integration with existing appointment workflow

All endpoints are protected by JWT authentication and support role-based access control.
