from rest_framework import serializers
from .models import Allowance,Deduction,Loan
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

class AllowanceSerializer(serializers.ModelSerializer):
    class Meta:
        model=Allowance
        fields='__all__'

class DeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Deduction
        fields='__all__'

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model=Loan
        fields='__all__'