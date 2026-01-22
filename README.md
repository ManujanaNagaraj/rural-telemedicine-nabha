# Rural Telemedicine Platform - Nabha

## Project Overview
A production-grade Django REST Framework backend for a government healthcare telemedicine platform serving rural areas in India, specifically the Nabha region.

## Tech Stack
- **Backend**: Django 6.0.1
- **API Framework**: Django REST Framework
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Authentication**: Session & Basic Authentication
- **CORS**: Enabled for Flutter mobile app integration

## Installation & Setup

### Prerequisites
- Python 3.8+
- Virtual Environment

### Steps to Run

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install django djangorestframework django-cors-headers psycopg2-binary

# 3. Run migrations
python manage.py makemigrations
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Start development server
python manage.py runserver
```

## API Endpoints

### Patients
- `GET /api/patients/` - List all patients
- `POST /api/patients/` - Create a new patient
- `GET /api/patients/{id}/` - Retrieve patient details
- `PUT /api/patients/{id}/` - Update patient
- `DELETE /api/patients/{id}/` - Delete patient

### Doctors
- `GET /api/doctors/` - List all doctors
- `POST /api/doctors/` - Create a new doctor
- `GET /api/doctors/{id}/` - Retrieve doctor details
- `PUT /api/doctors/{id}/` - Update doctor
- `DELETE /api/doctors/{id}/` - Delete doctor

### Appointments
- `GET /api/appointments/` - List all appointments
- `POST /api/appointments/` - Schedule an appointment
- `GET /api/appointments/{id}/` - Retrieve appointment details
- `PUT /api/appointments/{id}/` - Update appointment
- `DELETE /api/appointments/{id}/` - Cancel appointment

## Admin Interface
Access: `http://localhost:8000/admin/`
- Username: admin
- Use Django admin to manage users, patients, doctors, and appointments

## Database Models

### Patient
- User (OneToOne)
- Date of Birth
- Gender
- Phone Number
- Address
- Emergency Contact

### Doctor
- User (OneToOne)
- Specialization
- License Number (Unique)
- Phone Number
- Years of Experience
- Availability Status

### Appointment
- Patient (ForeignKey)
- Doctor (ForeignKey)
- Appointment Date/Time
- Status (Scheduled, Completed, Cancelled, No-show)
- Symptoms
- Diagnosis
- Prescription
- Notes

## Security Notes
- CORS enabled for Flutter app development
- Change SECRET_KEY in production
- Use PostgreSQL for production
- Implement JWT authentication for production
- Enable HTTPS in production

## Development Notes
- DEBUG = True (Development only)
- AllowAny permissions (Development only)
- Replace with proper authentication in production

## Project Structure
```
rural-telemedicine-platform/
├── nabha/                    # Project configuration
│   ├── settings.py          # Project settings
│   ├── urls.py              # Main URL routing
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
├── telemedicine/            # Main app
│   ├── models.py            # Data models
│   ├── views.py             # API views
│   ├── serializers.py       # Serializers
│   ├── urls.py              # App URL routing
│   ├── migrations/          # Database migrations
│   └── admin.py             # Admin configuration
├── manage.py                # Django management script
└── db.sqlite3              # SQLite database (dev)
```

## Future Enhancements
- JWT Token Authentication
- Video/Audio Consultation (WebRTC)
- AI-based Symptom Analysis
- SMS/Email Notifications
- Prescription Management
- Payment Integration
- Advanced Reporting & Analytics
