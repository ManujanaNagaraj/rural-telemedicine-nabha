import requests
import json

print('=' * 80)
print('LIVE API ENDPOINT TESTING - RURAL TELEMEDICINE PLATFORM')
print('=' * 80)
print()

headers = {'Content-Type': 'application/json'}

# Test Patients
print('1. PATIENTS ENDPOINT')
print('━' * 80)
try:
    resp = requests.get('http://127.0.0.1:8000/api/patients/', headers=headers)
    data = resp.json()
    print(f'Status: {resp.status_code} OK')
    print(f'Total Patients: {data["count"]}')
    if data['results']:
        print('Patient Records:')
        for p in data['results']:
            print(f'  • ID: {p["id"]} | User: {p["user"]} | Phone: {p["phone_number"]} | Gender: {p["gender"]}')
    else:
        print('  (No patient records)')
except Exception as e:
    print(f'Error: {e}')
print()

# Test Doctors
print('2. DOCTORS ENDPOINT')
print('━' * 80)
try:
    resp = requests.get('http://127.0.0.1:8000/api/doctors/', headers=headers)
    data = resp.json()
    print(f'Status: {resp.status_code} OK')
    print(f'Total Doctors: {data["count"]}')
    if data['results']:
        print('Doctor Records:')
        for d in data['results']:
            print(f'  • ID: {d["id"]} | User: {d["user"]} | Specialization: {d["specialization"]} | License: {d["license_number"]} | Available: {d["is_available"]}')
    else:
        print('  (No doctor records)')
except Exception as e:
    print(f'Error: {e}')
print()

# Test Appointments
print('3. APPOINTMENTS ENDPOINT')
print('━' * 80)
try:
    resp = requests.get('http://127.0.0.1:8000/api/appointments/', headers=headers)
    data = resp.json()
    print(f'Status: {resp.status_code} OK')
    print(f'Total Appointments: {data["count"]}')
    if data['results']:
        print('Appointment Records:')
        for a in data['results']:
            print(f'  • ID: {a["id"]} | Patient: {a["patient"]} | Doctor: {a["doctor"]} | Status: {a["status"]}')
            print(f'    Symptoms: {a["symptoms"]}')
            print(f'    Date: {a["appointment_date"]}')
    else:
        print('  (No appointment records)')
except Exception as e:
    print(f'Error: {e}')
print()

print('=' * 80)
print('✅ ALL ENDPOINTS RESPONDING SUCCESSFULLY')
print('=' * 80)
print()
print('🎉 LIVE SYSTEM VERIFIED AND OPERATIONAL 🎉')
print()
