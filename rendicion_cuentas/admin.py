from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import NumeralRendicion, CarpetaRendicion, DocumentoRendicion


@admin.register(NumeralRendicion)
class NumeralRendicionAdmin(admin.ModelAdmin):
    """Admin para Numerales de Rendición de Cuentas"""
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
    readonly_fields = ['slug', 'creado_en', 'actualizado_en']
    
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
    )
    
    list_per_page = 30
    ordering = ['orden', 'codigo']
    
    def codigo_badge(self, obj):
        return format_html(
            '<span style="background-color: #F59E0B; color: white; '
            'padding: 4px 12px; border-radius: 9999px; font-weight: bold; '
            'font-size: 13px;">{}</span>',
            obj.codigo
        )
    codigo_badge.short_description = 'Código'
    
    def activo_badge(self, obj):
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
        total = obj.carpetas.filter(padre__isnull=True).count()
        return format_html(
            '<span style="color: #F59E0B; font-weight: 600;">📁 {}</span>',
            total
        )
    total_carpetas.short_description = 'Carpetas'
    
    def total_docs(self, obj):
        total = obj.documentos.filter(publicado=True).count()
        color = '#10B981' if total > 0 else '#6B7280'
        return format_html(
            '<span style="color: {}; font-weight: 600;">📄 {}</span>',
            color, total
        )
    total_docs.short_description = 'Documentos'


@admin.register(CarpetaRendicion)
class CarpetaRendicionAdmin(admin.ModelAdmin):
    """Admin para Carpetas de Rendición de Cuentas"""
    list_display = [
        'icono_nivel',
        'nombre_jerarquico',
        'numeral_link',
        'total_docs_badge',
        'orden',
        'creado_en'
    ]
    list_filter = ['numeral', 'padre', 'creado_en']
    search_fields = ['nombre', 'descripcion', 'numeral__titulo_corto']
    autocomplete_fields = ['numeral', 'padre']
    readonly_fields = ['creado_en', 'actualizado_en']
    
    list_per_page = 50
    ordering = ['numeral', '-orden', '-nombre']
    
    def icono_nivel(self, obj):
        nivel = obj.nivel()
        iconos = {0: '📅', 1: '📁', 2: '📂'}
        icono = iconos.get(nivel, '📄')
        return format_html('<span style="font-size: 20px;">{}</span>', icono)
    icono_nivel.short_description = ''
    
    def nombre_jerarquico(self, obj):
        nivel = obj.nivel()
        indent = '&nbsp;&nbsp;&nbsp;&nbsp;' * nivel
        if nivel == 0:
            estilo = 'font-weight: bold; color: #1F2937; font-size: 14px;'
        elif nivel == 1:
            estilo = 'font-weight: 600; color: #374151;'
        else:
            estilo = 'color: #6B7280;'
        return format_html('{}<span style="{}">{}</span>', mark_safe(indent), estilo, obj.nombre)
    nombre_jerarquico.short_description = 'Nombre'
    
    def numeral_link(self, obj):
        url = reverse('admin:rendicion_cuentas_numeralrendicion_change', args=[obj.numeral.pk])
        return format_html('<a href="{}" style="color: #F59E0B;">📋 {}</a>', url, obj.numeral.codigo)
    numeral_link.short_description = 'Numeral'
    
    def total_docs_badge(self, obj):
        total = obj.total_documentos()
        color = '#F59E0B' if total > 0 else '#D1D5DB'
        text_color = 'white' if total > 0 else '#6B7280'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">📄 {}</span>',
            color, text_color, total
        )
    total_docs_badge.short_description = 'Docs'


