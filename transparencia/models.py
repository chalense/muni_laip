from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.urls import reverse
import os


class Numeral(models.Model):
    """
    Representa cada uno de los 29 numerales del Artículo 10
    de la Ley de Acceso a la Información Pública de Guatemala
    """
    codigo = models.IntegerField(
        unique=True, 
        verbose_name="Número de Inciso",
        help_text="Número del inciso (1-29)"
    )
    titulo_corto = models.CharField(
        max_length=200, 
        verbose_name="Título Corto"
    )
    descripcion = models.TextField(
        verbose_name="Descripción Legal Completa",
        help_text="Descripción completa del numeral según la ley"
    )
    slug = models.SlugField(
        unique=True, 
        blank=True,
        max_length=255,
        help_text="Se genera automáticamente del código"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Desmarcar para ocultar este numeral del público"
    )
    orden = models.IntegerField(
        default=0,
        verbose_name="Orden de Visualización",
        help_text="Número menor aparece primero. Por defecto usa el código"
    )
    
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    class Meta:
        ordering = ['orden', 'codigo']
        verbose_name = "Numeral (Inciso)"
        verbose_name_plural = "Numerales (Incisos)"
        indexes = [
            models.Index(fields=['codigo', 'activo']),
            models.Index(fields=['orden']),
        ]

    def save(self, *args, **kwargs):
        # Generar slug automáticamente si no existe
        if not self.slug:
            self.slug = slugify(f"numeral-{self.codigo}")
        
        # Si el orden es 0, usar el código como orden
        if self.orden == 0:
            self.orden = self.codigo
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo}. {self.titulo_corto}"
    
    def get_absolute_url(self):
        """URL para ver el detalle del numeral"""
        return reverse('transparencia:numeral_detail', kwargs={'slug': self.slug})
    
    def total_documentos(self):
        """Retorna el total de documentos publicados en este numeral"""
        return self.documentos.filter(publicado=True).count()
    total_documentos.short_description = "Total Documentos"
    
    def total_carpetas_raiz(self):
        """Retorna el total de carpetas raíz (años)"""
        return self.carpetas.filter(padre__isnull=True).count()
    total_carpetas_raiz.short_description = "Años"
    
    def tiene_documentos(self):
        """Verifica si tiene al menos un documento publicado"""
        return self.documentos.filter(publicado=True).exists()


