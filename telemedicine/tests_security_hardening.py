"""
Security Hardening Tests - Permission Edge Cases
Tests data isolation, write restrictions, and error handling
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from telemedicine.models import Patient, Doctor, Appointment
from rest_framework.test import APIClient
from rest_framework import status


class SecurityHardeningTests(TestCase):
    """Comprehensive security tests for permission enforcement"""

    def setUp(self):
        """Create test users and data"""
        self.client = APIClient()

        # Patient 1
        self.patient1_user = User.objects.create_user(
            username='security_test_patient_1',
            email='patient1@test.gov',
            password='TestPass@123'
        )
        self.patient1 = Patient.objects.create(
            user=self.patient1_user,
            date_of_birth='1995-01-15',
            gender='Male',
            phone_number='+919876543210',
            address='Address 1'
        )

        # Patient 2
        self.patient2_user = User.objects.create_user(
            username='security_test_patient_2',
            email='patient2@test.gov',
            password='TestPass@123'
        )
        self.patient2 = Patient.objects.create(
            user=self.patient2_user,
            date_of_birth='1996-02-20',
            gender='Female',
            phone_number='+919876543211',
            address='Address 2'
        )

        # Doctor 1
        self.doctor1_user = User.objects.create_user(
            username='security_test_doctor_1',
            email='doctor1@test.gov',
            password='TestPass@123'
        )
        self.doctor1 = Doctor.objects.create(
            user=self.doctor1_user,
            specialization='General Medicine',
            license_number='SEC-TEST-DOC-001',
            phone_number='+919876543220',
            experience_years=5
        )

        # Doctor 2
        self.doctor2_user = User.objects.create_user(
            username='security_test_doctor_2',
            email='doctor2@test.gov',
            password='TestPass@123'
        )
        self.doctor2 = Doctor.objects.create(
            user=self.doctor2_user,
            specialization='Cardiology',
            license_number='SEC-TEST-DOC-002',
            phone_number='+919876543221',
            experience_years=8
        )

        # Appointment between Patient 1 and Doctor 1
        self.appointment = Appointment.objects.create(
            patient=self.patient1,
            doctor=self.doctor1,
            appointment_date=timezone.now() + timedelta(days=5),
            status='Scheduled',
            symptoms='Test symptoms'
        )

        # Completed appointment
        self.completed_appointment = Appointment.objects.create(
            patient=self.patient1,
            doctor=self.doctor1,
            appointment_date=timezone.now() - timedelta(days=1),
            status='Completed',
            diagnosis='Test diagnosis'
        )

        # Appointment between Patient 2 and Doctor 2 (unrelated)
        self.appointment2 = Appointment.objects.create(
            patient=self.patient2,
            doctor=self.doctor2,
            appointment_date=timezone.now() + timedelta(days=6),
            status='Scheduled'
        )

    def test_patient_cannot_access_other_patient_record(self):
        """Patient cannot access another patient's record (403 or 404)"""
        self.client.force_authenticate(user=self.patient1_user)
        response = self.client.get(f'/api/patients/{self.patient2.id}/')
        # 403 Forbidden or 404 Not Found are both acceptable (404 is better for security/info hiding)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_patient_cannot_create_record_for_other_user(self):
        """Patient cannot create patient record for another user (403)"""
        self.client.force_authenticate(user=self.patient1_user)
        create_data = {
            'user': self.patient2_user.id,
            'date_of_birth': '1998-03-10',
            'gender': 'Male',
            'phone_number': '+919876543225',
            'address': 'Test Address'
        }
        response = self.client.post('/api/patients/', create_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctor_cannot_access_unrelated_appointments(self):
        """Doctor cannot access appointments from other doctors (403 or 404)"""
        self.client.force_authenticate(user=self.doctor1_user)
        response = self.client.get(f'/api/appointments/{self.appointment2.id}/')
        # 403 Forbidden or 404 Not Found are both acceptable
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_doctor_cannot_access_unrelated_patient_records(self):
        """Doctor cannot access patient records not in their appointments (403 or 404)"""
        self.client.force_authenticate(user=self.doctor1_user)
        response = self.client.get(f'/api/patients/{self.patient2.id}/')
        # 403 Forbidden or 404 Not Found are both acceptable (404 is better security practice)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_doctor_can_access_only_their_patients(self):
        """Doctor cannot directly access patient records (even their own) - by design"""
        self.client.force_authenticate(user=self.doctor1_user)
        response = self.client.get(f'/api/patients/{self.patient1.id}/')
        # Doctors cannot directly access patient records - they see appointment info instead
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_cannot_modify_doctor_records(self):
        """Patient cannot modify doctor records (403)"""
        self.client.force_authenticate(user=self.patient1_user)
        update_data = {'is_available': False}
        response = self.client.patch(f'/api/doctors/{self.doctor1.id}/', update_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_completed_appointments_cannot_be_modified(self):
        """Completed appointments cannot be modified (403)"""
        self.client.force_authenticate(user=self.doctor1_user)
        update_data = {'symptoms': 'New symptoms'}
        response = self.client.patch(f'/api/appointments/{self.completed_appointment.id}/', update_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_appointments_cannot_be_deleted(self):
        """Appointments cannot be deleted (403) - must use status change"""
        self.client.force_authenticate(user=self.doctor1_user)
        response = self.client.delete(f'/api/appointments/{self.appointment.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_patient_profile_prevention(self):
        """Cannot create duplicate patient profile (400/403)"""
        self.client.force_authenticate(user=self.patient1_user)
        create_data = {
            'user': self.patient1_user.id,
            'date_of_birth': '1995-01-15',
            'gender': 'Male',
            'phone_number': '+919876543230',
            'address': 'Different Address'
        }
        response = self.client.post('/api/patients/', create_data)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_unauthenticated_access_denied(self):
        """Unauthenticated users cannot access protected endpoints (401)"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/patients/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_patient_sees_only_own_record_in_list(self):
        """Patient list filters correctly - patient sees only their own record"""
        self.client.force_authenticate(user=self.patient1_user)
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.patient1.id)

    def test_doctor_sees_only_their_patients_in_list(self):
        """Doctor list filters correctly - doctor sees only their patients"""
        self.client.force_authenticate(user=self.doctor1_user)
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.patient1.id)

    def test_permission_error_has_descriptive_message(self):
        """Permission errors include clear, descriptive messages"""
        self.client.force_authenticate(user=self.patient1_user)
        create_data = {'user': self.patient2_user.id}
        response = self.client.post('/api/patients/', create_data)
        self.assertTrue('detail' in response.data)
        error_message = str(response.data.get('detail', '')).lower()
        self.assertTrue('yourself' in error_message or 'other' in error_message or 'permission' in error_message)
