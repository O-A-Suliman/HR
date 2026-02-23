from rest_framework import permissions

class IsAdminOrHR(permissions.BasePermission): #الكلاس الأساسية في Django REST Framework عشان تعمل صلاحيات مخصصة
    def has_permission(self, request, view):#الدالة الأساسية البتتسأل قبل ما أي request يدخل على الـ view
        return bool(request.user.is_authenticated and request.user.role in ['admin', 'hr'])