class Carpeta(models.Model):
    """
    Estructura jerárquica de carpetas para organizar documentos.
    Permite crear árbol de carpetas: Año -> Mes -> Subcarpetas
    
    Ejemplo:
    - 2024 (padre=null, es raíz)
      - Enero (padre=2024)
        - Actas (padre=Enero)
      - Febrero (padre=2024)
    """
    nombre = models.CharField(
        max_length=100, 
        verbose_name="Nombre de la Carpeta",
        help_text="Ej: 2024, Enero, Febrero, Actas, Contratos, etc."
    )
    numeral = models.ForeignKey(
        Numeral, 
        on_delete=models.CASCADE, 
        related_name='carpetas',
        verbose_name="Numeral"
    )
    padre = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcarpetas',
        verbose_name="Carpeta Padre",
        help_text="Dejar vacío si es una carpeta raíz (normalmente años)"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción opcional de esta carpeta"
    )
    orden = models.IntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Para ordenar carpetas del mismo nivel. Usar año o mes"
    )
    
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )
    
    def __str__(self):
        ruta = self.get_ruta_completa()
        return f"[Numeral {self.numeral.codigo}] {ruta}"

    class Meta:
        verbose_name = "Carpeta"
        verbose_name_plural = "Carpetas"
        ordering = ['-orden', '-nombre']
        unique_together = [['numeral', 'nombre', 'padre']]
        indexes = [
            models.Index(fields=['numeral', 'padre']),
            models.Index(fields=['-orden']),
        ]

    def __str__(self):
        return self.get_ruta_completa()
    
    def save(self, *args, **kwargs):
        # Si es un año (raíz) y no tiene orden, usar el nombre como orden
        if not self.padre and self.orden == 0:
            try:
                self.orden = int(self.nombre)
            except ValueError:
                self.orden = 0
        super().save(*args, **kwargs)
    
    def get_ruta_completa(self):
        """
        Retorna la ruta completa de la carpeta
        Ej: "2024 / Enero / Actas"
        """
        if self.padre:
            return f"{self.padre.get_ruta_completa()} / {self.nombre}"
        return self.nombre
    
    def get_ruta_breadcrumb(self):
        """
        Retorna la ruta como lista para breadcrumbs
        Ej: [("2024", carpeta_obj), ("Enero", carpeta_obj), ("Actas", carpeta_obj)]
        """
        ruta = []
        carpeta_actual = self
        
        while carpeta_actual:
            ruta.insert(0, (carpeta_actual.nombre, carpeta_actual))
            carpeta_actual = carpeta_actual.padre
            
        return ruta
    
    def es_carpeta_raiz(self):
        """Verifica si es una carpeta raíz (normalmente año)"""
        return self.padre is None
    
    def nivel(self):
        """
        Retorna el nivel de profundidad
        0 = raíz (año)
        1 = primer nivel (mes)
        2 = segundo nivel (subcarpeta)
        etc.
        """
        if self.padre is None:
            return 0
        return self.padre.nivel() + 1
    
    def total_documentos(self):
        """Cuenta documentos directos en esta carpeta"""
        return self.documentos.filter(publicado=True).count()
    total_documentos.short_description = "Documentos"
    
    def total_documentos_recursivo(self):
        """Cuenta todos los documentos incluyendo subcarpetas"""
        total = self.documentos.filter(publicado=True).count()
        for subcarpeta in self.subcarpetas.all():
            total += subcarpeta.total_documentos_recursivo()
        return total
    
    def get_todas_subcarpetas(self):
        """Retorna todas las subcarpetas recursivamente"""
        subcarpetas = list(self.subcarpetas.all())
        for subcarpeta in self.subcarpetas.all():
            subcarpetas.extend(subcarpeta.get_todas_subcarpetas())
        return subcarpetas
    
    def tiene_contenido(self):
        """Verifica si tiene documentos o subcarpetas"""
        return (
            self.documentos.filter(publicado=True).exists() or 
            self.subcarpetas.exists()
        )


def path_documento(instance, filename):
    """
    Genera la ruta de almacenamiento para documentos.
    Estructura: transparencia/numeral_X/año/mes/subcarpeta/archivo.pdf
    
    Si no hay carpeta: transparencia/numeral_X/sin_carpeta/archivo.pdf
    """
    # Sanitizar nombre de archivo (eliminar espacios y caracteres especiales)
    nombre_limpio = filename.replace(' ', '_')
    
    ruta_base = f'transparencia/numeral_{instance.numeral.codigo}/'
    
    if instance.carpeta:
        # Construir ruta desde la carpeta raíz hasta la actual
        carpetas = []
        carpeta_actual = instance.carpeta
        
        while carpeta_actual:
            # Sanitizar nombre de carpeta
            nombre_carpeta = carpeta_actual.nombre.replace(' ', '_')
            carpetas.insert(0, nombre_carpeta)
            carpeta_actual = carpeta_actual.padre
        
        ruta_base += '/'.join(carpetas) + '/'
    else:
        # Si no hay carpeta, guardar en carpeta especial
        ruta_base += 'sin_carpeta/'
    
    return ruta_base + nombre_limpio


