from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from auth_app.views import (
    UmsTokenRefreshView,
    change_password,
    forgot_password,
    login,
    me,
    register,
    reset_password,
    send_email_verification,
    verify_email,
)
from core.media_access import protected_media

urlpatterns = [
    re_path(r'^media/(?P<path>.+)$', protected_media, name='protected_media'),
    path('super_admin/', admin.site.urls),
    path('auth/register', register.as_view()),
    path('auth/login', login.as_view()),
    path('auth/me', me.as_view()),
    path('auth/send-email-verification', send_email_verification.as_view()),
    path('auth/verify-email', verify_email.as_view()),
    path('auth/forgot-password', forgot_password.as_view()),
    path('auth/reset-password', reset_password.as_view()),
    path('auth/change-password', change_password.as_view()),
    path('auth/token/refresh', UmsTokenRefreshView.as_view()),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('finance/', include('accountant_app.urls')),
    path('admin/', include('admin_app.urls')),
    path('applicant/', include('applicant_app.urls')),
    path('canteen/', include('caterer_app.urls')),
    path('chatbot/', include('chatbot_app.urls')),
    path('executive/', include('executive_app.urls')),
    path('gradebook/', include('gradebook_app.urls')),
    path('hr/', include('hr_app.urls')),
    path('librarian/', include('librarian_app.urls')),
    path('quiz/', include('quiz_app.urls')),
    path('student/', include('student_app.urls')),
    path('teacher/', include('teacher_app.urls')),
    path('ict-helpdesk/', include('technician_app.urls')),
    re_path(r'^notifications/?', include('notifications_package.urls')),
    path('', include('home_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
