from .serializers import LeaveRequestSerializer
from .models import LeaveRequest
from rest_framework import viewsets,status
from employees.permissions import IsAdminOrHR
from rest_framework.decorators import action
from rest_framework.response import Response
# Create your views here.
class LeaveRequestViewSet(viewsets.ModelViewSet):

    serializer_class=LeaveRequestSerializer
    def get_queryset(self):
        user=self.request.user
        if user.role in ['admin','hr']:
            return LeaveRequest.objects.all()
        return LeaveRequest.objects.filter(employee=user)
    
    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    @action(detail=False,methods=["POST"],permission_classes=[IsAdminOrHR])
    def approve(self, request, pk=None):
        leave_request = self.get_object() # 1. نجلب الطلب المقصود
        employee = leave_request.employee # 2. نجلب الموظف صاحب الطلب

        # المطب الأول: هل تمت الموافقة عليه مسبقاً أو رفضه؟
        if leave_request.status != 'pending':
            return Response(
                {"error": f"لا يمكن تعديل هذا الطلب، حالته الحالية هي: {leave_request.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # المطب الثاني وخطوتك الأولى: التحقق من الرصيد (للإجازات السنوية فقط)
        if leave_request.leave_type == 'annual':
            if employee.annual_leave_balance < leave_request.days:
                return Response(
                    {"error": f"رصيد الموظف ({employee.annual_leave_balance} أيام) لا يكفي لطلب ({leave_request.days} أيام)."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # خطوتك الثالثة: خصم الرصيد
            employee.annual_leave_balance -= leave_request.days
            employee.save() # حفظ رصيد الموظف الجديد

        # خطوتك الثانية: تغيير حالة الطلب إلى مقبول
        leave_request.status = 'approved'
        leave_request.save()

        return Response({
            "message": "تمت الموافقة على الإجازة بنجاح!",
            "new_balance": employee.annual_leave_balance
        }, status=status.HTTP_200_OK)
    