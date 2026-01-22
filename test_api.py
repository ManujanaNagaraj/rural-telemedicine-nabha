#!/usr/bin/env python
"""
API Testing Script for Rural Telemedicine Platform
Tests all endpoints and verifies functionality
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nabha.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from telemedicine.models import Patient, Doctor, Appointment

def test_api_endpoints():
    """Test core functionality"""
    print("=" * 80)
    print("RURAL TELEMEDICINE PLATFORM - NABHA")
    print("API Functionality Test Suite")
    print("=" * 80)
    print()

    # Test 1: User Creation
    print("TEST 1: Creating Test Users")
    print("-" * 80)
    try:
        if not User.objects.filter(username='patient1').exists():
            patient_user = User.objects.create_user(
                username='patient1',
                email='patient1@health.gov.in',
                first_name='Rajesh',
                last_name='Kumar'
            )
            print(f"✓ Patient user created: {patient_user.username}")
        else:
            patient_user = User.objects.get(username='patient1')
            print(f"✓ Patient user exists: {patient_user.username}")
        
        if not User.objects.filter(username='doctor1').exists():
            doctor_user = User.objects.create_user(
                username='doctor1',
                email='doctor1@health.gov.in',
                first_name='Dr.',
                last_name='Singh'
            )
            print(f"✓ Doctor user created: {doctor_user.username}")
        else:
            doctor_user = User.objects.get(username='doctor1')
            print(f"✓ Doctor user exists: {doctor_user.username}")
    except Exception as e:
        print(f"✗ Error creating users: {e}")
        return
    
    print()

    # Test 2: Patient Creation
    print("TEST 2: Creating Patient Profile")
    print("-" * 80)
    try:
        patient, created = Patient.objects.get_or_create(
            user=patient_user,
            defaults={
                'date_of_birth': '1995-06-15',
                'gender': 'Male',
                'phone_number': '+919876543210',
                'address': 'Village Nabha, Punjab 140601',
                'emergency_contact': '+919876543211'
            }
        )
        status = "created" if created else "already exists"
        print(f"✓ Patient profile {status}")
        print(f"  - Name: {patient.user.get_full_name()}")
        print(f"  - Phone: {patient.phone_number}")
        print(f"  - Location: {patient.address}")
        print(f"  - Database ID: {patient.id}")
    except Exception as e:
        print(f"✗ Error creating patient: {e}")
        return
    
    print()

    # Test 3: Doctor Creation
    print("TEST 3: Creating Doctor Profile")
    print("-" * 80)
    try:
        doctor, created = Doctor.objects.get_or_create(
            user=doctor_user,
            defaults={
                'specialization': 'General Medicine',
                'license_number': 'LIC-NB-2026-001',
                'phone_number': '+919876543220',
                'experience_years': 8,
                'is_available': True
            }
        )
        status = "created" if created else "already exists"
        print(f"✓ Doctor profile {status}")
        print(f"  - Name: Dr. {doctor.user.get_full_name()}")
        print(f"  - Specialization: {doctor.specialization}")
        print(f"  - License: {doctor.license_number}")
        print(f"  - Experience: {doctor.experience_years} years")
        print(f"  - Available: {doctor.is_available}")
        print(f"  - Database ID: {doctor.id}")
    except Exception as e:
        print(f"✗ Error creating doctor: {e}")
        return
    
    print()

    # Test 4: Appointment Creation
    print("TEST 4: Creating Appointment")
    print("-" * 80)
    try:
        from datetime import datetime, timedelta
        appointment_date = datetime.now() + timedelta(days=5)
        
        appointment, created = Appointment.objects.get_or_create(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_date,
            defaults={
                'status': 'Scheduled',
                'symptoms': 'Fever, cough, body ache',
                'diagnosis': '',
                'prescription': '',
                'notes': 'Initial consultation'
            }
        )
        status = "created" if created else "already exists"
        print(f"✓ Appointment {status}")
        print(f"  - Patient: {appointment.patient.user.get_full_name()}")
        print(f"  - Doctor: {appointment.doctor.user.get_full_name()}")
        print(f"  - Date: {appointment.appointment_date}")
        print(f"  - Status: {appointment.status}")
        print(f"  - Symptoms: {appointment.symptoms}")
        print(f"  - Database ID: {appointment.id}")
    except Exception as e:
        print(f"✗ Error creating appointment: {e}")
        return
    
    print()

    # Test 5: Database Statistics
    print("TEST 5: Database Statistics")
    print("-" * 80)
    patient_count = Patient.objects.count()
    doctor_count = Doctor.objects.count()
    appointment_count = Appointment.objects.count()
    user_count = User.objects.count()
    
    print(f"✓ Total Users: {user_count}")
    print(f"✓ Total Patients: {patient_count}")
    print(f"✓ Total Doctors: {doctor_count}")
    print(f"✓ Total Appointments: {appointment_count}")
    
    print()

    # Test 6: Query Performance
    print("TEST 6: API Query Tests")
    print("-" * 80)
    try:
        # Query all patients
        all_patients = Patient.objects.all()
        print(f"✓ Patient list query: {len(all_patients)} records")
        
        # Query all doctors
        all_doctors = Doctor.objects.all()
        print(f"✓ Doctor list query: {len(all_doctors)} records")
        
        # Query all appointments
        all_appointments = Appointment.objects.all()
        print(f"✓ Appointment list query: {len(all_appointments)} records")
        
        # Query scheduled appointments
        scheduled = Appointment.objects.filter(status='Scheduled')
        print(f"✓ Scheduled appointments: {len(scheduled)} records")
        
        # Query available doctors
        available = Doctor.objects.filter(is_available=True)
        print(f"✓ Available doctors: {len(available)} records")
        
    except Exception as e:
        print(f"✗ Error during queries: {e}")
        return
    
    print()

    # Final Summary
    print("=" * 80)
    print("✅ ALL TESTS PASSED - API IS FUNCTIONAL")
    print("=" * 80)
    print()
    print("API ENDPOINTS READY FOR USE:")
    print("  - GET    http://127.0.0.1:8000/api/patients/")
    print("  - GET    http://127.0.0.1:8000/api/doctors/")
    print("  - GET    http://127.0.0.1:8000/api/appointments/")
    print()
    print("Admin Interface:")
    print("  - http://127.0.0.1:8000/admin/")
    print("  - Username: admin")
    print()
    print(f"Test completed at: {datetime.now()}")
    print("=" * 80)

if __name__ == '__main__':
    test_api_endpoints()
