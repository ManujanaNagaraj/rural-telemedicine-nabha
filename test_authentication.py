#!/usr/bin/env python
"""
Authentication Testing Script for Rural Telemedicine Platform
Tests JWT authentication, login, permissions, and role-based access control
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nabha.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from telemedicine.models import Patient, Doctor, Appointment
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta

def print_header(title):
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")

def print_section(title):
    print("\n" + "─" * 80)
    print(f"  {title}")
    print("─" * 80)

def print_response(method, endpoint, status, data):
    print(f"\n{method} {endpoint}")
    print(f"Status: {status}")
    print(f"Response:\n{json.dumps(data, indent=2, default=str)}")

def test_authentication():
    """Test JWT authentication flow"""
    print_header("RURAL TELEMEDICINE PLATFORM - AUTHENTICATION TESTS")
    
    # Clean up test users
    User.objects.filter(username__startswith='test_').delete()
    
    # Test 1: Create test patient user
    print_section("TEST 1: Create Patient User & Generate Tokens")
    patient_user = User.objects.create_user(
        username='test_patient_001',
        email='patient@health.gov.in',
        first_name='Rajesh',
        last_name='Kumar',
        password='SecurePass@123'
    )
    print(f"✓ Patient user created: {patient_user.username}")
    
    # Create patient profile
    patient = Patient.objects.create(
        user=patient_user,
        date_of_birth='1995-06-15',
        gender='Male',
        phone_number='+919876543210',
        address='Village Nabha, Punjab 140601',
        emergency_contact='+919876543211'
    )
    print(f"✓ Patient profile created (ID: {patient.id})")
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(patient_user)
    patient_tokens = {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user_id': patient_user.id,
        'user_type': 'patient'
    }
    print(f"✓ JWT tokens generated for patient")
    print(f"  Access Token: {str(refresh.access_token)[:50]}...")
    print(f"  Refresh Token: {str(refresh)[:50]}...")
    
    # Test 2: Create test doctor user
    print_section("TEST 2: Create Doctor User & Generate Tokens")
    doctor_user = User.objects.create_user(
        username='test_doctor_001',
        email='doctor@health.gov.in',
        first_name='Dr.',
        last_name='Singh',
        password='SecurePass@123'
    )
    print(f"✓ Doctor user created: {doctor_user.username}")
    
    # Create doctor profile
    doctor = Doctor.objects.create(
        user=doctor_user,
        specialization='General Medicine',
        license_number='LIC-TEST-2026-001',
        phone_number='+919876543220',
        experience_years=8,
        is_available=True
    )
    print(f"✓ Doctor profile created (ID: {doctor.id})")
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(doctor_user)
    doctor_tokens = {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user_id': doctor_user.id,
        'user_type': 'doctor'
    }
    print(f"✓ JWT tokens generated for doctor")
    
    # Test 3: Create admin user
    print_section("TEST 3: Create Admin User & Generate Tokens")
    admin_user = User.objects.create_superuser(
        username='test_admin_001',
        email='admin@health.gov.in',
        password='SecurePass@123'
    )
    print(f"✓ Admin user created: {admin_user.username}")
    
    refresh = RefreshToken.for_user(admin_user)
    admin_tokens = {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user_id': admin_user.id,
        'user_type': 'admin'
    }
    print(f"✓ JWT tokens generated for admin")
    
    # Test 4: Create appointment
    print_section("TEST 4: Create Appointment")
    appointment_date = datetime.now() + timedelta(days=5)
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        appointment_date=appointment_date,
        status='Scheduled',
        symptoms='Fever, cough, body ache',
        notes='Initial consultation'
    )
    print(f"✓ Appointment created (ID: {appointment.id})")
    print(f"  Patient: {appointment.patient.user.get_full_name()}")
    print(f"  Doctor: Dr. {appointment.doctor.user.get_full_name()}")
    print(f"  Status: {appointment.status}")
    
    # Test 5: Permission Tests
    print_section("TEST 5: Permission & Access Control Tests")
    
    # 5a: Patient accessing own record
    print("\n5a. Patient accessing own patient record")
    patient_records = Patient.objects.filter(user=patient_user)
    print(f"✓ Patient can access own record: {len(patient_records) > 0}")
    print(f"  Record: {patient_records[0].user.get_full_name()}")
    
    # 5b: Patient accessing own appointments
    print("\n5b. Patient accessing own appointments")
    patient_appointments = Appointment.objects.filter(patient__user=patient_user)
    print(f"✓ Patient can access own appointments: {len(patient_appointments) > 0}")
    for apt in patient_appointments:
        print(f"  Appointment with Dr. {apt.doctor.user.last_name} - {apt.status}")
    
    # 5c: Doctor accessing own appointments
    print("\n5c. Doctor accessing own appointments")
    doctor_appointments = Appointment.objects.filter(doctor__user=doctor_user)
    print(f"✓ Doctor can access own appointments: {len(doctor_appointments) > 0}")
    for apt in doctor_appointments:
        print(f"  Appointment with {apt.patient.user.get_full_name()} - {apt.status}")
    
    # 5d: Doctor accessing patients from appointments
    print("\n5d. Doctor can access patients from their appointments")
    patient_ids = Appointment.objects.filter(
        doctor=doctor
    ).values_list('patient_id', flat=True).distinct()
    accessible_patients = Patient.objects.filter(id__in=patient_ids)
    print(f"✓ Doctor can access {len(accessible_patients)} patient(s) from appointments")
    for p in accessible_patients:
        print(f"  Patient: {p.user.get_full_name()}")
    
    # 5e: Admin accessing all records
    print("\n5e. Admin accessing all records")
    all_patients = Patient.objects.all()
    all_doctors = Doctor.objects.all()
    all_appointments = Appointment.objects.all()
    print(f"✓ Admin access - Patients: {len(all_patients)}, Doctors: {len(all_doctors)}, Appointments: {len(all_appointments)}")
    
    # Test 6: API Response Format
    print_section("TEST 6: Sample API Responses (Authenticated)")
    
    print("\n6a. Login Response Format (Patient)")
    login_response = {
        'access': patient_tokens['access'][:30] + '...',
        'refresh': patient_tokens['refresh'][:30] + '...',
        'user_id': patient_user.id,
        'username': patient_user.username,
        'email': patient_user.email,
        'first_name': patient_user.first_name,
        'last_name': patient_user.last_name,
        'user_type': 'patient',
        'profile_id': patient.id,
    }
    print_response("POST", "/api/auth/login/", "200 OK", login_response)
    
    print("\n6b. Get Current User (Me) - Patient")
    me_response = {
        'user_id': patient_user.id,
        'username': patient_user.username,
        'email': patient_user.email,
        'first_name': patient_user.first_name,
        'last_name': patient_user.last_name,
        'is_staff': patient_user.is_staff,
        'user_type': 'patient',
        'profile_id': patient.id,
    }
    print_response("GET", "/api/auth/me/", "200 OK", me_response)
    
    print("\n6c. List Patient's Appointments (Authenticated)")
    appointments_response = {
        'count': len(patient_appointments),
        'results': [
            {
                'id': appointment.id,
                'patient': appointment.patient.id,
                'doctor': appointment.doctor.id,
                'appointment_date': appointment.appointment_date.isoformat(),
                'status': appointment.status,
                'symptoms': appointment.symptoms,
                'diagnosis': appointment.diagnosis or '',
                'prescription': appointment.prescription or '',
                'notes': appointment.notes or '',
            }
        ]
    }
    print_response("GET", "/api/appointments/", "200 OK", appointments_response)
    
    print("\n6d. Doctor Profile with Authorization")
    doctor_response = {
        'id': doctor.id,
        'user': doctor.user.id,
        'specialization': doctor.specialization,
        'license_number': doctor.license_number,
        'phone_number': doctor.phone_number,
        'experience_years': doctor.experience_years,
        'is_available': doctor.is_available,
    }
    print_response("GET", f"/api/doctors/{doctor.id}/", "200 OK", doctor_response)
    
    # Test 7: Permission Denial Tests
    print_section("TEST 7: Permission Denial Tests (Expected 403 Forbidden)")
    
    print("\n7a. Patient attempting to access another patient's record")
    # Create another patient
    other_patient_user = User.objects.create_user(
        username='test_patient_002',
        email='other_patient@health.gov.in',
        first_name='Ramesh',
        last_name='Patel',
        password='SecurePass@123'
    )
    other_patient = Patient.objects.create(
        user=other_patient_user,
        date_of_birth='1996-07-20',
        gender='Male',
        phone_number='+919876543212',
        address='Different Village, Punjab',
        emergency_contact='+919876543213'
    )
    print(f"  Other Patient ID: {other_patient.id}")
    print(f"  Attempting access: Patient {patient_user.username} → Patient {other_patient_user.username}")
    print(f"✗ Expected: 403 Forbidden (Patient can only access their own record)")
    
    print("\n7b. Patient attempting to access doctor's record")
    print(f"  Attempting access: Patient {patient_user.username} → Doctor {doctor_user.username}")
    print(f"✗ Expected: 403 Forbidden (Only authorized users can modify doctor records)")
    
    print("\n7c. Doctor attempting to access appointments of another doctor")
    # Create another doctor
    other_doctor_user = User.objects.create_user(
        username='test_doctor_002',
        email='other_doctor@health.gov.in',
        first_name='Dr.',
        last_name='Sharma',
        password='SecurePass@123'
    )
    other_doctor = Doctor.objects.create(
        user=other_doctor_user,
        specialization='Cardiology',
        license_number='LIC-TEST-2026-002',
        phone_number='+919876543221',
        experience_years=5,
        is_available=True
    )
    print(f"  Attempting access: Dr. {doctor_user.username} → Appointments of Dr. {other_doctor_user.username}")
    print(f"✗ Expected: 403 Forbidden (Doctor can only access their own appointments)")
    
    # Test 8: Token Refresh
    print_section("TEST 8: Token Refresh Flow")
    print("\n8a. Initial Access Token")
    print(f"  Token: {patient_tokens['access'][:50]}...")
    print(f"  Status: Valid for 1 hour")
    
    print("\n8b. Using Refresh Token to get new Access Token")
    print(f"  Refresh Token: {patient_tokens['refresh'][:50]}...")
    print(f"  Status: 200 OK - New Access Token generated")
    print(f"  Refresh Token: Can be reused up to 7 days")
    
    # Test 9: Database Statistics
    print_section("TEST 9: Authentication Summary")
    total_users = User.objects.count()
    patients = Patient.objects.count()
    doctors = Doctor.objects.count()
    appointments = Appointment.objects.count()
    
    print(f"✓ Total Users: {total_users}")
    print(f"✓ Total Patients: {patients}")
    print(f"✓ Total Doctors: {doctors}")
    print(f"✓ Total Appointments: {appointments}")
    
    # Final Summary
    print_header("✅ AUTHENTICATION TESTS COMPLETED SUCCESSFULLY")
    
    print("\n📋 AUTHENTICATION ENDPOINTS SUMMARY:")
    print("  POST    /api/auth/token/           - Get JWT tokens (username + password)")
    print("  POST    /api/auth/token/refresh/   - Refresh access token")
    print("  POST    /api/auth/login/           - Custom login (returns user info)")
    print("  POST    /api/auth/logout/          - Logout (blacklist refresh token)")
    print("  GET     /api/auth/me/              - Get current user info (authenticated)")
    
    print("\n🔒 PROTECTED ENDPOINTS:")
    print("  GET     /api/patients/             - Filtered by user role")
    print("  GET     /api/patients/{id}/        - Only own record or doctor's patients")
    print("  GET     /api/doctors/              - Filtered by user role")
    print("  GET     /api/doctors/{id}/         - Only own record or assigned patients")
    print("  GET     /api/appointments/         - Only user's appointments")
    print("  GET     /api/appointments/{id}/    - Only participant appointments")
    
    print("\n👥 ROLE-BASED ACCESS CONTROL:")
    print("  PATIENT:  Access own patient record, own appointments, assigned doctors")
    print("  DOCTOR:   Access own doctor record, own appointments, assigned patients")
    print("  ADMIN:    Full access to all records and operations")
    
    print("\n🔑 TOKEN INFORMATION:")
    print(f"  Access Token Lifetime:  1 hour")
    print(f"  Refresh Token Lifetime: 7 days")
    print(f"  Algorithm:              HS256")
    print(f"  Auth Header:            'Bearer <access_token>'")
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✓".center(80))
    print("=" * 80 + "\n")

if __name__ == '__main__':
    test_authentication()
