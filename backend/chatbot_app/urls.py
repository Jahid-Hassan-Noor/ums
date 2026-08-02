from django.urls import path

from chatbot_app.search_views import ChatbotSearchView
from chatbot_app.views import ChatbotQueryView


urlpatterns = [
    path("query", ChatbotQueryView.as_view(), name="chatbot-query"),
    path("search", ChatbotSearchView.as_view(), name="chatbot-search"),
    path("search/", ChatbotSearchView.as_view(), name="chatbot-search-slash"),
]
