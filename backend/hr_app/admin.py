from django.contrib import admin

from hr_app.models import Employee, EmployeeDocument, EmploymentRecord, HRStaff, Position, SalaryAdjustment


admin.site.register(HRStaff)
admin.site.register(Position)
admin.site.register(Employee)
admin.site.register(EmploymentRecord)
admin.site.register(EmployeeDocument)
admin.site.register(SalaryAdjustment)
