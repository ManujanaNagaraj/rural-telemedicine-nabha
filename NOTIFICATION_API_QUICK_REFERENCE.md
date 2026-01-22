# Notification System - Quick API Reference

## Quick Start

### 1. Get User's Notifications
```bash
curl -X GET http://localhost:8000/api/notifications/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Get Unread Count
```bash
curl -X GET http://localhost:8000/api/notifications/unread_count/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Mark Notification as Read
```bash
curl -X PATCH http://localhost:8000/api/notifications/1/mark_read/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_read": true}'
```

### 4. Mark All as Read
```bash
curl -X POST http://localhost:8000/api/notifications/mark_all_as_read/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Filter by Type
```bash
curl -X GET "http://localhost:8000/api/notifications/?type=APPOINTMENT_CONFIRMED" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. Filter Unread Only
```bash
curl -X GET "http://localhost:8000/api/notifications/?is_read=false" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 7. Get User Preferences
```bash
curl -X GET http://localhost:8000/api/notification-preferences/my_preferences/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 8. Update User Preferences
```bash
curl -X PUT http://localhost:8000/api/notification-preferences/my_preferences/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "appointment_notifications": true,
    "inventory_notifications": false,
    "system_notifications": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00",
    "enable_quiet_hours": true
  }'
```

## Notification Types

| Type | Description |
|------|-------------|
| APPOINTMENT_CREATED | Appointment scheduled |
| APPOINTMENT_CONFIRMED | Doctor confirmed appointment |
| APPOINTMENT_COMPLETED | Appointment finished |
| APPOINTMENT_CANCELLED | Appointment cancelled |
| APPOINTMENT_NO_SHOW | Patient didn't attend |
| INVENTORY_LOW | Medicine stock low |
| INVENTORY_RESTOCKED | Medicine now available |
| SYSTEM | System/admin message |

## Real-World Workflow

### Step 1: Confirm Appointment (Doctor Side)
```bash
curl -X POST http://localhost:8000/api/appointments/1/confirm/ \
  -H "Authorization: Bearer DOCTOR_TOKEN"
```
**Result:** Creates APPOINTMENT_CONFIRMED notifications for both patient and doctor

### Step 2: Patient Checks Notifications
```bash
curl -X GET http://localhost:8000/api/notifications/ \
  -H "Authorization: Bearer PATIENT_TOKEN"
```
**Response:** Includes new APPOINTMENT_CONFIRMED notification

### Step 3: Patient Marks as Read
```bash
curl -X PATCH http://localhost:8000/api/notifications/1/mark_read/ \
  -H "Authorization: Bearer PATIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_read": true}'
```

## Response Examples

