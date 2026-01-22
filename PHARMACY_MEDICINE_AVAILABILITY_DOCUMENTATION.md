# Pharmacy & Medicine Availability Module
## Rural Telemedicine Platform – Nabha

**Status**: ✅ COMPLETE  
**Date**: 2026-01-22  
**Focus**: Healthcare supply chain for rural areas with low internet availability

---

## 📋 **FILES CREATED / MODIFIED**

| File | Type | Changes |
|------|------|---------|
| [telemedicine/models.py](telemedicine/models.py) | Modified | Added Pharmacy, Medicine, PharmacyInventory models |
| [telemedicine/serializers.py](telemedicine/serializers.py) | Modified | Added 5 serializers for pharmacy operations |
| [telemedicine/views.py](telemedicine/views.py) | Modified | Added 3 ViewSets with 5 custom endpoints |
| [telemedicine/urls.py](telemedicine/urls.py) | Modified | Registered new pharmacy endpoints |

---

## 🎯 **FEATURES IMPLEMENTED**

### **1. Pharmacy Model** ✅
```python
- name: Pharmacy name
- location: Village/area name (for rural identification)
- contact_number: Phone for availability queries
- address: Detailed location info
- is_active: Operational status
- created_at, updated_at: Audit fields
```

### **2. Medicine Model** ✅
```python
- name: Medicine name (unique)
- description: Dosage, uses, precautions
- is_prescription_required: Boolean flag
- created_at, updated_at: Audit fields
```

### **3. PharmacyInventory Model** ✅
```python
- pharmacy: FK to Pharmacy
- medicine: FK to Medicine
- quantity_available: Stock quantity (>= 0)
- last_updated: When stock was last changed
- created_at: When record was created
- Unique constraint: pharmacy + medicine
- Methods:
  - is_available(): Check if stock > 0
  - update_quantity(qty): Set quantity
  - add_stock(qty): Increase stock
  - remove_stock(qty): Decrease stock (safe)
```

### **4. Inventory Validation** ✅
```python
- No negative quantities
- Atomic stock operations
- Clear error messages
- Audit trail on updates
```

### **5. Access Control** ✅
```python
- Public data: View medicines and pharmacies
- Authenticated: View availability
- Admin/Pharmacy: Update inventory
- Role-based permissions
```

---

## 📡 **API ENDPOINTS**

### **1. List Medicines**
```
GET /api/medicines/
GET /api/medicines/?search=paracetamol
GET /api/medicines/?is_prescription_required=true

Response (200 OK):
{
  "count": 50,
  "next": "http://localhost:8000/api/medicines/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Paracetamol",
      "description": "Analgesic and antipyretic",
      "is_prescription_required": false,
      "available_pharmacies_count": 8,
      "created_at": "2026-01-22T09:00:00Z",
      "updated_at": "2026-01-22T09:00:00Z"
    }
  ]
}
```

### **2. Get Medicine Details**
```
GET /api/medicines/1/

Response (200 OK):
{
  "id": 1,
  "name": "Paracetamol",
  "description": "Analgesic and antipyretic. Typical dose: 500-1000mg",
  "is_prescription_required": false,
  "available_pharmacies_count": 8,
  "created_at": "2026-01-22T09:00:00Z",
  "updated_at": "2026-01-22T09:00:00Z"
}
```

### **3. List Active Pharmacies**
```
GET /api/pharmacies/
GET /api/pharmacies/?location=Village%20A
GET /api/pharmacies/?search=Central

Response (200 OK):
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "name": "Central Pharmacy",
      "location": "Main Market, Village A",
      "contact_number": "9876543210",
      "address": "Opp. Hospital, Main Market",
      "is_active": true,
      "available_medicines_count": 35,
      "created_at": "2026-01-15T08:00:00Z",
      "updated_at": "2026-01-22T10:00:00Z"
    }
  ]
}
```

### **4. Get Pharmacy Details with Inventory**
```
GET /api/pharmacies/2/

Response (200 OK):
{
  "id": 2,
  "name": "Central Pharmacy",
  "location": "Main Market, Village A",
  "contact_number": "9876543210",
  "address": "Opp. Hospital, Main Market",
  "is_active": true,
  "available_medicines_count": 35,
  "created_at": "2026-01-15T08:00:00Z",
  "updated_at": "2026-01-22T10:00:00Z"
}
```

