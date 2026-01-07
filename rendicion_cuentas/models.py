from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.urls import reverse
import os


class NumeralRendicion(models.Model):
    """
    Numerales específicos de Rendición de Cuentas
    """
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código del Numeral",
        help_text="Ej: 2.1.2, 2.1.4"
    )
    titulo_corto = models.CharField(
        max_length=200,
        verbose_name="Título Corto"
    )
    descripcion = models.TextField(
        verbose_name="Descripción Completa",
        help_text="Descripción del numeral"
    )
    slug = models.SlugField(
        unique=True,
        blank=True,
        max_length=255,
        help_text="Se genera automáticamente"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Desmarcar para ocultar este numeral"
    )
    orden = models.IntegerField(
        default=0,
        verbose_name="Orden de Visualización",
        help_text="Número menor aparece primero"
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
        verbose_name = "Numeral Rendición de Cuentas"
        verbose_name_plural = "Numerales Rendición de Cuentas"
        indexes = [
            models.Index(fields=['codigo', 'activo']),
            models.Index(fields=['orden']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"rendicion-{self.codigo}")
        if self.orden == 0:
            # Extraer números del código (ej: "2.1.2" -> 212)
            try:
                self.orden = int(''.join(filter(str.isdigit, self.codigo)))
            except:
                self.orden = 999
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.titulo_corto}"
    
    def get_absolute_url(self):
        return reverse('rendicion_cuentas:numeral_detail', kwargs={'slug': self.slug})
    
    def total_documentos(self):
        return self.documentos.filter(publicado=True).count()
    total_documentos.short_description = "Total Documentos"
    
    def total_carpetas_raiz(self):
        return self.carpetas.filter(padre__isnull=True).count()
    total_carpetas_raiz.short_description = "Años"


class CarpetaRendicion(models.Model):
    """
    Estructura jerárquica de carpetas para Rendición de Cuentas
    """
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre de la Carpeta",
        help_text="Ej: 2024, Enero, Trimestre 1..."
    )
    numeral = models.ForeignKey(
        NumeralRendicion,
        on_delete=models.CASCADE,
        related_name='carpetas',
        verbose_name="Numeral Rendición"
    )
    padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcarpetas',
        verbose_name="Carpeta Padre",
        help_text="Dejar vacío si es carpeta raíz"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción"
    )
    orden = models.IntegerField(
        default=0,
        verbose_name="Orden"
    )
    
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carpeta Rendición"
        verbose_name_plural = "Carpetas Rendición"
        ordering = ['-orden', '-nombre']
        unique_together = [['numeral', 'nombre', 'padre']]
        indexes = [
            models.Index(fields=['numeral', 'padre']),
        ]

    def __str__(self):
        return self.get_ruta_completa()
    
    def save(self, *args, **kwargs):
        if not self.padre and self.orden == 0:
            try:
                self.orden = int(self.nombre)
            except ValueError:
                self.orden = 0
        super().save(*args, **kwargs)
    
    def get_ruta_completa(self):
        if self.padre:
            return f"{self.padre.get_ruta_completa()} / {self.nombre}"
        return self.nombre
    
    def get_ruta_breadcrumb(self):
        ruta = []
        carpeta_actual = self
        while carpeta_actual:
            ruta.insert(0, (carpeta_actual.nombre, carpeta_actual))
            carpeta_actual = carpeta_actual.padre
        return ruta
    
    def es_carpeta_raiz(self):
        return self.padre is None
    
    def nivel(self):
        if self.padre is None:
            return 0
        return self.padre.nivel() + 1
    
    def total_documentos(self):
        return self.documentos.filter(publicado=True).count()
    total_documentos.short_description = "Documentos"


def path_documento_rendicion(instance, filename):
    """
    Genera la ruta para documentos de Rendición de Cuentas
    """
    nombre_limpio = filename.replace(' ', '_')
    # Reemplazar puntos en el código para la ruta
    codigo_limpio = instance.numeral.codigo.replace('.', '_')
    ruta_base = f'rendicion_cuentas/numeral_{codigo_limpio}/'
    
    if instance.carpeta:
        carpetas = []
        carpeta_actual = instance.carpeta
        while carpeta_actual:
            nombre_carpeta = carpeta_actual.nombre.replace(' ', '_')
            carpetas.insert(0, nombre_carpeta)
            carpeta_actual = carpeta_actual.padre
        ruta_base += '/'.join(carpetas) + '/'
    else:
        ruta_base += 'sin_carpeta/'
    
    return ruta_base + nombre_limpio


