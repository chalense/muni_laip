from django.contrib import admin
from django.utils.html import format_html
from .models import CarpetaSINACIG, DocumentoSINACIG


@admin.register(CarpetaSINACIG)
class CarpetaSINACIGAdmin(admin.ModelAdmin):
    list_display = [
        'nombre',
        'get_categoria_display',
        'get_nivel_display',
        'get_padre_display',
        'total_documentos_display',
        'orden',
        'actualizado_en'
    ]
    list_filter = ['categoria', 'padre', 'creado_en']
    search_fields = ['nombre', 'descripcion']
    ordering = ['-orden', '-nombre']
    date_hierarchy = 'creado_en'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'categoria', 'padre', 'descripcion')
        }),
        ('Organización', {
            'fields': ('orden',)
        }),
    )
    
    def get_categoria_display(self, obj):
        if obj.categoria:
            return dict(CarpetaSINACIG.CATEGORIAS).get(obj.categoria, '-')
        return '-'
    get_categoria_display.short_description = 'Categoría'
    
    def get_nivel_display(self, obj):
        nivel = obj.nivel()
        if nivel == 0:
            badge_color = 'blue'
            texto = 'Año'
        elif nivel == 1:
            badge_color = 'green'
            texto = 'Categoría'
        else:
            badge_color = 'gray'
            texto = f'Nivel {nivel}'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            badge_color,
            texto
        )
    get_nivel_display.short_description = 'Nivel'
    
    def get_padre_display(self, obj):
        if obj.padre:
            return obj.padre.nombre
        return format_html(
            '<span style="color: green; font-weight: bold;">📁 Raíz</span>'
        )
    get_padre_display.short_description = 'Carpeta Padre'
    
    def total_documentos_display(self, obj):
        total = obj.total_documentos
        total_recursivo = obj.total_documentos_recursivo
        
        if total_recursivo > total:
            return format_html(
                '<span style="font-weight: bold;">{}</span> <span style="color: gray; font-size: 11px;">(+{} en subcarpetas)</span>',
                total,
                total_recursivo - total
            )
        return total
    total_documentos_display.short_description = 'Documentos'


@admin.register(DocumentoSINACIG)
class DocumentoSINACIGAdmin(admin.ModelAdmin):
    list_display = [
        'titulo',
        'get_carpeta_completa',
        'get_extension_badge',
        'tamanio_display',
        'descargas',
        'destacado_display',
        'publicado_display',
        'fecha_publicacion'
    ]
    list_filter = [
        'publicado',
        'destacado',
        'extension',
        'carpeta__categoria',
        'fecha_publicacion'
    ]
    search_fields = ['titulo', 'descripcion', 'carpeta__nombre']
    readonly_fields = ['tamanio_bytes', 'extension', 'descargas', 'fecha_publicacion', 'fecha_actualizacion']
    date_hierarchy = 'fecha_publicacion'
    ordering = ['-fecha_publicacion']
    
    fieldsets = (
        ('Información del Documento', {
            'fields': ('titulo', 'descripcion', 'carpeta', 'archivo')
        }),
        ('Estado', {
            'fields': ('publicado', 'destacado')
        }),
        ('Metadata (Solo Lectura)', {
            'fields': ('tamanio_bytes', 'extension', 'descargas', 'fecha_publicacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_carpeta_completa(self, obj):
        return obj.carpeta.get_ruta_completa()
    get_carpeta_completa.short_description = 'Ubicación'
    
    def get_extension_badge(self, obj):
        color_map = {
            'PDF': 'red',
            'XLSX': 'green',
            'XLS': 'green',
            'DOCX': 'blue',
            'DOC': 'blue',
            'PNG': 'purple',
            'JPG': 'purple',
            'JPEG': 'purple',
        }
        color = color_map.get(obj.extension, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.extension
        )
    get_extension_badge.short_description = 'Tipo'
    
    def tamanio_display(self, obj):
        return obj.tamanio_legible()
    tamanio_display.short_description = 'Tamaño'
    
    def destacado_display(self, obj):
        if obj.destacado:
            return format_html(
                '<span style="color: gold; font-size: 16px;">⭐</span>'
            )
        return '-'
    destacado_display.short_description = 'Destacado'
    
    def publicado_display(self, obj):
        if obj.publicado:
            return format_html(
                '<span style="color: green; font-size: 16px;">✓</span>'
            )
        return format_html(
            '<span style="color: red; font-size: 16px;">✗</span>'
        )
    publicado_display.short_description = 'Publicado'
    
    actions = ['marcar_destacado', 'desmarcar_destacado', 'marcar_publicado', 'marcar_no_publicado']
    
    def marcar_destacado(self, request, queryset):
        updated = queryset.update(destacado=True)
        self.message_user(request, f'{updated} documento(s) marcado(s) como destacado.')
    marcar_destacado.short_description = 'Marcar como destacado'
    
    def desmarcar_destacado(self, request, queryset):
        updated = queryset.update(destacado=False)
        self.message_user(request, f'{updated} documento(s) desmarcado(s) como destacado.')
    desmarcar_destacado.short_description = 'Desmarcar como destacado'
    
    def marcar_publicado(self, request, queryset):
        updated = queryset.update(publicado=True)
        self.message_user(request, f'{updated} documento(s) marcado(s) como publicado.')
    marcar_publicado.short_description = 'Marcar como publicado'
    
    def marcar_no_publicado(self, request, queryset):
        updated = queryset.update(publicado=False)
        self.message_user(request, f'{updated} documento(s) marcado(s) como no publicado.')
    marcar_no_publicado.short_description = 'Marcar como no publicado'