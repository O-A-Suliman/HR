from .serializers import AttendanceSerializer
from .models import Attendance
from rest_framework import viewsets,status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.utils import timezone
from rest_framework.response import Response
# Create your views here.
class AttendanceViewset(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    # 3. تعديل الفلتر: الموظف هو نفسه الـ request.user
    def get_queryset(self):
        return Attendance.objects.filter(employee=self.request.user)

    @action(detail=False, methods=["POST"])
    def check_in(self, request):
        employee = request.user
        today_date = timezone.now().date()
        
        if Attendance.objects.filter(employee=employee, date=today_date).exists():
            return Response(
                {"error": "لقد قمت بتسجيل الحضور مسبقاً هذا اليوم!"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        time_now = timezone.now()
        Attendance.objects.create(employee=employee, date=today_date, check_in=time_now, status="present")
        
        return Response(
            {"message": "تم تسجيل الحضور بنجاح!", "time": time_now}, 
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["POST"])
    def check_out(self, request): # إضافة self
        employee = request.user
        today_date = timezone.now().date()
        
        try:
            attendance = Attendance.objects.get(employee=employee, date=today_date)
        except Attendance.DoesNotExist:
            return Response(
                {"error": "لا يمكنك تسجيل الانصراف لأنك لم تسجل الحضور اليوم!"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if attendance.check_out:
            return Response(
                {"error": "لقد قمت بتسجيل الانصراف مسبقاً هذا اليوم!"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        time_now = timezone.now()
        attendance.check_out = time_now
        time_diff = attendance.check_out - attendance.check_in
        attendance.worked_hours = time_diff.total_seconds() / 3600
        attendance.save()
        
        return Response(
            {"message": "تم تسجيل الانصراف بنجاح، شكراً لجهدك اليوم!", "time": time_now}, 
            status=status.HTTP_200_OK
        )
