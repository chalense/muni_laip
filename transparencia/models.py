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
            'CSV': 'file-csv',
        }
        return iconos.get(self.extension, 'file')
    
    def get_color_badge(self):
        """
        Retorna el color para el badge según la extensión
        Para usar con Tailwind CSS
        """
        colores = {
            'PDF': 'red',
            'XLS': 'green',
            'XLSX': 'green',
            'DOC': 'blue',
            'DOCX': 'blue',
            'PNG': 'purple',
            'JPG': 'purple',
            'JPEG': 'purple',
            'SVG': 'purple',
            'CSV': 'yellow',
        }
        return colores.get(self.extension, 'gray')
    
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