### **5. List Available Medicines (Active Pharmacies Only)**
```
GET /api/pharmacy-inventory/

Response (200 OK):
{
  "count": 280,
  "next": "http://localhost:8000/api/pharmacy-inventory/?page=2",
  "previous": null,
  "results": [
    {
      "id": 15,
      "pharmacy": 2,
      "pharmacy_name": "Central Pharmacy",
      "pharmacy_location": "Main Market, Village A",
      "medicine": 1,
      "medicine_name": "Paracetamol",
      "is_prescription_required": false,
      "quantity_available": 45,
      "is_available": true,
      "last_updated": "2026-01-22T10:00:00Z",
      "created_at": "2026-01-15T08:00:00Z"
    }
  ]
}
```

### **6. Get Availability of Specific Medicine**
```
GET /api/pharmacy-inventory/by_medicine/?medicine_id=1

Response (200 OK):
{
  "medicine_id": 1,
  "medicine_name": "Paracetamol",
  "is_prescription_required": false,
  "pharmacies": [
    {
      "pharmacy_id": 2,
      "pharmacy_name": "Central Pharmacy",
      "location": "Main Market, Village A",
      "contact_number": "9876543210",
      "quantity_available": 45,
      "last_updated": "2026-01-22T10:00:00Z"
    },
    {
      "pharmacy_id": 3,
      "pharmacy_name": "Health Mart",
      "location": "Sub-Market, Village B",
      "contact_number": "9876543211",
      "quantity_available": 22,
      "last_updated": "2026-01-22T09:30:00Z"
    }
  ],
  "total_available_at": 2
}
```

### **7. Get All Medicines at Specific Pharmacy**
```
GET /api/pharmacy-inventory/by_pharmacy/?pharmacy_id=2

Response (200 OK):
{
  "pharmacy_id": 2,
  "pharmacy_name": "Central Pharmacy",
  "pharmacy_location": "Main Market, Village A",
  "pharmacy_contact": "9876543210",
  "medicines": [
    {
      "id": 15,
      "pharmacy": 2,
      "pharmacy_name": "Central Pharmacy",
      "pharmacy_location": "Main Market, Village A",
      "medicine": 1,
      "medicine_name": "Paracetamol",
      "is_prescription_required": false,
      "quantity_available": 45,
      "is_available": true,
      "last_updated": "2026-01-22T10:00:00Z",
      "created_at": "2026-01-15T08:00:00Z"
    },
    {
      "id": 16,
      "pharmacy": 2,
      "pharmacy_name": "Central Pharmacy",
      "pharmacy_location": "Main Market, Village A",
      "medicine": 2,
      "medicine_name": "Aspirin",
      "is_prescription_required": false,
      "quantity_available": 32,
      "is_available": true,
      "last_updated": "2026-01-22T10:00:00Z",
      "created_at": "2026-01-15T08:00:00Z"
    }
  ]
}
```

### **8. Update Inventory Quantity (Admin/Pharmacy Staff)**
```
PATCH /api/pharmacy-inventory/15/update_quantity/

Request Body:
{
  "quantity": 50,
  "reason": "Restock from distributor"
}

Response (200 OK):
{
  "detail": "Inventory updated successfully",
  "medicine": "Paracetamol",
  "pharmacy": "Central Pharmacy",
  "new_quantity": 50
}

Error Response (400):
{
  "detail": "Quantity cannot be negative."
}

Error Response (403):
{
  "detail": "Only admin and pharmacy staff can update inventory."
}
```

---

## 🧪 **SAMPLE API WORKFLOWS**

### **Workflow 1: Patient Searches for Medicine Availability**

```bash
# Step 1: Get list of medicines
GET /api/medicines/?search=paracetamol

# Step 2: Find which pharmacies have it
GET /api/pharmacy-inventory/by_medicine/?medicine_id=1

# Step 3: Contact nearest pharmacy
# Response shows location, phone, quantity
```

---

### **Workflow 2: Pharmacy Updates Stock**

