from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AllowanceViewSet, 
    DeductionViewSet, 
    LoanViewSet, 
    PayrollCalculationView, 
    PayslipPDFView
)

# 1. إعداد الـ Router للجداول الإدارية
router = DefaultRouter()
router.register(r'allowances', AllowanceViewSet, basename='allowance')
router.register(r'deductions', DeductionViewSet, basename='deduction')
router.register(r'loans', LoanViewSet, basename='loan')

# 2. إعداد المسارات المباشرة للعمليات الحسابية
urlpatterns = [
    # مسارات الحسابات وتوليد الـ PDF (تمرير رقم الموظف في الرابط)
    path('calculate/<int:employee_id>/', PayrollCalculationView.as_view(), name='payroll-calculate'),
    path('download-pdf/<int:employee_id>/', PayslipPDFView.as_view(), name='payroll-download-pdf'),
    
    # دمج مسارات الـ Router (الإضافة، التعديل، الحذف)
    path('', include(router.urls)), 
]