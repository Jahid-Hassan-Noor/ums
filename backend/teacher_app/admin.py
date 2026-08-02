from django.contrib import admin
from .models import (
    Assignment,
    AssignmentAttachment,
    AssignmentComment,
    AssignmentFeedback,
    AssignmentRubric,
    AttendanceSession,
    CourseActivity,
    CourseAnnouncement,
    CourseResource,
    CourseResourceFolder,
    CourseSection,
    ResultSubmission,
    AssignmentSubmission,
    Teacher,
)

admin.site.register(Assignment)
admin.site.register(AssignmentAttachment)
admin.site.register(AssignmentComment)
admin.site.register(AssignmentFeedback)
admin.site.register(AssignmentRubric)
admin.site.register(AttendanceSession)
admin.site.register(CourseActivity)
admin.site.register(CourseAnnouncement)
admin.site.register(CourseResource)
admin.site.register(CourseResourceFolder)
admin.site.register(CourseSection)
admin.site.register(ResultSubmission)
admin.site.register(AssignmentSubmission)
admin.site.register(Teacher)
