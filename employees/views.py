from xhtml2pdf import pisa
from django.template.loader import get_template
from .serializers import EmployeeSerializer
from .permissions import IsAdminOrHR
from rest_framework import viewsets,status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Employee
from leaves.models import LeaveRequest
from attendance.models import Attendance
from payroll.models import Allowance,Deduction,Loan
from django.db.models import Sum
# Create your views here.

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