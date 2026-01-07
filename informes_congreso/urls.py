from django.urls import path
from .views import (
    NumeralInformesCongresoListView,
    NumeralInformesCongresoDetailView,
    CarpetaInformesCongresoDetailView,
    DocumentoInformesCongresoDownloadView,
    BusquedaInformesCongresoView,
    EstadisticasInformesCongresoView
)

app_name = 'informes_congreso'

urlpatterns = [
    path('', NumeralInformesCongresoListView.as_view(), name='numeral_list'),
    path('numeral/<slug:slug>/', NumeralInformesCongresoDetailView.as_view(), name='numeral_detail'),
    path('carpeta/<int:pk>/', CarpetaInformesCongresoDetailView.as_view(), name='carpeta_detail'),
    path('documento/<int:pk>/descargar/', DocumentoInformesCongresoDownloadView.as_view(), name='documento_download'),
    path('buscar/', BusquedaInformesCongresoView.as_view(), name='busqueda'),
    path('estadisticas/', EstadisticasInformesCongresoView.as_view(), name='estadisticas'),
]