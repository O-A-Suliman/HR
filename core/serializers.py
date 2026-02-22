from rest_framework import serializers
from .models import Employee,Attendance,LeaveRequest
class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model=Employee
        fields="__all__"

class AttendanceSerializer(serializers.ModelSerializer):
    # 1. نعلن عن حقل محسوب جديد
    daily_pay = serializers.SerializerMethodField() #حقل اضافي للحساب يطلع القيمة في API فقط

    class Meta:
        model = Attendance
        fields = ['id', 'employee', 'date', 'check_in', 'check_out', 'worked_hours', 'daily_pay']
        read_only_fields = ['worked_hours', 'daily_pay']

    # 3. نكتب الدالة التي ستحسب قيمة هذا الحقل
    # (اسم الدالة يجب أن يكون get_ متبوعاً باسم الحقل)
    def get_daily_pay(self, obj):
        # obj هنا يمثل سجل الحضور الحالي
        if obj.worked_hours and obj.employee.basic_salary:
            # العملية الحسابية التي اكتشفتها أنت!
            pay = obj.worked_hours * float(obj.employee.hourly_rate)
            return round(pay, 2) # نقرب الناتج لرقمين عشريين فقط (للقروش/السنتات)
        
        return 0.00
    
class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model=LeaveRequest
        fields='__all__'

class PayslipSerializer(serializers.Serializer):
    employee = serializers.CharField()
    month = serializers.CharField()
    year = serializers.CharField()
    basic_salary = serializers.FloatField()
    total_worked_hours = serializers.FloatField()
    unpaid_leave_days = serializers.IntegerField()
    allowances = serializers.FloatField()     # إجمالي البدلات والمكافآت
    deductions = serializers.FloatField()     # إجمالي الخصومات (إجازات + جزاءات)
    net_salary = serializers.FloatField()
    loan_installments = serializers.FloatField()