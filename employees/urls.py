from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet,DownloadSecureCVView

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
urlpatterns = [
    path('', include(router.urls)),
    path('employees/<int:employee_id>/download_documents/', DownloadSecureCVView.as_view(), name='download_documents'),
]