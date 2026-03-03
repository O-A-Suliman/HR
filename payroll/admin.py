from django.contrib import admin
from .models import Allowance,Deduction,Loan
# Register your models here.
admin.site.register(Allowance)
admin.site.register(Deduction)
admin.site.register(Loan)