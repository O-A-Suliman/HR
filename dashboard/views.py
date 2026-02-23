from rest_framework.views import APIView
from django.utils import timezone
from employees.models import Employee
from attendance.models import Attendance
from leaves.models import LeaveRequest
from rest_framework.response import Response
from rest_framework import status


class DashboardAPIView(APIView):
    # يمكننا لاحقاً إضافة IsAdminOrHR هنا لحماية اللوحة
    
    def get(self, request):
        today = timezone.now().date()
        
        # 1. إجمالي الموظفين
        total_employees = Employee.objects.count()
        
        # 2. الحضور اليوم
        present_today = Attendance.objects.filter(date=today).count()
        
        # 3. المجازين اليوم
        on_leave_today = LeaveRequest.objects.filter(
            status='approved',
            start_date__lte=today,
            end_date__gte=today
        ).count()
        
        # 4. الغياب (معادلة استنتاجية بسيطة)
        absent_today = total_employees - (present_today + on_leave_today)
        
        return Response({
            "date": today,
            "total_employees": total_employees,
            "present_today": present_today,
            "on_leave_today": on_leave_today,
            "absent_today": absent_today if absent_today > 0 else 0
        }, status=status.HTTP_200_OK)