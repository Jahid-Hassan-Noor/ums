from django.contrib import admin
from .models import (
    CourseOfferProposal,
    Executive,
    ExecutiveUnitAssignment,
    ResultApproval,
    ResultBatch,
    ResultPublication,
    ResultRecord,
    ResultReviewNote,
    TimetableSlot,
)

admin.site.register(CourseOfferProposal)
admin.site.register(Executive)
admin.site.register(ExecutiveUnitAssignment)
admin.site.register(ResultApproval)
admin.site.register(ResultBatch)
admin.site.register(ResultPublication)
admin.site.register(ResultRecord)
admin.site.register(ResultReviewNote)
admin.site.register(TimetableSlot)
