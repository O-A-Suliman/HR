from django.db import models
from django.contrib.auth.models import AbstractUser



class Department(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Employee(AbstractUser):
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(
        max_length=20, 
        choices=[('admin', 'Admin'), ('hr', 'HR'), ('employee', 'Employee')],
        default='employee'
    )
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    annual_leave_balance = models.PositiveIntegerField(default=21)

    @property #بتتعامل مع الدالة كأنها حقل خاص زي باقي الحقول
    def hourly_rate(self):
        if self.basic_salary:
            return (self.basic_salary / 30) / 8
        return 0.00

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    worked_hours = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, default='present')


class LeaveRequest(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    
    LEAVE_TYPES = [
        ('annual', 'سنوية'),
        ('sick', 'مرضية'),
        ('unpaid', 'بدون أجر'),
    ]
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    days = models.PositiveIntegerField() 
    
    reason = models.TextField()
    
    
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('approved', 'مقبول'),
        ('rejected', 'مرفوض'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # متى تم تقديم الطلب؟ (للتتبع)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.username} - {self.leave_type} ({self.status})"
    
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