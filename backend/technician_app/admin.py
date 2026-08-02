from django.contrib import admin

from technician_app.models import (
    Election,
    ElectionCandidate,
    ElectionResultSnapshot,
    HelpdeskTicket,
    HelpdeskTicketUpdate,
    SchoolElectionSeat,
    Technician,
    Vote,
)


admin.site.register(Technician)
admin.site.register(HelpdeskTicket)
admin.site.register(HelpdeskTicketUpdate)
admin.site.register(Election)
admin.site.register(SchoolElectionSeat)
admin.site.register(ElectionCandidate)
admin.site.register(Vote)
admin.site.register(ElectionResultSnapshot)
