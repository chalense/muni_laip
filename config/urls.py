"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from transparencia.views import get_carpetas_por_numeral

urlpatterns = [
    path("admin/", admin.site.urls),
    
    #vista ajax para filtrado de carpetas en el admin
    path('admin/get-carpetas-por-numeral/', get_carpetas_por_numeral, name='get_carpetas_por_numeral'),
    
     # Aplicación de transparencia (página principal)
    path('', include('home.urls')),
    
    # Redirección alternativa
    path('articulo-10/', include('transparencia.urls')),
    path('comude/', include('comude.urls')),
    path('rendicion-cuentas/', include('rendicion_cuentas.urls')),
    path('informes-congreso/', include('informes_congreso.urls')),
    path('sinacig/', include('sinacig.urls')),
    path('solicitudes/', include('solicitudes.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
