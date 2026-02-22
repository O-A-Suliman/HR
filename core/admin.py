from django.contrib import admin
from .models import Employee, Attendance, LeaveRequest, Allowance, Deduction,Loan

admin.site.register(Employee)
admin.site.register(Attendance)
admin.site.register(LeaveRequest)
admin.site.register(Allowance)
admin.site.register(Loan)
admin.site.register(Deduction)