@admin.register(DocumentoRendicion)
class DocumentoRendicionAdmin(admin.ModelAdmin):
    """Admin para Documentos de Rendición de Cuentas"""
    
    # Filtro personalizado para ubicación
    class UbicacionFilter(admin.SimpleListFilter):
        title = 'ubicación'
        parameter_name = 'ubicacion'
        
        def lookups(self, request, model_admin):
            return (
                ('raiz', '📋 En raíz del numeral'),
                ('carpetas', '📁 En carpetas'),
            )
        
        def queryset(self, request, queryset):
            if self.value() == 'raiz':
                return queryset.filter(carpeta__isnull=True)
            if self.value() == 'carpetas':
                return queryset.filter(carpeta__isnull=False)
            return queryset
    
    list_display = [
        'extension_badge',
        'titulo',
        'numeral_link',
        'carpeta_ruta',
        'tamanio_badge',
        'descargas_badge',
        'estado_badge',
        'fecha_publicacion',
        'acciones_rapidas'
    ]
    
    list_filter = [
        'publicado',
        'destacado',
        UbicacionFilter,
        'extension',
        'numeral',
        ('fecha_publicacion', admin.DateFieldListFilter),
    ]
    
    search_fields = ['titulo', 'descripcion', 'numeral__titulo_corto']
    autocomplete_fields = ['numeral']
    readonly_fields = ['tamanio_bytes', 'extension', 'descargas', 'fecha_publicacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información del Documento', {
            'fields': ('titulo', 'descripcion', 'archivo')
        }),
        ('Ubicación', {
            'fields': ('numeral', 'carpeta'),
            'description': '''
                <div style="background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 12px; margin: 10px 0; border-radius: 4px;">
                    <strong style="color: #92400E;">💡 Importante sobre la ubicación:</strong>
                    <ul style="margin: 8px 0 0 0; padding-left: 20px; color: #B45309;">
                        <li><strong>Sin carpeta (Raíz):</strong> Deja el campo "Carpeta" vacío para que el documento aparezca directamente en el numeral.</li>
                        <li><strong>Con carpeta:</strong> Selecciona una carpeta para organizar el documento por año/mes.</li>
                        <li><strong>Crear carpetas:</strong> Ve a <a href="/admin/rendicion_cuentas/carpetarendicion/add/" style="color: #F59E0B; font-weight: 600;">Carpetas > Agregar carpeta</a>.</li>
                    </ul>
                </div>
            '''
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
    )
    
    list_per_page = 50
    date_hierarchy = 'fecha_publicacion'
    ordering = ['-fecha_publicacion']
    
    actions = ['publicar_documentos', 'despublicar_documentos', 'marcar_destacados']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtra las carpetas según el numeral seleccionado"""
        if db_field.name == "carpeta":
            obj_id = request.resolver_match.kwargs.get('object_id')
            
            if obj_id:
                try:
                    documento = DocumentoRendicion.objects.get(pk=obj_id)
                    kwargs["queryset"] = CarpetaRendicion.objects.filter(
                        numeral=documento.numeral
                    ).select_related('padre')
                except DocumentoRendicion.DoesNotExist:
                    kwargs["queryset"] = CarpetaRendicion.objects.none()
            else:
                numeral_id = request.POST.get('numeral') or request.GET.get('numeral')
                
                if numeral_id:
                    kwargs["queryset"] = CarpetaRendicion.objects.filter(
                        numeral_id=numeral_id
                    ).select_related('padre')
                else:
                    kwargs["queryset"] = CarpetaRendicion.objects.none()
            
            def label_from_instance(obj):
                return f"{obj.get_ruta_completa()}"
            
            form_field = super().formfield_for_foreignkey(db_field, request, **kwargs)
            form_field.label_from_instance = label_from_instance
            form_field.required = False
            
            return form_field
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_form(self, request, obj=None, **kwargs):
        """Personaliza el formulario"""
        form = super().get_form(request, obj, **kwargs)
        
        if 'carpeta' in form.base_fields:
            form.base_fields['carpeta'].required = False
            
            if obj and obj.numeral:
                form.base_fields['carpeta'].help_text = f'''
                    <span style="color: #B45309; font-weight: 600;">📁 Carpetas del Numeral {obj.numeral.codigo}</span><br>
                    <span style="color: #6B7280;">Deja vacío para subir a la raíz del numeral (sin carpetas)</span>
                '''
            else:
                form.base_fields['carpeta'].help_text = '''
                    <span style="color: #DC2626; font-weight: 600;">⚠️ Primero selecciona un Numeral</span><br>
                    <span style="color: #6B7280;">Luego podrás elegir una carpeta o dejarlo vacío para la raíz</span>
                '''
        
        return form
    
    def extension_badge(self, obj):
        colores = {
            'PDF': '#EF4444', 'XLS': '#10B981', 'XLSX': '#10B981',
            'DOC': '#3B82F6', 'DOCX': '#3B82F6', 'PNG': '#8B5CF6',
            'JPG': '#8B5CF6', 'JPEG': '#8B5CF6', 'SVG': '#8B5CF6', 'CSV': '#F59E0B',
        }
        color = colores.get(obj.extension, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold; '
            'font-family: monospace;">{}</span>',
            color, obj.extension
        )
    extension_badge.short_description = 'Tipo'
    
    def numeral_link(self, obj):
        url = reverse('admin:rendicion_cuentas_numeralrendicion_change', args=[obj.numeral.pk])
        return format_html('<a href="{}" style="color: #F59E0B; font-weight: 600;">{}</a>', url, obj.numeral.codigo)
    numeral_link.short_description = 'Numeral'
    
    def carpeta_ruta(self, obj):
        if obj.carpeta:
            return format_html(
                '<span style="color: #B45309; font-size: 12px; font-weight: 600;">📁 {}</span>',
                obj.carpeta.get_ruta_completa()
            )
        return format_html(
            '<span style="color: #F59E0B; font-size: 12px; font-weight: 600; '
            'background: #FEF3C7; padding: 2px 8px; border-radius: 4px;">📋 Raíz del Numeral</span>'
        )
    carpeta_ruta.short_description = 'Ubicación'
    
    def tamanio_badge(self, obj):
        return format_html('<span style="color: #6B7280; font-size: 12px; font-weight: 600;">{}</span>', obj.tamanio_legible())
    tamanio_badge.short_description = 'Tamaño'
    
    def descargas_badge(self, obj):
        if obj.descargas > 100:
            color = '#10B981'
        elif obj.descargas > 10:
            color = '#F59E0B'
        else:
            color = '#6B7280'
        return format_html('<span style="color: {}; font-weight: 600;">⬇ {}</span>', color, obj.descargas)
    descargas_badge.short_description = 'Descargas'
    
    def estado_badge(self, obj):
        badges = []
        if obj.publicado:
            badges.append('<span style="background-color: #10B981; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 600; margin-right: 4px;">✓ Publicado</span>')
        else:
            badges.append('<span style="background-color: #EF4444; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 600; margin-right: 4px;">✗ Oculto</span>')
        if obj.destacado:
            badges.append('<span style="background-color: #F59E0B; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 600;">⭐ Destacado</span>')
        return format_html(''.join(badges))
    estado_badge.short_description = 'Estado'
    
    def acciones_rapidas(self, obj):
        """Botones de acción rápida"""
        editar_url = reverse('admin:rendicion_cuentas_documentorendicion_change', args=[obj.pk])
        eliminar_url = reverse('admin:rendicion_cuentas_documentorendicion_delete', args=[obj.pk])
        ver_url = obj.archivo.url if obj.archivo else '#'
        
        html = f'''
        <div style="display: flex; gap: 4px; flex-wrap: wrap;">
            <a href="{editar_url}" 
               style="display: inline-flex; align-items: center; padding: 4px 8px; 
                      background: #F59E0B; color: white; border-radius: 4px; 
                      text-decoration: none; font-size: 11px; font-weight: 600;" title="Editar">
                ✏️
            </a>
            <a href="{ver_url}" target="_blank"
               style="display: inline-flex; align-items: center; padding: 4px 8px; 
                      background: #3B82F6; color: white; border-radius: 4px; 
                      text-decoration: none; font-size: 11px; font-weight: 600;" title="Ver">
                👁️
            </a>
            <a href="{eliminar_url}" 
               style="display: inline-flex; align-items: center; padding: 4px 8px; 
                      background: #EF4444; color: white; border-radius: 4px; 
                      text-decoration: none; font-size: 11px; font-weight: 600;"
               onclick="return confirm('¿Eliminar?');" title="Eliminar">
                🗑️
            </a>
        </div>
        '''
        return mark_safe(html)
    acciones_rapidas.short_description = 'Acciones'
    
    def publicar_documentos(self, request, queryset):
        updated = queryset.update(publicado=True)
        self.message_user(request, f'{updated} documento(s) publicado(s).')
    publicar_documentos.short_description = "✓ Publicar seleccionados"
    
    def despublicar_documentos(self, request, queryset):
        updated = queryset.update(publicado=False)
        self.message_user(request, f'{updated} documento(s) ocultado(s).')
    despublicar_documentos.short_description = "✗ Ocultar seleccionados"
    
    def marcar_destacados(self, request, queryset):
        updated = queryset.update(destacado=True)
        self.message_user(request, f'{updated} documento(s) destacado(s).')
    marcar_destacados.short_description = "⭐ Marcar como destacados"