class Documento(models.Model):
    """
    Documentos que se publican en cada numeral.
    Pueden estar organizados en carpetas o en la raíz del numeral.
    """
    # Extensiones permitidas
    EXTENSIONES_PERMITIDAS = [
        'pdf', 'xls', 'xlsx', 'doc', 'docx', 
        'png', 'jpg', 'jpeg', 'svg', 'csv'
    ]
    
    # Relaciones
    numeral = models.ForeignKey(
        Numeral, 
        on_delete=models.CASCADE, 
        related_name='documentos',
        verbose_name="Numeral"
    )
    carpeta = models.ForeignKey(
        Carpeta, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='documentos',
        verbose_name="Carpeta",
        help_text="Seleccionar carpeta donde se publicará (opcional)"
    )
    
    # Información del documento
    titulo = models.CharField(
        max_length=300, 
        verbose_name="Título del Documento",
        help_text="Nombre descriptivo del documento"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción opcional del contenido"
    )
    archivo = models.FileField(
        upload_to=path_documento,
        validators=[FileExtensionValidator(
            allowed_extensions=EXTENSIONES_PERMITIDAS
        )],
        verbose_name="Archivo"
    )
    
    # Metadatos del archivo (se calculan automáticamente)
    tamanio_bytes = models.BigIntegerField(
        default=0,
        verbose_name="Tamaño en Bytes",
        editable=False
    )
    extension = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Extensión",
        editable=False
    )
    
    # Estadísticas
    descargas = models.PositiveIntegerField(
        default=0,
        verbose_name="Número de Descargas",
        editable=False
    )
    
    # Control de publicación
    publicado = models.BooleanField(
        default=True,
        verbose_name="Publicado",
        help_text="Desmarcar para ocultar temporalmente"
    )
    destacado = models.BooleanField(
        default=False,
        verbose_name="Destacado",
        help_text="Marcar para resaltar este documento"
    )
    
    # Fechas
    fecha_publicacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Publicación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['-destacado', '-fecha_publicacion']
        indexes = [
            models.Index(fields=['numeral', 'publicado']),
            models.Index(fields=['carpeta', 'publicado']),
            models.Index(fields=['-fecha_publicacion']),
            models.Index(fields=['publicado', '-destacado']),
        ]

    def save(self, *args, **kwargs):
        if self.archivo:
            # Calcular tamaño del archivo en bytes
            self.tamanio_bytes = self.archivo.size
            
            # Extraer y normalizar extensión
            _, ext = os.path.splitext(self.archivo.name)
            self.extension = ext.lower().replace('.', '').upper()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo
    
    def get_absolute_url(self):
        """URL para descargar el documento"""
        return self.archivo.url
    
    def get_extension(self):
        """Retorna la extensión del archivo"""
        return self.extension
    
    def tamanio_legible(self):
        """
        Retorna el tamaño del archivo en formato legible
        Ej: "2.5 MB", "512 KB"
        """
        tamanio = float(self.tamanio_bytes)
        
        for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
            if tamanio < 1024.0:
                return f"{tamanio:.1f} {unidad}"
            tamanio /= 1024.0
            
        return f"{tamanio:.1f} PB"
    
    def incrementar_descargas(self):
        """
        Incrementa el contador de descargas de forma eficiente.
        Usar este método en la vista de descarga.
        """
        self.descargas += 1
        self.save(update_fields=['descargas'])
    
    def get_ruta_completa(self):
        """
        Retorna la ruta completa del documento
        Ej: "Numeral 1 / 2024 / Enero / documento.pdf"
        """
        ruta = f"{self.numeral}"
        
        if self.carpeta:
            ruta += f" / {self.carpeta.get_ruta_completa()}"
        else:
            ruta += " / Raíz"
            
        return ruta
    
    def get_icono_extension(self):
        """
        Retorna el nombre del ícono según la extensión
        Para usar con librerías de iconos
        """
        iconos = {
            'PDF': 'file-pdf',
            'XLS': 'file-excel',
            'XLSX': 'file-excel',
            'DOC': 'file-word',
            'DOCX': 'file-word',
            'PNG': 'file-image',
            'JPG': 'file-image',
            'JPEG': 'file-image',
            'SVG': 'file-image',
            'GIF': 'file-image',
            'BMP': 'file-image',
            'CSV': 'file-csv',
            'TXT': 'file-alt',
            'ZIP': 'file-archive',
            'RAR': 'file-archive',
            '7Z': 'file-archive',
            'MP4': 'file-video',
            'AVI': 'file-video',
            'MOV': 'file-video',
            'MP3': 'file-audio',
            'WAV': 'file-audio',
            'PPT': 'file-powerpoint',
            'PPTX': 'file-powerpoint',
        }
        return iconos.get(self.extension, 'file')
    
    def get_color_badge(self):
        """
        Retorna el color para el badge según la extensión
        Para usar con Tailwind CSS
        """
        colores = {
            'PDF': 'text-red-600',
            'XLS': 'text-green-600',
            'XLSX': 'text-green-600',
            'DOC': 'text-blue-600',
            'DOCX': 'text-blue-600',
            'PNG': 'text-purple-600',
            'JPG': 'text-purple-600',
            'JPEG': 'text-purple-600',
            'SVG': 'text-purple-600',
            'GIF': 'text-purple-600',
            'BMP': 'text-purple-600',
            'CSV': 'text-yellow-600',
            'TXT': 'text-gray-600',
            'ZIP': 'text-orange-600',
            'RAR': 'text-orange-600',
            '7Z': 'text-orange-600',
            'MP4': 'text-pink-600',
            'AVI': 'text-pink-600',
            'MOV': 'text-pink-600',
            'MP3': 'text-indigo-600',
            'WAV': 'text-indigo-600',
            'PPT': 'text-orange-500',
            'PPTX': 'text-orange-500',
        }
        return colores.get(self.extension, 'text-gray-500')
    
    def get_color_tailwind(self):
        """
        Retorna clases de Tailwind según el tipo de archivo
        """
        color = self.get_color_badge()
        return {
            'bg': f'bg-{color}-100',
            'text': f'text-{color}-800',
            'border': f'border-{color}-300',
        }
    
    def es_imagen(self):
        """Verifica si el documento es una imagen"""
        return self.extension in ['PNG', 'JPG', 'JPEG', 'SVG']
    
    def es_excel(self):
        """Verifica si el documento es un archivo Excel"""
        return self.extension in ['XLS', 'XLSX', 'CSV']
    
    def es_word(self):
        """Verifica si el documento es un archivo Word"""
        return self.extension in ['DOC', 'DOCX']
    
    def es_pdf(self):
        """Verifica si el documento es un PDF"""
        return self.extension == 'PDF'


