from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import SolicitudInformacion


@admin.register(SolicitudInformacion)
class SolicitudInformacionAdmin(admin.ModelAdmin):
    list_display = [
        'numero_seguimiento',
        'nombre_completo',
        'correo_electronico',
        'get_estado_badge',
        'medio_entrega',
        'fecha_solicitud',
        'get_dias_transcurridos',
        'get_acciones'
    ]
    list_filter = [
        'estado',
        'medio_entrega',
        'genero',
        'fecha_solicitud',
    ]
    search_fields = [
        'numero_seguimiento',
        'nombre_completo',
        'correo_electronico',
        'telefono',
        'solicitud',
    ]
    readonly_fields = [
        'numero_seguimiento',
        'fecha_solicitud',
        'ip_address',
        'user_agent',
        'get_dias_transcurridos',
    ]
    date_hierarchy = 'fecha_solicitud'
    ordering = ['-fecha_solicitud']
    
    fieldsets = (
        ('Información de Seguimiento', {
            'fields': ('numero_seguimiento', 'estado', 'fecha_solicitud', 'fecha_respuesta')
        }),
        ('Datos del Solicitante', {
            'fields': (
                'nombre_completo',
                'lugar_residencia',
                'telefono',
                'correo_electronico',
                'genero'
            )
        }),
        ('Solicitud', {
            'fields': ('solicitud', 'medio_entrega')
        }),
        ('Respuesta', {
            'fields': ('respuesta',),
            'classes': ('collapse',)
        }),
        ('Información Técnica', {
            'fields': ('ip_address', 'user_agent', 'get_dias_transcurridos'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'marcar_en_proceso',
        'marcar_respondida',
        'marcar_rechazada',
    ]
    
    def get_estado_badge(self, obj):
        color_map = {
            'pendiente': 'orange',
            'en_proceso': 'blue',
            'respondida': 'green',
            'rechazada': 'red',
        }
        color = color_map.get(obj.estado, 'gray')
        
        # Agregar alerta si está vencida
        alerta = ''
        if obj.esta_vencida():
            alerta = ' ⚠️ VENCIDA'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold; font-size: 11px;">{}{}</span>',
            color,
            obj.get_estado_display(),
            alerta
        )
    get_estado_badge.short_description = 'Estado'
    
    def get_dias_transcurridos(self, obj):
        dias = obj.dias_desde_solicitud()
        
        if obj.estado == 'pendiente':
            if dias > 10:
                return format_html(
                    '<span style="color: red; font-weight: bold;">{} días (VENCIDA)</span>',
                    dias
                )
            elif dias > 7:
                return format_html(
                    '<span style="color: orange; font-weight: bold;">{} días (URGENTE)</span>',
                    dias
                )
        
        return f"{dias} días"
    get_dias_transcurridos.short_description = 'Días transcurridos'
    
    def get_acciones(self, obj):
        html = f'<a href="/admin/solicitudes/solicitudinformacion/{obj.pk}/change/" style="margin-right: 10px;">Ver</a>'
        
        if obj.estado == 'pendiente':
            html += '<span style="color: orange;">⏳ Pendiente</span>'
        elif obj.estado == 'respondida':
            html += '<span style="color: green;">✓ Respondida</span>'
        
        return format_html(html)
    get_acciones.short_description = 'Acciones'
    
    def marcar_en_proceso(self, request, queryset):
        updated = queryset.update(estado='en_proceso')
        self.message_user(request, f'{updated} solicitud(es) marcada(s) como "En Proceso".')
    marcar_en_proceso.short_description = 'Marcar como "En Proceso"'
    
    def marcar_respondida(self, request, queryset):
        updated = queryset.update(estado='respondida', fecha_respuesta=timezone.now())
        self.message_user(request, f'{updated} solicitud(es) marcada(s) como "Respondida".')
    marcar_respondida.short_description = 'Marcar como "Respondida"'
    
    def marcar_rechazada(self, request, queryset):
        updated = queryset.update(estado='rechazada', fecha_respuesta=timezone.now())
        self.message_user(request, f'{updated} solicitud(es) marcada(s) como "Rechazada".')
    marcar_rechazada.short_description = 'Marcar como "Rechazada"'
    
    def changelist_view(self, request, extra_context=None):
        # Agregar estadísticas al contexto
        extra_context = extra_context or {}
        extra_context['estadisticas'] = SolicitudInformacion.get_estadisticas()
        return super().changelist_view(request, extra_context=extra_context)