from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum
from .models import Employee, Attendance,LeaveRequest,Allowance,Deduction,Loan
from .serializers import EmployeeSerializer, AttendanceSerializer,LeaveRequestSerializer,PayslipSerializer
from .permissions import IsAdminOrHR
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from rest_framework.views import APIView
from django.utils import timezone

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [IsAdminOrHR()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Employee.objects.all() 
    
    @action(detail=True, methods=["GET"])
    def payroll(self, request, pk=None):
        employee = self.get_object() 
        user = request.user
        if user not in ['admin','hr'] and user !=employee:
            return Response(
                {"error": "عملية مرفوضة! لا يمكنك الاطلاع على رواتب الموظفين الآخرين. 🛑"}, 
                status=status.HTTP_403_FORBIDDEN
            ) 
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        if not month or not year:
            return Response({"error": "الرجاء تحديد الشهر والسنة"}, status=status.HTTP_400_BAD_REQUEST)
            
        # 1. حساب الساعات الفعلية (للعرض في الكشف فقط)
        attendances = Attendance.objects.filter(employee=employee, date__month=month, date__year=year)
        total_hours_dict = attendances.aggregate(total=Sum('worked_hours'))
        total_hours = total_hours_dict['total'] or 0
        
        # 2. البدلات (Allowances)
        allowance = Allowance.objects.filter(employee=employee, date__month=month, date__year=year)
        total_amount_dict = allowance.aggregate(total=Sum('amount')) # تصحيح Sum و aggregate
        total_amount = float(total_amount_dict['total'] or 0) # تحويل إلى float
        
        # 3. الخصومات والجزاءات (Deductions)
        deduction = Deduction.objects.filter(employee=employee, date__month=month, date__year=year)
        total_deduction_dict = deduction.aggregate(total=Sum('amount')) # تصحيح Sum و aggregate
        total_deduction = float(total_deduction_dict["total"] or 0) # تحويل إلى float
        
        # 4. أيام الإجازات بدون أجر
        unpaid_leaves = LeaveRequest.objects.filter(
            employee=employee,
            leave_type='unpaid',
            status='approved',
            start_date__month=month, 
            start_date__year=year
        )
        unpaid_days_dict = unpaid_leaves.aggregate(total_days=Sum('days'))
        unpaid_days = unpaid_days_dict['total_days'] or 0
        
        # 5. الحسبة المالية الرسمية للـ HR
        basic_salary = float(employee.basic_salary)
        daily_rate = basic_salary / 30  # أجر اليوم الواحد
        
        deduction_amount = float(unpaid_days) * daily_rate # قيمة خصم الغياب        
        # 4. أقساط السلف الجارية (Loans)
        active_loans = Loan.objects.filter(
            employee=employee, 
            status= 'approved'  # ماذا نكتب هنا؟
        )
        total_loan_installments_dict = active_loans.aggregate(total=Sum( 'monthly_installment' )) # ما هو الحقل الذي سنجمعه؟
        total_loan_installments = float(total_loan_installments_dict["total"] or 0)
        total_discounts = total_deduction + deduction_amount+total_loan_installments # إجمالي الخصومات (غياب + جزاءات)
        
        
        net_salary = basic_salary + total_amount - total_discounts # صافي الراتب
        
        # 6. تجهيز البيانات للـ Serializer
        data = {
            "employee": employee.username, # استخدام username بدلاً من كائن الموظف بالكامل
            "month": month,
            "year": year,
            "basic_salary": round(basic_salary, 2),
            "total_worked_hours": round(total_hours, 2),
            "unpaid_leave_days": unpaid_days, # الحقل المفقود
            "allowances": round(total_amount, 2), # توحيد اسم المتغير
            "deductions": round(total_discounts, 2), 
            "loan_installments": round(total_loan_installments, 2),
            "net_salary": round(net_salary, 2)
        }
        
        serializer = PayslipSerializer(instance=data) # استخدمنا instance لتمرير القاموس
        return Response(serializer.data, status=status.HTTP_200_OK)
    @action(detail=True, methods=["GET"])
    def download_payslip(self, request, pk=None):
        # 1. الخدعة المعمارية: استدعاء دالة payroll للحصول على الأرقام الجاهزة!
        payroll_response = self.payroll(request, pk=pk)
        
        # إذا كان هناك خطأ (مثلاً لم يرسل الشهر والسنة)، نرجع الخطأ كما هو
        if payroll_response.status_code != 200:
            return payroll_response 
            
        # 2. استخراج البيانات (الـ JSON) من استجابة الدالة
        payroll_data = payroll_response.data 
        
        # 3. دمج البيانات مع القالب HTML
        template = get_template('payslip.html') # اسم الملف الذي أنشأناه
        html = template.render(payroll_data)    # حقن المتغيرات داخله
        
        # 4. إعداد الـ Response ليكون من نوع PDF وليس JSON
        response = HttpResponse(content_type='application/pdf')
        # السطر التالي يخبر المتصفح أن يحمل الملف باسم ديناميكي
        filename = f"Payslip_{payroll_data['employee']}_{payroll_data['month']}_{payroll_data['year']}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # 5. تحويل الـ HTML إلى PDF باستخدام المكتبة
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return Response({'error': 'حدث خطأ أثناء توليد الملف'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return response
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
    
class LeaveRequestViewSet(viewsets.ModelViewSet):

    serializer_class=LeaveRequestSerializer
    def get_queryset(self):
        user=self.request.user
        if user.role is ['admin','hr']:
            return LeaveRequest.objects.all()
        return LeaveRequest.objects.filter(emplotee=user)
    
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