from django.db import models
from employees.models import Employee
# Create your models here.
class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    worked_hours = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, default='present')