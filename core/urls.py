from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, AttendanceViewset, LeaveRequestViewSet,DashboardAPIView
# تأكد من استدعاء كل الـ Views الخاصة بك هنا

# هنا نستخدم الـ Router السحري الخاص بـ DRF
router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'attendances', AttendanceViewset, basename='attendance')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')

urlpatterns = [
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    path('', include(router.urls)), 
]