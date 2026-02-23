from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import AttendanceViewset

router = DefaultRouter()
router.register(r'attendances', AttendanceViewset, basename='attendance')

urlpatterns = [
    path('', include(router.urls)), 
]