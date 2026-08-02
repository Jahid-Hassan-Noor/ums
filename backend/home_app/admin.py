from django.contrib import admin
from .models import (
    OfficialLink,
    PublicAnnouncement,
    PublicDirectoryEntry,
    PublicEvent,
    PublicInquiry,
    PublicNews,
    PublicPage,
)

admin.site.register(OfficialLink)
admin.site.register(PublicAnnouncement)
admin.site.register(PublicDirectoryEntry)
admin.site.register(PublicEvent)
admin.site.register(PublicInquiry)
admin.site.register(PublicNews)
admin.site.register(PublicPage)
