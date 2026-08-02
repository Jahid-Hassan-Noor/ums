from django.urls import path

from caterer_app.views import *


urlpatterns = [
    path("", CatererUms.as_view()),
    path("dashboard", CatererDashboard.as_view()),
    path("student", CatererStudentAccount.as_view()),
    path("transactions", CatererTransactions.as_view()),
]

