from django.db import models
from employees.models import Employee
# Create your models here.
class AuditLog(models.Model):
    user=models.ForeignKey(Employee,on_delete=models.SET_NULL,null=True)
    action=models.CharField(max_length=50,choices=[('create','CREATE'),('update','UPDATE'),('delete','DELETE')])
    model_name=models.CharField(max_length=50)
    record_id=models.IntegerField()
    old_values=models.JSONField()
    new_values=models.JSONField()
    timestamp=models.DateTimeField(auto_now_add=True)