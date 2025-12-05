from django.urls import path
from .views import (
    NumeralListView,
    NumeralDetailView,
    CarpetaDetailView,
    DocumentoDownloadView,
    BusquedaView,
    EstadisticasView
)

app_name = 'transparencia'

urlpatterns = [
    # Página principal - Lista de numerales
    path('', NumeralListView.as_view(), name='numeral_list'),
    
    # Detalle de un numeral específico
    path('numeral/<slug:slug>/', NumeralDetailView.as_view(), name='numeral_detail'),
    
    # Detalle de una carpeta específica
    path('carpeta/<int:pk>/', CarpetaDetailView.as_view(), name='carpeta_detail'),
    
    # Descarga de documento
    path('documento/<int:pk>/descargar/', DocumentoDownloadView.as_view(), name='documento_download'),
    
    # Búsqueda de documentos
    path('buscar/', BusquedaView.as_view(), name='busqueda'),
    
    # Estadísticas
    path('estadisticas/', EstadisticasView.as_view(), name='estadisticas'),
]