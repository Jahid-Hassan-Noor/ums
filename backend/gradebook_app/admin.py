from django.contrib import admin

from gradebook_app.models import (
    GradebookCategory,
    GradebookGrade,
    GradebookGradeHistory,
    GradebookItem,
    GradebookScale,
    GradebookScaleRange,
)


admin.site.register(GradebookScale)
admin.site.register(GradebookScaleRange)
admin.site.register(GradebookCategory)
admin.site.register(GradebookItem)
admin.site.register(GradebookGrade)
admin.site.register(GradebookGradeHistory)
