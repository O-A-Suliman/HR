from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.files.storage import FileSystemStorage
from config import settings
# Create your models here.
class Department(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Employee(AbstractUser):
    private_storage=FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    documents=models.FileField(upload_to='employees/documents/',storage=private_storage,null=True,blank=True)
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