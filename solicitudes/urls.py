from django.urls import path
from .views import (
    SolicitudInformacionCreateView,
    SolicitudExitoView,
    SolicitudConsultaView,
    EstadisticasSolicitudesView
)

app_name = 'solicitudes'

urlpatterns = [
    path('', SolicitudInformacionCreateView.as_view(), name='solicitud_create'),
    path('exito/', SolicitudExitoView.as_view(), name='solicitud_exito'),
    path('consulta/', SolicitudConsultaView.as_view(), name='solicitud_consulta'),
    path('estadisticas/', EstadisticasSolicitudesView.as_view(), name='estadisticas'),
]