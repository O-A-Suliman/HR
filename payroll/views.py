from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

# 1. استدعاء النماذج والمحولات المحلية الخاصة بالماليات
from .models import Allowance, Deduction, Loan
from .serializers import  PayslipSerializer,LoanSerializer,AllowanceSerializer,DeductionSerializer

from employees.models import Employee
from attendance.models import Attendance
from leaves.models import LeaveRequest

# ==========================================
# أولاً: قسم العمليات الإدارية (CRUD)
# ==========================================
class AllowanceViewSet(viewsets.ModelViewSet):
    queryset = Allowance.objects.all()
    serializer_class = AllowanceSerializer
    permission_classes = [IsAuthenticated] # استخدم IsAdminOrHR لاحقاً

class DeductionViewSet(viewsets.ModelViewSet):
    queryset = Deduction.objects.all()
    serializer_class = DeductionSerializer
    permission_classes = [IsAuthenticated]

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

# ==========================================
# ثانياً: قسم العمليات الحسابية (Business Logic)
# ==========================================
class PayrollCalculationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        if not month or not year:
            return Response({"error": "الرجاء تحديد الشهر والسنة"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "الموظف غير موجود"}, status=status.HTTP_404_NOT_FOUND)

        # (قم بوضع الكود الحسابي الكامل الخاص بك هنا لحساب الساعات، الإجازات، الخ)
        # سأضع لك مثالاً للبدلات والخصومات من التطبيق الحالي:
        
        basic_salary = float(employee.basic_salary)
        
        allowances = Allowance.objects.filter(employee=employee, date__month=month, date__year=year)
        total_allowances = float(allowances.aggregate(total=Sum('amount'))['total'] or 0)
        
        deductions = Deduction.objects.filter(employee=employee, date__month=month, date__year=year)
        total_deductions = float(deductions.aggregate(total=Sum('amount'))['total'] or 0)
        
        # معادلة الصافي التقريبية للتوضيح
        net_salary = basic_salary + total_allowances - total_deductions
        
        data = {
            "employee": employee.username,
            "month": month,
            "year": year,
            "basic_salary": round(basic_salary, 2),
            "total_worked_hours": 0, # احسبها من Attendance كما في كودك القديم
            "unpaid_leave_days": 0,  # احسبها من LeaveRequest
            "allowances": round(total_allowances, 2),
            "deductions": round(total_deductions, 2),
            "loan_installments": 0,  # احسبها من Loan
            "net_salary": round(net_salary, 2)
        }
        
        serializer = PayslipSerializer(instance=data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PayslipPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        # استدعاء دالة الحساب أو جلب البيانات (الأفضل مستقبلاً جلبها من جدول تجميد الرواتب Snapshot)
        payroll_view = PayrollCalculationView()
        response = payroll_view.get(request, employee_id=employee_id)
        
        if response.status_code != 200:
            return response 
            
        payroll_data = response.data 
        
        template = get_template('payslip.html') 
        html = template.render(payroll_data)    
        
        pdf_response = HttpResponse(content_type='application/pdf')
        filename = f"Payslip_{payroll_data['employee']}_{payroll_data['month']}_{payroll_data['year']}.pdf"
        pdf_response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        pisa_status = pisa.CreatePDF(html, dest=pdf_response)
        
        if pisa_status.err:
            return Response({'error': 'حدث خطأ أثناء توليد الملف'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return pdf_response