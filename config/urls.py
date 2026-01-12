from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from transparencia.views import get_carpetas_por_numeral

#Handlers de errores personalizados
from config.error_handlers import (
    handler404,
    handler500,
    handler403,
    handler400
)

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

#Configuración de handlers de errores personalizados
# Estos handlers se activan cuando DEBUG = False
handler404 = 'config.error_handlers.handler404'
handler500 = 'config.error_handlers.handler500'
handler403 = 'config.error_handlers.handler403'
handler400 = 'config.error_handlers.handler400'

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
