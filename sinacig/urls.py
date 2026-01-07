from django.urls import path
from .views import (
    CarpetaSINACIGListView,
    CarpetaSINACIGDetailView,
    DocumentoSINACIGDownloadView,
    BusquedaSINACIGView,
    EstadisticasSINACIGView
)

app_name = 'sinacig'

urlpatterns = [
    path('', CarpetaSINACIGListView.as_view(), name='carpeta_list'),
    path('carpeta/<int:pk>/', CarpetaSINACIGDetailView.as_view(), name='carpeta_detail'),
    path('documento/<int:pk>/descargar/', DocumentoSINACIGDownloadView.as_view(), name='documento_download'),
    path('buscar/', BusquedaSINACIGView.as_view(), name='busqueda'),
    path('estadisticas/', EstadisticasSINACIGView.as_view(), name='estadisticas'),
]