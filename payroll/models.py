from django.db import models
from employees.models import Employee
# Create your models here.
class Allowance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='allowances')
    amount = models.DecimalField(max_digits=10, decimal_places=2) # للماليات
    date = models.DateField() # لتحديد شهر الاستحقاق
    reason = models.CharField(max_length=255) # نص قصير لسبب المكافأة
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.username} - Allowance: {self.amount}"

class Deduction(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='deductions')
    amount = models.DecimalField(max_digits=10, decimal_places=2) # للماليات
    date = models.DateField() # لتحديد شهر الخصم
    reason = models.CharField(max_length=255) # نص قصير لسبب الخصم (تأخير، سلفة...)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.username} - Deduction: {self.amount}"
    
class Loan(models.Model):
    # خيارات حالة السلفة
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليه (جاري الخصم)'),
        ('paid', 'تم السداد'),
        ('rejected', 'مرفوض'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loans')
    reason = models.CharField(max_length=255) # سبب السلفة
    
    # 1. إجمالي مبلغ السلفة
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # 2. القسط الشهري الذي سيتم خصمه تلقائياً
    monthly_installment = models.DecimalField(max_digits=10, decimal_places=2)
    
    # 3. حالة السلفة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.username} - Loan: {self.total_amount} ({self.get_status_display()})"