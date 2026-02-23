from django.db import models
from employees.models import Employee
# Create your models here.
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
    