from rest_framework.routers import DefaultRouter
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    PatientViewSet, DoctorViewSet, AppointmentViewSet, 
    CustomTokenObtainPairView, LoginView, symptom_checker
)

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'auth', LoginView, basename='auth')

urlpatterns = [
    # JWT Token endpoints
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Login/Logout endpoints
    path('auth/login/', LoginView.as_view({'post': 'login'}), name='auth_login'),
    path('auth/logout/', LoginView.as_view({'post': 'logout'}), name='auth_logout'),
    path('auth/me/', LoginView.as_view({'get': 'me'}), name='auth_me'),
    
    # AI Symptom Checker endpoint (no authentication required - public triage)
    path('symptom-check/', symptom_checker, name='symptom_checker'),
] + router.urls