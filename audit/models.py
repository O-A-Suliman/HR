from django.db import models
from employees.models import Employee # تأكد من مسار جدول الموظفين الخاص بك

class AuditLog(models.Model):
    user = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=[('create','CREATE'), ('update','UPDATE'), ('delete','DELETE')])
    model_name = models.CharField(max_length=50)
    record_id = models.IntegerField()
    old_values = models.JSONField(null=True, blank=True) # جعلناها اختيارية تحسباً للإنشاء الجديد
    new_values = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name}"