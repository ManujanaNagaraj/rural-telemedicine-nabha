# Nabha Rural Telemedicine Frontend

A React-based frontend application for the Nabha Rural Telemedicine Platform, optimized for low-bandwidth rural environments.

## Features

- **User Authentication**: Secure JWT-based authentication with token refresh
- **Offline Support**: Continues to function with cached data when offline
- **Incremental Sync**: Efficient data synchronization using ETag and timestamps (95%+ bandwidth reduction)
- **Conflict Handling**: Server-authoritative conflict resolution (handles 409 Conflict responses)
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Low-Bandwidth Optimized**: Minimal payload sizes, efficient caching

## Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable React components
│   │   └── ProtectedRoute.js
│   ├── context/            # React Context for state management
│   │   ├── AuthContext.js
│   │   └── SyncContext.js
│   ├── pages/              # Page components
│   │   ├── LoginPage.js
│   │   └── DashboardPage.js
│   ├── services/           # API service layer
│   │   ├── apiClient.js    # Axios instance with interceptors
│   │   ├── authService.js
│   │   ├── appointmentService.js
│   │   ├── pharmacyService.js
│   │   ├── notificationService.js
│   │   ├── syncService.js
│   │   └── index.js
│   ├── utils/              # Utility functions
│   │   ├── validation.js
│   │   └── index.js
│   ├── App.js              # Main App component with routing
│   └── index.js            # React entry point
├── package.json
├── .env.local              # Environment configuration
└── README.md
```

## Prerequisites

- Node.js 16.x or higher
- npm or yarn package manager
- Backend Django API running at `http://localhost:8000`

## Installation

1. Clone the repository:
```bash
cd frontend
npm install
```

2. Configure environment variables in `.env.local`:
```
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENV=development
```

3. Start the development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

## Available Scripts

### `npm start`
Runs the app in development mode at http://localhost:3000

### `npm build`
Builds the app for production to the `build` folder

### `npm test`
Runs the test suite

## API Integration

### Authentication Flow

1. User logs in with email/password
2. Backend returns `access` and `refresh` tokens
3. Tokens stored in localStorage
4. `access` token attached to all API requests via Authorization header
5. Token refresh handled automatically on 401 responses

Example:
```javascript
import { authService } from './services';

const result = await authService.login('user@example.com', 'password');
if (result.success) {
  // User authenticated
}
```

### Sync Operations

All sync endpoints support incremental syncing with ETag caching:

```javascript
import { syncService } from './services';

// Sync appointments (only new/updated since last sync)
const appointments = await syncService.syncAppointments();

// Force full sync (ignore incremental)
const allAppointments = await syncService.syncAppointments({ incremental: false });
```

### Conflict Handling

When a 409 Conflict occurs (client data is stale):

```javascript
try {
  await appointmentService.updateAppointment(id, data);
} catch (error) {
  if (error.isConflict) {
    // Server returned 409 - fetch fresh data and retry
    const freshData = await appointmentService.getAppointment(id);
    // Update with fresh data
  }
}
```

## Context Hooks

### useAuth()
```javascript
const { user, loading, error, login, logout, refreshUser, isAuthenticated } = useAuth();
```

### useSync()
```javascript
const { syncStatus, syncPatients, syncAppointments, syncAll } = useSync();
// syncStatus: { isOnline, isSyncing, lastSyncTime, syncError }
```

## Service Layer

### authService
- `login(email, password)` - Authenticate user
- `logout()` - Clear tokens and user data
- `getCurrentUser()` - Get authenticated user
- `refreshToken()` - Refresh JWT token
- `isAuthenticated()` - Check authentication status
- `getAccessToken()` - Get stored token

### appointmentService
- `getAppointments(filters)` - Get user appointments
- `getAppointment(id)` - Get single appointment
- `createAppointment(data)` - Create new appointment
- `updateAppointment(id, data)` - Update appointment
- `cancelAppointment(id, reason)` - Cancel appointment

### pharmacyService
- `getPharmacies(filters)` - Get available pharmacies
- `getMedicines(filters)` - Search medicines
- `getPharmacyInventory(pharmacyId, filters)` - Get pharmacy inventory
- `checkAvailability(pharmacyId, medicineId)` - Check medicine availability

### notificationService
- `getNotifications(filters)` - Get notifications
- `markAsRead(notificationId)` - Mark as read
- `markAllAsRead()` - Mark all as read
- `deleteNotification(notificationId)` - Delete notification

