from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.asistencia.views import ServiceWorkerView

urlpatterns = [
    # 1. TU LOGIN PERSONALIZADO (Va primero para ganar prioridad)
    path('accounts/login/', auth_views.LoginView.as_view(template_name='asistencia/login.html'), name='login'),

    # 2. TU LOGOUT
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('sw.js', ServiceWorkerView.as_view(), name='sw_js'),

    # 3. ADMIN Y EL RESTO DE LA APP
    path('admin/', admin.site.urls),
    path('', include('apps.asistencia.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)