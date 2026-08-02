from django.urls import path

from technician_app.views import *


urlpatterns = [
    path("student/tickets", StudentHelpdeskTickets.as_view()),
    path("technician/dashboard", TechnicianHelpdeskDashboard.as_view()),
    path("technician/elections", TechnicianElections.as_view()),
    path("technician/elections/<int:pk>", TechnicianElectionDetail.as_view()),
    path("technician/elections/candidates", TechnicianElectionsCandidates.as_view()),
    path("technician/elections/candidates/<int:pk>", TechnicianElectionCandidateDetail.as_view()),
    path("technician/elections/results", TechnicianElectionsResults.as_view()),
    path("technician/tickets/<int:pk>", TechnicianHelpdeskTicketDetail.as_view()),
    path("technician/venue-bookings", TechnicianVenueBookings.as_view()),
    path("technician/venue-bookings/<int:pk>/decision", TechnicianVenueBookingDecision.as_view()),
]