### syncService
- `syncPatients(options)` - Sync patient data
- `syncAppointments(options)` - Sync appointments
- `syncPharmacyInventory(options)` - Sync inventory
- `handleSyncConflict(type, id, data)` - Handle 409 conflicts
- `isOnline()` - Check online status
- `setupConnectivityListeners(callbacks)` - Setup offline detection

## Utility Functions

### Validation
- `validateEmail(email)` - Email format validation
- `validatePassword(password)` - Password strength validation
- `validatePhoneNumber(phone)` - Phone number validation
- `validateFormData(data, fields)` - Form data validation

### Date/Time
- `formatDate(date)` - Format as "Jan 15, 2024"
- `formatDateTime(date)` - Format as "Jan 15, 2024 2:30 PM"
- `formatTime(date)` - Format as "2:30 PM"
- `getRelativeTime(date)` - Format as "2 hours ago"

### Storage
- `storageUtils.set(key, value)` - Save to localStorage
- `storageUtils.get(key)` - Get from localStorage
- `storageUtils.remove(key)` - Remove from localStorage

### Error Handling
- `errorUtils.getErrorMessage(error)` - Extract error message
- `errorUtils.isNetworkError(error)` - Check if network error
- `errorUtils.isConflict(error)` - Check if 409 conflict
- `errorUtils.isUnauthorized(error)` - Check if 401 error

## Offline Mode

The app continues to function offline with the following behavior:

1. **Data Display**: Shows cached data from last sync
2. **Navigation**: All routes accessible offline
3. **Sync Indicator**: Shows "● Offline" status in header
4. **Error Handling**: Network errors handled gracefully
5. **Auto-Sync**: Resumes syncing automatically when online

Example offline usage:
```javascript
const { syncStatus } = useSync();

if (!syncStatus.isOnline) {
  // Show offline indicator or use cached data
}
```

## Error Handling

The app handles common errors gracefully:

- **Network Errors**: Shown as alerts, allow retry
- **401 Unauthorized**: Triggers automatic token refresh
- **409 Conflict**: Fetches fresh server data and suggests retry
- **Validation Errors**: Shown on form fields
- **API Errors**: Display user-friendly error messages

## Performance Optimization

1. **ETag Caching**: 304 Not Modified responses skip data processing
2. **Incremental Sync**: Only new/updated data downloaded (last_sync_timestamp)
3. **Lazy Loading**: Components load on-demand via React Router
4. **Memoization**: Expensive computations cached
5. **Debouncing**: Form inputs debounced for search

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REACT_APP_API_URL` | `http://localhost:8000/api` | Backend API base URL |
| `REACT_APP_ENV` | `development` | Environment (development/production) |
| `REACT_APP_ENABLE_OFFLINE_MODE` | `true` | Enable offline support |
| `REACT_APP_SYNC_INTERVAL` | `30000` | Auto-sync interval in ms |

## Development

### Adding a New Page

1. Create component in `src/pages/YourPage.js`
2. Add route to `src/App.js`
3. Wrap with `<ProtectedRoute>` if authentication required

### Adding a New Service

1. Create file in `src/services/yourService.js`
2. Export from `src/services/index.js`
3. Use in components via `import { yourService } from '../services'`

### Adding a Context

1. Create context in `src/context/YourContext.js`
2. Add provider wrapper to `App.js`
3. Use hook in components: `const context = useYourContext()`

## Testing

```bash
npm test
```

Tests are located in `*.test.js` files alongside components.

## Deployment

### Production Build

```bash
npm run build
```

Creates optimized production build in `build/` folder.

### Environment Configuration

Update `.env.local` for production:
```
REACT_APP_API_URL=https://api.nabha-telemedicine.com
REACT_APP_ENV=production
```

### Serving

Can be served with any static file server:
```bash
npx serve -s build
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Known Limitations

1. **Offline Sync**: While offline, all data is cached. New data from other users not available.
2. **Real-time Updates**: Uses polling (not WebSocket) for notifications
3. **Large Files**: File uploads limited to available bandwidth

## Troubleshooting

### API Connection Fails

1. Verify backend is running at `REACT_APP_API_URL`
2. Check CORS headers in backend
3. Clear browser cache and localStorage

### Authentication Loop

1. Clear localStorage: `localStorage.clear()`
2. Verify backend token endpoints working
3. Check token expiration settings

### Offline Mode Not Working

1. Verify `REACT_APP_ENABLE_OFFLINE_MODE=true` in `.env.local`
2. Check browser localStorage enabled
3. Verify at least one sync completed

## License

Proprietary - Nabha Rural Telemedicine Platform

## Support

For issues and questions, contact the development team.
