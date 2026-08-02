from django.contrib import admin

from .models import (
    AdmissionApplication,
    Applicant,
    ApplicationDocument,
    ApplicationIntake,
    ApplicationProgramme,
    ApplicationStatusEvent,
    ScholarshipApplication,
)


admin.site.register(Applicant)
admin.site.register(ApplicationIntake)
admin.site.register(ApplicationProgramme)
admin.site.register(AdmissionApplication)
admin.site.register(ScholarshipApplication)
admin.site.register(ApplicationDocument)
admin.site.register(ApplicationStatusEvent)