#Para iconos SVG de los archivos
# def get_icono_svg(self):
#     """Retorna el HTML del ícono SVG según la extensión"""
#     iconos = {
#         'PDF': '''
#             <svg viewBox="0 0 24 24" class="w-full h-full">
#                 <!-- Ícono estilo Adobe PDF -->
#                 <path fill="#DC1C13" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm0-3.5c-.55 0-1-.45-1-1V8c0-.55.45-1 1-1s1 .45 1 1v4.5c0 .55-.45 1-1 1z"/>
#                 <text x="12" y="17" text-anchor="middle" fill="white" font-size="6" font-weight="bold" font-family="Arial">PDF</text>
#             </svg>
#         ''',
#         'DOCX': '''
#             <svg viewBox="0 0 24 24" class="w-full h-full">
#                 <!-- Ícono estilo Microsoft Word -->
#                 <rect fill="#2B579A" width="24" height="24" rx="2"/>
#                 <text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">W</text>
#             </svg>
#         ''',
#         'DOC': '''
#             <svg viewBox="0 0 24 24" class="w-full h-full">
#                 <rect fill="#2B579A" width="24" height="24" rx="2"/>
#                 <text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">W</text>
#             </svg>
#         ''',
#         'XLSX': '''
#             <svg viewBox="0 0 24 24" class="w-full h-full">
#                 <!-- Ícono estilo Microsoft Excel -->
#                 <rect fill="#217346" width="24" height="24" rx="2"/>
#                 <text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">X</text>
#             </svg>
#         ''',
#         'XLS': '''
#             <svg viewBox="0 0 24 24" class="w-full h-full">
#                 <rect fill="#217346" width="24" height="24" rx="2"/>
#                 <text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">X</text>
#             </svg>
#         ''',
#         'PPTX': '''
#             <svg viewBox="0 0 24 24" class="w-full h-full">
#                 <!-- Ícono estilo Microsoft PowerPoint -->
#                 <rect fill="#D24726" width="24" height="24" rx="2"/>
#                 <text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">P</text>
#             </svg>
#         ''',
#         'PPT': '''
#             <svg viewBox="0 0 24 24" class="w-full h-full">
#                 <rect fill="#D24726" width="24" height="24" rx="2"/>
#                 <text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">P</text>
#             </svg>
#         ''',
#     }
    
#     # Si no hay SVG personalizado, usar Font Awesome
#     if self.extension in iconos:
#         return iconos[self.extension]
#     else:
#         return f'<i class="fas {self.get_icono_marca()} {self.get_color_icono()} text-2xl"></i>'

# def usar_icono_svg(self):
#     """Verifica si debe usar SVG o Font Awesome"""
#     return self.extension in ['PDF', 'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT', 'PPTX']