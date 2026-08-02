from django.urls import path

from gradebook_app.views import AdminGradebook, StudentGradebook, TeacherGradebook


urlpatterns = [
    path("admin", AdminGradebook.as_view()),
    path("teacher", TeacherGradebook.as_view()),
    path("student", StudentGradebook.as_view()),
]
