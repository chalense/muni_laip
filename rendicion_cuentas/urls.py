from django.urls import path
from .views import (
    NumeralRendicionListView,
    NumeralRendicionDetailView,
    CarpetaRendicionDetailView,
    DocumentoRendicionDownloadView,
    BusquedaRendicionView,
    EstadisticasRendicionView
)

app_name = 'rendicion_cuentas'

urlpatterns = [
    path('', NumeralRendicionListView.as_view(), name='numeral_list'),
    path('numeral/<slug:slug>/', NumeralRendicionDetailView.as_view(), name='numeral_detail'),
    path('carpeta/<int:pk>/', CarpetaRendicionDetailView.as_view(), name='carpeta_detail'),
    path('documento/<int:pk>/descargar/', DocumentoRendicionDownloadView.as_view(), name='documento_download'),
    path('buscar/', BusquedaRendicionView.as_view(), name='busqueda'),
    path('estadisticas/', EstadisticasRendicionView.as_view(), name='estadisticas'),
]