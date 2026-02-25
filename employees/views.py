from .serializers import EmployeeSerializer
from .permissions import IsAdminOrHR
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Employee
from rest_framework.views import APIView
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
# Create your views here.

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [IsAdminOrHR()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Employee.objects.all() 
    
class DownloadSecureCVView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,employee_id):
        employee=get_object_or_404(Employee,id=employee_id)
        if employee !=request.user and request.user.role in ['hr',"admin"]:
            return Response(
                {"detail": "عذراً، غير مصرح لك بتحميل هذا الملف."}, 
                status=403
            )
        if not employee.documents:
            raise Http404("لا يوجد مستند  لهذا الموظف")
        file_path=employee.documents.path
        return FileResponse(open(file_path,'rb'))