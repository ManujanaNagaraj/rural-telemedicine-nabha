# Nabha Telemedicine Frontend - Quick Start Guide

## 5-Minute Setup

### Prerequisites
- Node.js 16+ installed
- Backend API running at `http://localhost:8000`

### Installation

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies (first time only)
npm install

# 3. Start development server
npm start
```

The app opens automatically at `http://localhost:3000`

### Login
Use these demo credentials:
- **Email**: doctor@example.com
- **Password**: Doctor@123

## Quick Architecture Overview

```
┌─────────────────────────────────────┐
│      React Components (Pages)       │
│  LoginPage, Dashboard, Appointments │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Context Hooks (State)            │
│  AuthContext, SyncContext           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Service Layer (API Logic)      │
│ authService, appointmentService,   │
│ pharmacyService, syncService       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   API Client (Axios + Interceptors) │
│ JWT Auth, ETag Caching, Conflicts  │
└──────────────┬──────────────────────┘
               │
       Backend Django API
```

## Key Files You Need to Know

### To Use Authentication
```javascript
import { useAuth } from './context/AuthContext';

function MyComponent() {
  const { user, login, logout } = useAuth();
  
  const handleLogin = async (email, password) => {
    const result = await login(email, password);
    if (result.success) {
      // User logged in
    }
  };
}
```

### To Sync Data
```javascript
import { useSync } from './context/SyncContext';

function MyComponent() {
  const { syncStatus, syncAll } = useSync();
  
  const handleSync = async () => {
    const result = await syncAll();
    // Data synced
  };
  
  if (!syncStatus.isOnline) {
    return <p>⚠️ Currently Offline - Using Cached Data</p>;
  }
}
```

### To Call APIs
```javascript
import { appointmentService } from './services';

async function loadAppointments() {
  try {
    const appointments = await appointmentService.getAppointments();
    // appointments is an array
  } catch (error) {
    console.error(error.message);
  }
}
```

### To Handle Forms
```javascript
import { validateEmail, validateFormData } from './utils/validation';

function LoginForm() {
  const errors = validateFormData(formData, ['email', 'password']);
  if (Object.keys(errors).length > 0) {
    // Show errors to user
  }
}
```

## Common Tasks

### Adding a New Page

1. Create `src/pages/MyPage.js`:
```javascript
function MyPage() {
  return <div>My Page Content</div>;
}
export default MyPage;
```

2. Add route to `src/App.js`:
```javascript
<Route
  path="/mypage"
  element={
    <ProtectedRoute>
      <MyPage />
    </ProtectedRoute>
  }
/>
```

3. Navigate to it:
```javascript
import { useNavigate } from 'react-router-dom';
const navigate = useNavigate();
navigate('/mypage');
```

### Making an API Call

1. Create service in `src/services/myService.js`:
```javascript
const myService = {
  getMyData: async (filters = {}) => {
    const response = await apiClient.get('/my-endpoint/', { params: filters });
    return response.data;
  }
};
export default myService;
```

2. Export from `src/services/index.js`:
```javascript
export { default as myService } from './myService';
```

3. Use in component:
```javascript
import { myService } from './services';

const data = await myService.getMyData({ status: 'active' });
```

### Handling Offline Data

```javascript
import { useSync } from './context/SyncContext';

function MyComponent() {
  const { syncStatus } = useSync();
  
  return (
    <>
      {!syncStatus.isOnline && (
        <div>⚠️ Offline Mode - Data may be outdated</div>
      )}
      
      <button 
        onClick={syncAll}
        disabled={!syncStatus.isOnline || syncStatus.isSyncing}
      >
        {syncStatus.isSyncing ? 'Syncing...' : 'Sync Now'}
      </button>
    </>
  );
}
```

### Displaying Appointment Status

```javascript
import { statusUtils, dateUtils } from './utils';

function AppointmentCard({ appointment }) {
  return (
    <>
      <span style={{ color: statusUtils.getStatusClass(appointment.status) }}>
        {statusUtils.getStatusIcon(appointment.status)}
        {statusUtils.getStatusDisplay(appointment.status)}
      </span>
      
      <p>{dateUtils.formatDateTime(appointment.scheduled_time)}</p>
    </>
  );
}
```

