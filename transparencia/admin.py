from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Numeral, Carpeta, Documento


@admin.register(Numeral)
class NumeralAdmin(admin.ModelAdmin):
    """
    Administración de Numerales del Artículo 10
    """
    list_display = [
        'codigo_badge',
        'titulo_corto',
        'activo_badge',
        'total_carpetas',
        'total_docs',
        'actualizado_en'
    ]
    list_filter = ['activo', 'creado_en', 'actualizado_en']
    search_fields = ['codigo', 'titulo_corto', 'descripcion']
    prepopulated_fields = {'slug': ('codigo', 'titulo_corto')}
    readonly_fields = ['slug', 'creado_en', 'actualizado_en', 'vista_previa']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('codigo', 'titulo_corto', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('activo', 'orden', 'slug')
        }),
        ('Metadatos', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
        ('Vista Previa', {
            'fields': ('vista_previa',),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 30
    ordering = ['orden', 'codigo']
    
    def codigo_badge(self, obj):
        """Muestra el código con badge colorido"""
        return format_html(
            '<span style="background-color: #3B82F6; color: white; '
            'padding: 4px 12px; border-radius: 9999px; font-weight: bold; '
            'font-size: 13px;">{}</span>',
            obj.codigo
        )
    codigo_badge.short_description = 'Código'
    
    def activo_badge(self, obj):
        """Muestra estado activo/inactivo con colores"""
        if obj.activo:
            return format_html(
                '<span style="background-color: #10B981; color: white; '
                'padding: 3px 10px; border-radius: 12px; font-size: 11px; '
                'font-weight: 600;">✓ ACTIVO</span>'
            )
        return format_html(
            '<span style="background-color: #EF4444; color: white; '
            'padding: 3px 10px; border-radius: 12px; font-size: 11px; '
            'font-weight: 600;">✗ INACTIVO</span>'
        )
    activo_badge.short_description = 'Estado'
    
    def total_carpetas(self, obj):
        """Cuenta total de carpetas raíz (años)"""
        total = obj.carpetas.filter(padre__isnull=True).count()
        return format_html(
            '<span style="color: #059669; font-weight: 600;">📁 {}</span>',
            total
        )
    total_carpetas.short_description = 'Carpetas'
    
    def total_docs(self, obj):
        """Cuenta total de documentos publicados"""
        total = obj.documentos.filter(publicado=True).count()
        color = '#10B981' if total > 0 else '#6B7280'
        return format_html(
            '<span style="color: {}; font-weight: 600;">📄 {}</span>',
            color, total
        )
    total_docs.short_description = 'Documentos'
    
    def vista_previa(self, obj):
        """Genera una vista previa del numeral con estadísticas"""
        if not obj.pk:
            return "Guarda el numeral primero para ver la vista previa"
        
        total_docs = obj.documentos.filter(publicado=True).count()
        total_carpetas = obj.carpetas.filter(padre__isnull=True).count()
        total_descargas = sum(
            doc.descargas for doc in obj.documentos.all()
        )
        
        url = obj.get_absolute_url() if obj.activo else '#'
        
        html = f'''
        <div style="background: #F3F4F6; padding: 20px; border-radius: 8px; 
                    border-left: 4px solid #3B82F6;">
            <h3 style="margin: 0 0 15px 0; color: #1F2937;">
                📋 Numeral {obj.codigo}: {obj.titulo_corto}
            </h3>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); 
                        gap: 15px; margin-bottom: 15px;">
                <div style="background: white; padding: 12px; border-radius: 6px;">
                    <div style="color: #6B7280; font-size: 12px;">Carpetas</div>
                    <div style="color: #059669; font-size: 24px; font-weight: bold;">
                        {total_carpetas}
                    </div>
                </div>
                <div style="background: white; padding: 12px; border-radius: 6px;">
                    <div style="color: #6B7280; font-size: 12px;">Documentos</div>
                    <div style="color: #3B82F6; font-size: 24px; font-weight: bold;">
                        {total_docs}
                    </div>
                </div>
                <div style="background: white; padding: 12px; border-radius: 6px;">
                    <div style="color: #6B7280; font-size: 12px;">Descargas</div>
                    <div style="color: #F59E0B; font-size: 24px; font-weight: bold;">
                        {total_descargas}
                    </div>
                </div>
            </div>
            {f'<a href="{url}" target="_blank" style="display: inline-block; background: #3B82F6; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: 600;">Ver en el sitio público →</a>' if obj.activo else '<span style="color: #EF4444;">⚠️ Numeral inactivo - no visible públicamente</span>'}
        </div>
        '''
        return mark_safe(html)
    vista_previa.short_description = 'Vista Previa y Estadísticas'
    
    def get_queryset(self, request):
        """Optimiza las consultas con anotaciones"""
        qs = super().get_queryset(request)
        return qs.annotate(
            total_documentos=Count('documentos', filter=Q(documentos__publicado=True))
        )


@admin.register(Carpeta)
class CarpetaAdmin(admin.ModelAdmin):
    """
    Administración de Carpetas (estructura jerárquica)
    """
    list_display = [
        'icono_nivel',
        'nombre_jerarquico',
        'numeral_link',
        'total_docs_badge',
        'orden',
        'creado_en'
    ]
    list_filter = [
        'numeral',
        'padre',
        'creado_en'
    ]
    search_fields = ['nombre', 'descripcion', 'numeral__titulo_corto']
    autocomplete_fields = ['numeral', 'padre']
    readonly_fields = ['creado_en', 'actualizado_en', 'info_jerarquia']
    
    fieldsets = (
        ('Información de la Carpeta', {
            'fields': ('nombre', 'descripcion')
        }),
        ('Ubicación', {
            'fields': ('numeral', 'padre', 'orden')
        }),
        ('Metadatos', {
            'fields': ('creado_en', 'actualizado_en', 'info_jerarquia'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    ordering = ['numeral', '-orden', '-nombre']
    
    def icono_nivel(self, obj):
        """Muestra ícono según el nivel de la carpeta"""
        nivel = obj.nivel()
        iconos = {
            0: '📅',  # Año (raíz)
            1: '📁',  # Mes
            2: '📂',  # Subcarpeta
        }
        icono = iconos.get(nivel, '📄')
        color = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'][min(nivel, 3)]
        
        return format_html(
            '<span style="font-size: 20px;" title="Nivel {}">{}</span>',
            nivel, icono
        )
    icono_nivel.short_description = ''
    
    def nombre_jerarquico(self, obj):
        """Muestra el nombre con indentación según nivel"""
        nivel = obj.nivel()
        indent = '&nbsp;&nbsp;&nbsp;&nbsp;' * nivel
        
        if nivel == 0:
            estilo = 'font-weight: bold; color: #1F2937; font-size: 14px;'
        elif nivel == 1:
            estilo = 'font-weight: 600; color: #374151;'
        else:
            estilo = 'color: #6B7280;'
        
        return format_html(
            '{}<span style="{}">{}</span>',
            mark_safe(indent), estilo, obj.nombre
        )
    nombre_jerarquico.short_description = 'Nombre'
    
    def numeral_link(self, obj):
        """Enlace al numeral"""
        url = reverse('admin:transparencia_numeral_change', args=[obj.numeral.pk])
        return format_html(
            '<a href="{}" style="color: #3B82F6; text-decoration: none;">'
            '📋 Numeral {}</a>',
            url, obj.numeral.codigo
        )
    numeral_link.short_description = 'Numeral'
    
    def total_docs_badge(self, obj):
        """Muestra total de documentos con badge"""
        total = obj.total_documentos()
        color = '#10B981' if total > 0 else '#D1D5DB'
        text_color = 'white' if total > 0 else '#6B7280'
        
        return format_html(
            '<span style="background-color: {}; color: {}; '
            'padding: 3px 10px; border-radius: 12px; font-size: 11px; '
            'font-weight: 600;">📄 {}</span>',
            color, text_color, total
        )
    total_docs_badge.short_description = 'Docs'
    
    def info_jerarquia(self, obj):
        """Información detallada de la jerarquía"""
        if not obj.pk:
            return "Guarda la carpeta primero"
        
        nivel = obj.nivel()
        ruta = obj.get_ruta_completa()
        total_docs = obj.total_documentos()
        total_docs_recursivo = obj.total_documentos_recursivo()
        subcarpetas = obj.subcarpetas.count()
        
        html = f'''
        <div style="background: #F9FAFB; padding: 15px; border-radius: 6px; 
                    border: 1px solid #E5E7EB;">
            <div style="margin-bottom: 12px;">
                <strong style="color: #374151;">Ruta Completa:</strong>
                <div style="background: white; padding: 8px; margin-top: 5px; 
                           border-radius: 4px; font-family: monospace; color: #3B82F6;">
                    {ruta}
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
                <div>
                    <div style="color: #6B7280; font-size: 11px;">NIVEL</div>
                    <div style="color: #1F2937; font-weight: 600;">{nivel}</div>
                </div>
                <div>
                    <div style="color: #6B7280; font-size: 11px;">DOCUMENTOS</div>
                    <div style="color: #3B82F6; font-weight: 600;">{total_docs}</div>
                </div>
                <div>
                    <div style="color: #6B7280; font-size: 11px;">DOCS TOTAL</div>
                    <div style="color: #10B981; font-weight: 600;">{total_docs_recursivo}</div>
                </div>
                <div>
                    <div style="color: #6B7280; font-size: 11px;">SUBCARPETAS</div>
                    <div style="color: #F59E0B; font-weight: 600;">{subcarpetas}</div>
                </div>
            </div>
        </div>
        '''
        return mark_safe(html)
    info_jerarquia.short_description = 'Información de Jerarquía'


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    """
    Administración de Documentos
    """
    list_display = [
        'extension_badge',
        'titulo',
        'numeral_link',
        'carpeta_ruta',
        'tamanio_badge',
        'descargas_badge',
        'estado_badge',
        'fecha_publicacion'
    ]
    list_filter = [
        'publicado',
        'destacado',
        'extension',
        'numeral',
        'fecha_publicacion'
    ]
    search_fields = ['titulo', 'descripcion', 'numeral__titulo_corto']
    autocomplete_fields = ['numeral', 'carpeta']
    readonly_fields = [
        'tamanio_bytes',
        'extension',
        'descargas',
        'fecha_publicacion',
        'fecha_actualizacion',
        'preview_documento'
    ]
    
    fieldsets = (
        ('Información del Documento', {
            'fields': ('titulo', 'descripcion', 'archivo')
        }),
        ('Ubicación', {
            'fields': ('numeral', 'carpeta')
        }),
        ('Estado', {
            'fields': ('publicado', 'destacado')
        }),
        ('Metadatos del Archivo', {
            'fields': ('extension', 'tamanio_bytes', 'descargas'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_publicacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
        ('Vista Previa', {
            'fields': ('preview_documento',),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    date_hierarchy = 'fecha_publicacion'
    ordering = ['-fecha_publicacion']
    
    actions = ['publicar_documentos', 'despublicar_documentos', 'marcar_destacados']
    
    def extension_badge(self, obj):
        """Badge con el tipo de archivo"""
        colores = {
            'PDF': '#EF4444',
            'XLS': '#10B981',
            'XLSX': '#10B981',
            'DOC': '#3B82F6',
            'DOCX': '#3B82F6',
            'PNG': '#8B5CF6',
            'JPG': '#8B5CF6',
            'JPEG': '#8B5CF6',
            'SVG': '#8B5CF6',
            'CSV': '#F59E0B',
        }
        color = colores.get(obj.extension, '#6B7280')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 4px 8px; border-radius: 4px; font-size: 11px; '
            'font-weight: bold; font-family: monospace;">{}</span>',
            color, obj.extension
        )
    extension_badge.short_description = 'Tipo'
    
    def numeral_link(self, obj):
        """Enlace al numeral"""
        url = reverse('admin:transparencia_numeral_change', args=[obj.numeral.pk])
        return format_html(
            '<a href="{}" style="color: #3B82F6; font-weight: 600; '
            'text-decoration: none;">Numeral {}</a>',
            url, obj.numeral.codigo
        )
    numeral_link.short_description = 'Numeral'
    
    def carpeta_ruta(self, obj):
        """Muestra la ruta de la carpeta"""
        if obj.carpeta:
            return format_html(
                '<span style="color: #6B7280; font-size: 12px;">📁 {}</span>',
                obj.carpeta.get_ruta_completa()
            )
        return format_html(
            '<span style="color: #D1D5DB; font-style: italic;">Sin carpeta</span>'
        )
    carpeta_ruta.short_description = 'Ubicación'
    
    def tamanio_badge(self, obj):
        """Muestra el tamaño del archivo"""
        tamanio = obj.tamanio_legible()
        return format_html(
            '<span style="color: #6B7280; font-size: 12px; font-weight: 600;">{}</span>',
            tamanio
        )
    tamanio_badge.short_description = 'Tamaño'
    
    def descargas_badge(self, obj):
        """Muestra el número de descargas"""
        if obj.descargas > 100:
            color = '#10B981'
        elif obj.descargas > 10:
            color = '#F59E0B'
        else:
            color = '#6B7280'
        
        return format_html(
            '<span style="color: {}; font-weight: 600;">⬇ {}</span>',
            color, obj.descargas
        )
    descargas_badge.short_description = 'Descargas'
    
    def estado_badge(self, obj):
        """Badge de estado publicado/destacado"""
        badges = []
        
        if obj.publicado:
            badges.append(
                '<span style="background-color: #10B981; color: white; '
                'padding: 2px 8px; border-radius: 10px; font-size: 10px; '
                'font-weight: 600; margin-right: 4px;">✓ Publicado</span>'
            )
        else:
            badges.append(
                '<span style="background-color: #EF4444; color: white; '
                'padding: 2px 8px; border-radius: 10px; font-size: 10px; '
                'font-weight: 600; margin-right: 4px;">✗ Oculto</span>'
            )
        
        if obj.destacado:
            badges.append(
                '<span style="background-color: #F59E0B; color: white; '
                'padding: 2px 8px; border-radius: 10px; font-size: 10px; '
                'font-weight: 600;">⭐ Destacado</span>'
            )
        
        return format_html(''.join(badges))
    estado_badge.short_description = 'Estado'
    
    def preview_documento(self, obj):
        """Vista previa del documento"""
        if not obj.pk:
            return "Guarda el documento primero"
        
        html = f'''
        <div style="background: #F9FAFB; padding: 20px; border-radius: 8px; 
                    border: 1px solid #E5E7EB;">
            <div style="display: flex; align-items: start; gap: 20px;">
                <div style="background: white; padding: 20px; border-radius: 8px; 
                           text-align: center; border: 2px solid #E5E7EB;">
                    <div style="font-size: 48px; margin-bottom: 10px;">📄</div>
                    <div style="background: {obj.get_color_tailwind()['bg']}; 
                               color: {obj.get_color_tailwind()['text']}; 
                               padding: 4px 12px; border-radius: 4px; 
                               font-weight: bold; font-size: 12px;">
                        {obj.extension}
                    </div>
                </div>
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 10px 0; color: #1F2937;">{obj.titulo}</h3>
                    <div style="color: #6B7280; font-size: 13px; line-height: 1.6;">
                        <p><strong>Tamaño:</strong> {obj.tamanio_legible()}</p>
                        <p><strong>Descargas:</strong> {obj.descargas}</p>
                        <p><strong>Ubicación:</strong> {obj.get_ruta_completa()}</p>
                        <p><strong>Publicado:</strong> {obj.fecha_publicacion.strftime('%d/%m/%Y %H:%M')}</p>
                    </div>
                    <a href="{obj.archivo.url}" target="_blank" 
                       style="display: inline-block; margin-top: 12px; 
                              background: #3B82F6; color: white; padding: 8px 16px; 
                              border-radius: 6px; text-decoration: none; 
                              font-weight: 600; font-size: 13px;">
                        Descargar Archivo →
                    </a>
                </div>
            </div>
        </div>
        '''
        return mark_safe(html)
    preview_documento.short_description = 'Vista Previa del Documento'
    
    # Acciones masivas
    def publicar_documentos(self, request, queryset):
        """Acción para publicar documentos seleccionados"""
        updated = queryset.update(publicado=True)
        self.message_user(request, f'{updated} documento(s) publicado(s) correctamente.')
    publicar_documentos.short_description = "✓ Publicar documentos seleccionados"
    
    def despublicar_documentos(self, request, queryset):
        """Acción para ocultar documentos seleccionados"""
        updated = queryset.update(publicado=False)
        self.message_user(request, f'{updated} documento(s) ocultado(s) correctamente.')
    despublicar_documentos.short_description = "✗ Ocultar documentos seleccionados"
    
    def marcar_destacados(self, request, queryset):
        """Acción para marcar documentos como destacados"""
        updated = queryset.update(destacado=True)
        self.message_user(request, f'{updated} documento(s) marcado(s) como destacado(s).')
    marcar_destacados.short_description = "⭐ Marcar como destacados"


# Personalización del Admin Site
admin.site.site_header = "Sistema de Transparencia Municipal"
admin.site.site_title = "Administración - El Chal, Petén"
admin.site.index_title = "Panel de Control - Ley de Información Pública"