```bash
# Step 1: Pharmacy admin logs in
POST /api/auth/login/ (with pharmacy admin credentials)

# Step 2: Update inventory after restocking
PATCH /api/pharmacy-inventory/15/update_quantity/
{
  "quantity": 100,
  "reason": "Distributor delivery"
}

# Step 3: Patients see updated availability
GET /api/pharmacy-inventory/by_medicine/?medicine_id=1
```

---

### **Workflow 3: Rural Area Stock Check**

```bash
# Step 1: Find pharmacies in specific area
GET /api/pharmacies/?location=Village%20A

# Step 2: Get all medicines at that pharmacy
GET /api/pharmacy-inventory/by_pharmacy/?pharmacy_id=2

# Step 3: Make informed purchase decision
```

---

## 📊 **SAMPLE DATA SCENARIOS**

### **Scenario 1: Common Over-the-Counter Medicine**
```json
{
  "id": 1,
  "name": "Paracetamol",
  "is_prescription_required": false,
  "available_at": 8,  // pharmacies
  "locations": ["Village A", "Village B", "Town Center"]
}
```

### **Scenario 2: Prescription Required Medicine**
```json
{
  "id": 12,
  "name": "Amoxicillin 500mg",
  "is_prescription_required": true,
  "available_at": 3,  // fewer pharmacies
  "locations": ["Main Town", "Hospital Area"]
}
```

### **Scenario 3: Low Stock Alert**
```json
{
  "id": 1,
  "medicine": "Paracetamol",
  "pharmacy": "Central Pharmacy",
  "quantity_available": 2,  // Low!
  "status": "Need restock soon"
}
```

---

## 🌐 **RURAL DESIGN CONSIDERATIONS**

### **Low Internet Availability**
```
✓ Endpoints designed for minimal data transfer
✓ Compact JSON responses
✓ Pagination built-in for large datasets
✓ Can be cached locally on devices
✓ Async sync capability for offline-first apps
```

### **Offline-First Architecture**
```
Pharmacy staff can:
1. Update inventory locally
2. Sync when internet available
3. Use PharmacyInventory model as local cache
```

### **Access Pattern Optimization**
```
- Users can check nearest pharmacy by location
- No complex joins required
- Indexed queries for performance
- Minimal database operations
```

---

## 🔐 **PERMISSION MATRIX**

| Action | Patient | Pharmacy Staff | Admin |
|--------|---------|----------------|-------|
| View medicines | ✅ | ✅ | ✅ |
| View pharmacies | ✅ | ✅ | ✅ |
| Check availability | ✅ | ✅ | ✅ |
| Update inventory | ❌ | ✅ | ✅ |
| Create medicine | ❌ | ❌ | ✅ |
| Create pharmacy | ❌ | ❌ | ✅ |

---

## ✨ **VALIDATION & ERROR HANDLING**

### **Validation Checks**
```python
✓ No negative quantities
✓ Unique pharmacy + medicine combinations
✓ Only active pharmacies shown
✓ Only stock > 0 displayed in availability
✓ Invalid medicine IDs return 404
✓ Invalid pharmacy IDs return 404
```

### **Error Messages (User-Friendly)**
```
"Quantity cannot be negative."
"Medicine with ID 999 not found."
"Active pharmacy with ID 999 not found."
"Only admin and pharmacy staff can update inventory."
"medicine_id query parameter is required."
"pharmacy_id query parameter is required."
```

---

## 🗄️ **DATABASE SCHEMA**

```sql
Pharmacy
├── id (PK)
├── name (Indexed)
├── location (Indexed)
├── contact_number
├── address
├── is_active (Indexed)
├── created_at
└── updated_at

Medicine
├── id (PK)
├── name (Unique, Indexed)
├── description
├── is_prescription_required (Indexed)
├── created_at
└── updated_at

PharmacyInventory
├── id (PK)
├── pharmacy_id (FK, Indexed)
├── medicine_id (FK, Indexed)
├── quantity_available (Indexed)
├── last_updated
├── created_at
└── Unique(pharmacy_id, medicine_id)
    Indexes:
    ├── (pharmacy_id, quantity_available)
    ├── (medicine_id, quantity_available)
    └── last_updated
```

---

## ✅ **SUCCESS CHECKLIST**

