from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, DetailView, ListView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import SolicitudInformacion
from .forms import SolicitudInformacionForm


class SolicitudInformacionCreateView(CreateView):
    """
    Vista para crear una nueva solicitud de información
    """
    model = SolicitudInformacion
    form_class = SolicitudInformacionForm
    template_name = 'solicitudes/solicitud_form.html'
    success_url = reverse_lazy('solicitudes:solicitud_exito')
    
    def form_valid(self, form):
        # Guardar la solicitud
        solicitud = form.save(commit=False)
        
        # Guardar IP y User Agent
        solicitud.ip_address = self.get_client_ip()
        solicitud.user_agent = self.request.META.get('HTTP_USER_AGENT', '')[:255]
        
        solicitud.save()
        
        # Enviar correo electrónico
        self.enviar_notificacion_email(solicitud)
        
        # Guardar el número de seguimiento en la sesión
        self.request.session['numero_seguimiento'] = solicitud.numero_seguimiento
        
        messages.success(
            self.request,
            f'¡Solicitud enviada exitosamente! Su número de seguimiento es: {solicitud.numero_seguimiento}'
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Por favor, corrija los errores en el formulario.'
        )
        return super().form_invalid(form)
    
    def get_client_ip(self):
        """Obtiene la IP del cliente"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def enviar_notificacion_email(self, solicitud):
        """
        Envía notificación por correo electrónico
        """
        try:
            # Email al solicitante
            asunto_solicitante = f'Solicitud de Información - {solicitud.numero_seguimiento}'
            mensaje_solicitante = f"""
Estimado/a {solicitud.nombre_completo}:

Su solicitud de información pública ha sido recibida exitosamente.

Número de seguimiento: {solicitud.numero_seguimiento}
Fecha de solicitud: {solicitud.fecha_solicitud.strftime('%d/%m/%Y %H:%M')}

Solicitud:
{solicitud.solicitud}

Medio de entrega: {solicitud.get_medio_entrega_display()}

De acuerdo con la Ley de Acceso a la Información Pública (Decreto 57-2008), su solicitud será respondida en un plazo máximo de 10 días hábiles.

Podrá consultar el estado de su solicitud en cualquier momento utilizando su número de seguimiento.

Atentamente,
Unidad de Información Pública
Municipalidad de El Chal, Petén
            """
            
            send_mail(
                asunto_solicitante,
                mensaje_solicitante,
                settings.DEFAULT_FROM_EMAIL,
                [solicitud.correo_electronico],
                fail_silently=True,
            )
            
            # Email a la oficina de información pública
            asunto_oficina = f'Nueva Solicitud de Información - {solicitud.numero_seguimiento}'
            mensaje_oficina = f"""
Nueva solicitud de información pública recibida:

Número de seguimiento: {solicitud.numero_seguimiento}
Fecha: {solicitud.fecha_solicitud.strftime('%d/%m/%Y %H:%M')}

DATOS DEL SOLICITANTE:
- Nombre: {solicitud.nombre_completo}
- Lugar de residencia: {solicitud.lugar_residencia}
- Teléfono: {solicitud.telefono}
- Correo: {solicitud.correo_electronico}
- Género: {solicitud.get_genero_display() if solicitud.genero else 'No especificado'}

SOLICITUD:
{solicitud.solicitud}

MEDIO DE ENTREGA SOLICITADO:
{solicitud.get_medio_entrega_display()}

---
Para gestionar esta solicitud, ingrese al panel administrativo.
            """
            
            send_mail(
                asunto_oficina,
                mensaje_oficina,
                settings.DEFAULT_FROM_EMAIL,
                ['infopublica@munielchalpeten.gob.gt'],
                fail_silently=True,
            )
            
        except Exception as e:
            # Log del error pero no detener el proceso
            print(f"Error al enviar email: {e}")


class SolicitudExitoView(DetailView):
    """
    Vista de éxito después de crear una solicitud
    """
    template_name = 'solicitudes/solicitud_exito.html'
    
    def get_object(self):
        numero_seguimiento = self.request.session.get('numero_seguimiento')
        if numero_seguimiento:
            return get_object_or_404(SolicitudInformacion, numero_seguimiento=numero_seguimiento)
        return None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['solicitud'] = self.get_object()
        return context


class SolicitudConsultaView(ListView):
    """
    Vista para consultar el estado de una solicitud
    """
    model = SolicitudInformacion
    template_name = 'solicitudes/solicitud_consulta.html'
    context_object_name = 'solicitud'
    
    def get_queryset(self):
        numero = self.request.GET.get('numero', '')
        if numero:
            return SolicitudInformacion.objects.filter(numero_seguimiento__iexact=numero)
        return SolicitudInformacion.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['numero_busqueda'] = self.request.GET.get('numero', '')
        if context['object_list'].exists():
            context['solicitud'] = context['object_list'].first()
        return context


class EstadisticasSolicitudesView(ListView):
    """
    Vista de estadísticas públicas de solicitudes
    """
    model = SolicitudInformacion
    template_name = 'solicitudes/estadisticas.html'
    context_object_name = 'solicitudes'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estadisticas'] = SolicitudInformacion.get_estadisticas()
        
        # Solicitudes recientes (últimas 10)
        context['solicitudes_recientes'] = SolicitudInformacion.objects.all()[:10]
        
        return context