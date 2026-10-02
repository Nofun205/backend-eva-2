from django.contrib import admin
from django.urls import path, include, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    
    # Requisito de la rúbrica: Documentación Swagger / OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Frontend (Página principal tipo Coursera)
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # Catch-all para mostrar la página 404 personalizada incluso con DEBUG=True
    re_path(r'^.*/$', TemplateView.as_view(template_name='404.html')),
]
