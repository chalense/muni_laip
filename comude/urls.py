from django.urls import path
from .views import (
    NumeralComudeListView,
    NumeralComudeDetailView,
    CarpetaComudeDetailView,
    DocumentoComudeDownloadView,
    BusquedaComudeView,
    EstadisticasComudeView
)

app_name = 'comude'

urlpatterns = [
    path('', NumeralComudeListView.as_view(), name='numeral_list'),
    path('numeral/<slug:slug>/', NumeralComudeDetailView.as_view(), name='numeral_detail'),
    path('carpeta/<int:pk>/', CarpetaComudeDetailView.as_view(), name='carpeta_detail'),
    path('documento/<int:pk>/descargar/', DocumentoComudeDownloadView.as_view(), name='documento_download'),
    path('buscar/', BusquedaComudeView.as_view(), name='busqueda'),
    path('estadisticas/', EstadisticasComudeView.as_view(), name='estadisticas'),
]