class DocumentoRendicion(models.Model):
    """
    Documentos de Rendición de Cuentas
    """
    EXTENSIONES_PERMITIDAS = [
        'pdf', 'xls', 'xlsx', 'doc', 'docx',
        'png', 'jpg', 'jpeg', 'svg', 'csv'
    ]
    
    numeral = models.ForeignKey(
        NumeralRendicion,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name="Numeral Rendición"
    )
    carpeta = models.ForeignKey(
        CarpetaRendicion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='documentos',
        verbose_name="Carpeta"
    )
    
    titulo = models.CharField(
        max_length=300,
        verbose_name="Título del Documento"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción"
    )
    archivo = models.FileField(
        upload_to=path_documento_rendicion,
        validators=[FileExtensionValidator(
            allowed_extensions=EXTENSIONES_PERMITIDAS
        )],
        verbose_name="Archivo"
    )
    
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
    
    descargas = models.PositiveIntegerField(
        default=0,
        verbose_name="Número de Descargas",
        editable=False
    )
    
    publicado = models.BooleanField(
        default=True,
        verbose_name="Publicado"
    )
    destacado = models.BooleanField(
        default=False,
        verbose_name="Destacado"
    )
    
    fecha_publicacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Publicación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    class Meta:
        verbose_name = "Documento Rendición"
        verbose_name_plural = "Documentos Rendición"
        ordering = ['-destacado', '-fecha_publicacion']
        indexes = [
            models.Index(fields=['numeral', 'publicado']),
            models.Index(fields=['carpeta', 'publicado']),
            models.Index(fields=['-fecha_publicacion']),
        ]

    def save(self, *args, **kwargs):
        if self.archivo:
            self.tamanio_bytes = self.archivo.size
            _, ext = os.path.splitext(self.archivo.name)
            self.extension = ext.lower().replace('.', '').upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo
    
    def get_absolute_url(self):
        return self.archivo.url
    
    def tamanio_legible(self):
        tamanio = float(self.tamanio_bytes)
        for unidad in ['B', 'KB', 'MB', 'GB', 'TB']:
            if tamanio < 1024.0:
                return f"{tamanio:.1f} {unidad}"
            tamanio /= 1024.0
        return f"{tamanio:.1f} PB"
    
    def incrementar_descargas(self):
        self.descargas += 1
        self.save(update_fields=['descargas'])
    
    def get_icono_extension(self):
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
            'CSV': 'file-csv',
        }
        return iconos.get(self.extension, 'file')
    
    def get_color_icono(self):
        """Retorna el color del ícono según la extensión"""
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
            'PPT': 'text-orange-500',
            'PPTX': 'text-orange-500',
        }
        return colores.get(self.extension, 'text-gray-500')

    def get_fondo_icono(self):
        """Retorna el color de fondo según el tipo"""
        fondos = {
            'PDF': 'bg-red-50',
            'XLS': 'bg-green-50',
            'XLSX': 'bg-green-50',
            'DOC': 'bg-blue-50',
            'DOCX': 'bg-blue-50',
            'PPT': 'bg-orange-50',
            'PPTX': 'bg-orange-50',
            'PNG': 'bg-purple-50',
            'JPG': 'bg-purple-50',
            'JPEG': 'bg-purple-50',
            'SVG': 'bg-purple-50',
            'GIF': 'bg-purple-50',
            'BMP': 'bg-purple-50',
            'CSV': 'bg-green-50',
            'TXT': 'bg-gray-50',
            'ZIP': 'bg-yellow-50',
            'RAR': 'bg-yellow-50',
        }
        return fondos.get(self.extension, 'bg-gray-50')

    def get_badge_color(self):
        """Retorna los colores del badge según el tipo"""
        colores = {
            'PDF': {'bg': 'bg-red-100', 'text': 'text-red-800'},
            'XLS': {'bg': 'bg-green-100', 'text': 'text-green-800'},
            'XLSX': {'bg': 'bg-green-100', 'text': 'text-green-800'},
            'DOC': {'bg': 'bg-blue-100', 'text': 'text-blue-800'},
            'DOCX': {'bg': 'bg-blue-100', 'text': 'text-blue-800'},
            'PPT': {'bg': 'bg-orange-100', 'text': 'text-orange-800'},
            'PPTX': {'bg': 'bg-orange-100', 'text': 'text-orange-800'},
            'PNG': {'bg': 'bg-purple-100', 'text': 'text-purple-800'},
            'JPG': {'bg': 'bg-purple-100', 'text': 'text-purple-800'},
            'JPEG': {'bg': 'bg-purple-100', 'text': 'text-purple-800'},
            'CSV': {'bg': 'bg-green-100', 'text': 'text-green-800'},
        }
        return colores.get(self.extension, {'bg': 'bg-gray-100', 'text': 'text-gray-800'})