## Configuration

Edit `.env.local`:

```env
# Backend API URL
REACT_APP_API_URL=http://localhost:8000/api

# Environment
REACT_APP_ENV=development

# Features
REACT_APP_ENABLE_OFFLINE_MODE=true
REACT_APP_SYNC_INTERVAL=30000
REACT_APP_NOTIFICATION_POLL_INTERVAL=30000
```

## Troubleshooting

### "Cannot connect to API"
1. Verify backend running: `curl http://localhost:8000/api/`
2. Check REACT_APP_API_URL in .env.local
3. Check browser console for CORS errors

### "Login not working"
1. Check backend token endpoint: `POST http://localhost:8000/api/auth/token/`
2. Clear localStorage: `localStorage.clear()` in console
3. Check backend is accepting credentials

### "Offline mode not working"
1. Verify `REACT_APP_ENABLE_OFFLINE_MODE=true` in .env.local
2. Check at least one sync succeeded
3. Verify localStorage is enabled in browser

### "Data not syncing"
1. Check online status: Open DevTools → Application → Storage → sync_timestamp
2. Click "Sync Now" button manually
3. Check browser console for errors
4. Verify last_sync_timestamp is set

## Available Services

```javascript
import {
  authService,        // login, logout, getCurrentUser, refreshToken
  appointmentService, // getAppointments, createAppointment, updateAppointment
  pharmacyService,    // getPharmacies, getMedicines, checkAvailability
  notificationService,// getNotifications, markAsRead
  syncService,        // syncPatients, syncAppointments, handleSyncConflict
  apiClient           // Raw axios instance if needed
} from './services';
```

## Utility Functions Quick Reference

### Validation
```javascript
import { validateEmail, validatePhoneNumber, validateFormData } from './utils/validation';

validateEmail('user@example.com')           // true/false
validatePhoneNumber('1234567890')           // true/false
validateFormData(data, ['email', 'password']) // { field: 'error' }
```

### Formatting
```javascript
import { dateUtils, formatUtils, statusUtils } from './utils';

dateUtils.formatDate(new Date())            // "Jan 15, 2024"
dateUtils.getRelativeTime(new Date())       // "Just now"
formatUtils.formatPhoneNumber('1234567890') // "(123) 456-7890"
formatUtils.truncate('Long text', 50)       // "Long text..."
statusUtils.getStatusDisplay('pending')     // "Pending"
```

### Storage
```javascript
import { storageUtils } from './utils';

storageUtils.set('key', { data: 'value' })  // Save object
storageUtils.get('key')                     // Get object
storageUtils.remove('key')                  // Remove item
```

### Error Handling
```javascript
import { errorUtils } from './utils';

errorUtils.getErrorMessage(error)           // Extract readable message
errorUtils.isNetworkError(error)            // Check error type
errorUtils.isConflict(error)                // Check 409 status
errorUtils.isUnauthorized(error)            // Check 401 status
```

## Performance Tips

1. **Use Sync Endpoints**: Always use sync endpoints instead of full fetch
2. **Enable Offline**: Cached data means app works offline
3. **Minimize Bundle**: Tree-shake unused code in production build
4. **Cache API Responses**: Use localStorage for frequently accessed data
5. **Lazy Load Routes**: Use React.lazy() for code splitting

## Next Steps

1. ✅ Setup complete
2. ✅ Authentication working
3. ✅ Services configured
4. ⏳ Build additional pages (AppointmentDetail, PharmacyPage, etc.)
5. ⏳ Add error boundary
6. ⏳ Add loading states
7. ⏳ Add unit tests
8. ⏳ Deploy to production

## Testing with Backend

### Test Authentication
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@example.com","password":"Doctor@123"}'
```

### Test Sync Endpoint
```bash
curl -X GET "http://localhost:8000/api/sync/appointments/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Offline Sync
1. Go Online: Data syncs
2. Go Offline: App uses cached data
3. Go Online: Auto-syncs again

## Support

For issues:
1. Check browser console (F12)
2. Check backend logs
3. Check .env.local configuration
4. Clear localStorage and try again

---

Happy coding! 🚀