- [x] Pharmacy model with location-based search
- [x] Medicine model with prescription flag
- [x] PharmacyInventory with quantity tracking
- [x] Stock validation (no negatives)
- [x] Medicine availability endpoints
- [x] Pharmacy listing with filtering
- [x] Inventory update with permissions
- [x] Read-only access for patients
- [x] Admin/pharmacy update access
- [x] Clear error messages
- [x] Offline-friendly design
- [x] Database indexes for performance
- [x] Audit fields (created_at, updated_at)
- [x] No errors or import issues

---

## 📝 **SUGGESTED GIT COMMIT BREAKDOWN**

### **Commit 1: Core Pharmacy Models**
```
commit: "feat(pharmacy): Add Pharmacy and Medicine models"

Files:
  telemedicine/models.py (Pharmacy, Medicine)

Description:
Core pharmacy infrastructure with:
- Pharmacy model (location, contact, active status)
- Medicine model (name, description, prescription flag)
- Audit fields and database indexes
```

### **Commit 2: Inventory Management**
```
commit: "feat(pharmacy): Add PharmacyInventory model with stock management"

Files:
  telemedicine/models.py (PharmacyInventory)

Description:
Inventory tracking system with:
- PharmacyInventory model (stock, timestamps)
- Quantity validation and constraints
- Stock manipulation methods (add, remove, update)
- Unique constraint on pharmacy + medicine
- Performance indexes
```

### **Commit 3: API & Serializers**
```
commit: "feat(api,serializers): Add pharmacy endpoints and serializers"

Files:
  telemedicine/serializers.py
  telemedicine/views.py
  telemedicine/urls.py

Description:
Complete API implementation with:
- MedicineSerializer, PharmacySerializer, PharmacyInventorySerializer
- MedicineViewSet (list, filter, search)
- PharmacyViewSet (list, filter, search)
- PharmacyInventoryViewSet with custom actions
- Available slots and pharmacy-based queries
- 8 API endpoints total
```

### **Commit 4: Documentation**
```
commit: "docs(pharmacy): Add comprehensive pharmacy module documentation"

Files:
  PHARMACY_MEDICINE_AVAILABILITY_DOCUMENTATION.md

Description:
Complete documentation including:
- Feature descriptions
- API endpoint specifications
- Sample requests and responses
- Rural design considerations
- Access control matrix
- Validation and error handling
- Database schema
- Workflow examples
```

---

## 🚀 **DEPLOYMENT CHECKLIST**

### **Database Setup**
```bash
python manage.py makemigrations telemedicine
python manage.py migrate
```

### **Initial Data**
```bash
# Create admin pharmacies and medicines
python manage.py shell
>>> from telemedicine.models import Medicine, Pharmacy
>>> # Add medicines and pharmacies
```

### **Permission Setup**
```python
# Ensure pharmacy staff has appropriate permissions
# Consider creating a PharmacyStaff group or custom permission
```

---

## 🎓 **REAL-WORLD USE CASE**

**Scenario**: Rural telemedicine platform in Northern India

1. **Patient in Village A** needs Paracetamol
   - Opens app → Search medicines → Find Paracetamol
   - Sees 3 pharmacies have it nearby
   - Chooses Central Pharmacy (quantity: 45)
   - Calls pharmacy → Confirms availability → Purchases

2. **Pharmacy Staff** restocks daily
   - Receives medicines from distributor
   - Updates inventory via app
   - Uses: `PATCH /pharmacy-inventory/15/update_quantity/`
   - Patients see updated availability

3. **Admin** monitors supply
   - Tracks low-stock medicines
   - Ensures adequate supply across villages
   - Makes procurement decisions

---

## 🔧 **MAINTENANCE & MONITORING**

### **Common Queries**
```python
# Which pharmacies have low stock?
PharmacyInventory.objects.filter(quantity_available__lt=5)

# Which medicines are available everywhere?
Medicine.objects.filter(pharmacy_inventory__quantity_available__gt=0).distinct().count()

# Last update times for audit
PharmacyInventory.objects.order_by('-last_updated')[:10]
```

### **Performance Optimization**
- Indexes on `quantity_available` for fast filtering
- Indexes on location for rural searches
- `select_related` used for nested data
- Pagination for large datasets

---

**End of Documentation**
