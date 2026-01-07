from django.db import models
from django.core.validators import EmailValidator
from django.utils import timezone


class SolicitudInformacion(models.Model):
    """
    Modelo para las solicitudes de información pública
    """
    MEDIO_ENTREGA_CHOICES = [
        ('correo', 'Correo electrónico'),
        ('impreso', 'Impreso'),
        ('almacenamiento', 'Dispositivo de almacenamiento'),
    ]
    
    GENERO_CHOICES = [
        ('hombre', 'Hombre'),
        ('mujer', 'Mujer'),
        ('otro', 'Otro'),
        ('prefiero_no_decir', 'Prefiero no decir'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('respondida', 'Respondida'),
        ('rechazada', 'Rechazada'),
    ]
    
    # Datos del solicitante
    nombre_completo = models.CharField(
        max_length=200,
        verbose_name="Nombres y apellidos"
    )
    lugar_residencia = models.CharField(
        max_length=200,
        verbose_name="Lugar de residencia"
    )
    telefono = models.CharField(
        max_length=20,
        verbose_name="Teléfono"
    )
    correo_electronico = models.EmailField(
        validators=[EmailValidator()],
        verbose_name="Correo electrónico"
    )
    
    # Medio de entrega
    medio_entrega = models.CharField(
        max_length=20,
        choices=MEDIO_ENTREGA_CHOICES,
        default='correo',
        verbose_name="Medio de entrega"
    )
    
    # Género (opcional)
    genero = models.CharField(
        max_length=20,
        choices=GENERO_CHOICES,
        blank=True,
        verbose_name="Género"
    )
    
    # Solicitud
    solicitud = models.TextField(
        verbose_name="Solicitud",
        help_text="Descripción clara y precisa de la información solicitada"
    )
    
    # Estado y seguimiento
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name="Estado"
    )
    numero_seguimiento = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name="Número de seguimiento"
    )
    
    # Fechas
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de solicitud"
    )
    fecha_respuesta = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de respuesta"
    )
    
    # Respuesta
    respuesta = models.TextField(
        blank=True,
        verbose_name="Respuesta"
    )
    
    # Metadatos
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Dirección IP"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )
    
    class Meta:
        verbose_name = "Solicitud de Información"
        verbose_name_plural = "Solicitudes de Información"
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['-fecha_solicitud']),
            models.Index(fields=['estado']),
            models.Index(fields=['numero_seguimiento']),
        ]
    
    def __str__(self):
        return f"{self.numero_seguimiento} - {self.nombre_completo}"
    
    def save(self, *args, **kwargs):
        if not self.numero_seguimiento:
            # Generar número de seguimiento único
            from django.utils.crypto import get_random_string
            import datetime
            fecha = datetime.datetime.now()
            year = fecha.strftime('%Y')
            month = fecha.strftime('%m')
            day = fecha.strftime('%d')
            random_code = get_random_string(length=6, allowed_chars='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            self.numero_seguimiento = f"SI-{year}{month}{day}-{random_code}"
        super().save(*args, **kwargs)
    
    def get_estado_display_color(self):
        """Retorna el color para el estado"""
        colores = {
            'pendiente': 'yellow',
            'en_proceso': 'blue',
            'respondida': 'green',
            'rechazada': 'red',
        }
        return colores.get(self.estado, 'gray')
    
    def dias_desde_solicitud(self):
        """Calcula los días desde que se hizo la solicitud"""
        from django.utils import timezone
        delta = timezone.now() - self.fecha_solicitud
        return delta.days
    
    def esta_vencida(self):
        """Verifica si la solicitud está vencida (más de 10 días según la ley)"""
        return self.dias_desde_solicitud() > 10 and self.estado == 'pendiente'
    
    @classmethod
    def get_estadisticas(cls):
        """Retorna estadísticas de las solicitudes"""
        from django.db.models import Count
        return {
            'total': cls.objects.count(),
            'pendientes': cls.objects.filter(estado='pendiente').count(),
            'en_proceso': cls.objects.filter(estado='en_proceso').count(),
            'respondidas': cls.objects.filter(estado='respondida').count(),
            'rechazadas': cls.objects.filter(estado='rechazada').count(),
            'vencidas': cls.objects.filter(
                estado='pendiente',
                fecha_solicitud__lt=timezone.now() - timezone.timedelta(days=10)
            ).count(),
        }