### List Notifications (200 OK)
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 5,
      "title": "Appointment Confirmed",
      "message": "Your appointment with Dr. John Smith on 2025-01-25 at 10:00 AM is confirmed",
      "notification_type": "APPOINTMENT_CONFIRMED",
      "is_read": false,
      "read_at": null,
      "related_appointment": 12,
      "related_medicine": null,
      "created_at": "2025-01-20T10:30:00Z"
    },
    {
      "id": 2,
      "user": 5,
      "title": "Appointment Scheduled",
      "message": "Your appointment has been scheduled for 2025-01-25 at 10:00 AM",
      "notification_type": "APPOINTMENT_CREATED",
      "is_read": true,
      "read_at": "2025-01-20T10:32:00Z",
      "related_appointment": 12,
      "related_medicine": null,
      "created_at": "2025-01-20T10:25:00Z"
    }
  ]
}
```

### Unread Count (200 OK)
```json
{
  "username": "patient_john",
  "unread_count": 2
}
```

### Mark as Read (200 OK)
```json
{
  "detail": "Notification marked as read.",
  "notification": {
    "id": 1,
    "user": 5,
    "title": "Appointment Confirmed",
    "message": "Your appointment with Dr. John Smith on 2025-01-25 at 10:00 AM is confirmed",
    "notification_type": "APPOINTMENT_CONFIRMED",
    "is_read": true,
    "read_at": "2025-01-20T10:35:00Z",
    "related_appointment": 12,
    "related_medicine": null,
    "created_at": "2025-01-20T10:30:00Z"
  }
}
```

### User Preferences (200 OK)
```json
{
  "id": 3,
  "user": 5,
  "appointment_notifications": true,
  "inventory_notifications": true,
  "system_notifications": false,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "enable_quiet_hours": true,
  "created_at": "2025-01-15T09:00:00Z",
  "updated_at": "2025-01-20T14:00:00Z"
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden (Accessing Another User's Notification)
```json
{
  "detail": "Not found."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 400 Bad Request (Invalid Data)
```json
{
  "quiet_hours_start": [
    "Time has wrong format. Use one of these formats instead: HH:MM"
  ]
}
```

## Testing Complete Workflow

### 1. Setup: Create Appointment
```bash
# Login as patient
PATIENT_TOKEN=$(curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "patient1", "password": "pass123"}' | jq -r '.access')

# Create appointment
curl -X POST http://localhost:8000/api/appointments/ \
  -H "Authorization: Bearer $PATIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "doctor": 1,
    "appointment_date": "2025-01-25",
    "appointment_time": "10:00",
    "reason": "Chest pain"
  }'
```

### 2. Doctor Confirms
```bash
# Login as doctor
DOCTOR_TOKEN=$(curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "doctor1", "password": "pass123"}' | jq -r '.access')

# Confirm appointment
curl -X POST http://localhost:8000/api/appointments/1/confirm/ \
  -H "Authorization: Bearer $DOCTOR_TOKEN"
```

### 3. Patient Receives Notification
```bash
# Check notifications
curl -X GET http://localhost:8000/api/notifications/ \
  -H "Authorization: Bearer $PATIENT_TOKEN" | jq '.'

# Result: Should have APPOINTMENT_CONFIRMED notification
```

### 4. Patient Disables Notifications
```bash
# Disable appointment notifications
curl -X PUT http://localhost:8000/api/notification-preferences/my_preferences/ \
  -H "Authorization: Bearer $PATIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"appointment_notifications": false}'

# Future appointment notifications won't be created
```

## Database Info

### Notification Table Structure
```
Table: telemedicine_notification
  - id (PK)
  - user_id (FK)
  - title
  - message
  - notification_type
  - is_read
  - read_at
  - related_appointment_id (FK, nullable)
  - related_medicine_id (FK, nullable)
  - created_at
  
Indexes:
  - (user_id, is_read)
  - (created_at)
```

### NotificationPreference Table Structure
```
Table: telemedicine_notificationpreference
  - id (PK)
  - user_id (FK, UNIQUE)
  - appointment_notifications
  - inventory_notifications
  - system_notifications
  - quiet_hours_start
  - quiet_hours_end
  - enable_quiet_hours
  - created_at
  - updated_at
```

## Performance Notes

- GET /api/notifications/ uses pagination (default 20 per page)
- Indexed queries on user_id and created_at for fast retrieval
- Filtering by type and read status is instant
- Quiet hours checked in-memory (no DB query)
- Supports sorting by most recent first (default)

## Migration Steps

```bash
# 1. Create migrations
python manage.py makemigrations

# 2. Apply migrations
python manage.py migrate

# 3. Test API endpoints
python manage.py test

# 4. Run development server
python manage.py runserver

# 5. Test via curl or Postman
```

## Troubleshooting

**Issue: User doesn't receive notifications**
- Check user preferences: `GET /api/notification-preferences/my_preferences/`
- Check if in quiet hours
- Verify appointment confirmation was called

**Issue: 403 Forbidden when marking notification as read**
- Make sure you're using the correct user's token
- Each user can only modify their own notifications

**Issue: No unread count returned**
- Ensure user is authenticated
- Check if notifications were actually created

---

**For detailed documentation, see: NOTIFICATION_SYSTEM_DOCUMENTATION.md**
