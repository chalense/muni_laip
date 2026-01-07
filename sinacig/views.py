from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Prefetch
from django.http import FileResponse, Http404
from django.views import View
from .models import CarpetaSINACIG, DocumentoSINACIG


class CarpetaSINACIGListView(ListView):
    """
    Vista principal de SINACIG - Muestra carpetas de años
    """
    model = CarpetaSINACIG
    template_name = 'sinacig/carpeta_list.html'
    context_object_name = 'carpetas_anios'
    
    def get_queryset(self):
        # Solo carpetas raíz (años)
        return CarpetaSINACIG.objects.filter(
            padre__isnull=True
        ).annotate(
            total_docs=Count('documentos', filter=Q(documentos__publicado=True))
        ).order_by('-orden', '-nombre').prefetch_related(
            Prefetch(
                'subcarpetas',
                queryset=CarpetaSINACIG.objects.annotate(
                    total_docs=Count('documentos', filter=Q(documentos__publicado=True))
                ).order_by('nombre')
            )
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_carpetas'] = CarpetaSINACIG.objects.count()
        context['total_documentos'] = DocumentoSINACIG.objects.filter(publicado=True).count()
        context['documentos_destacados'] = DocumentoSINACIG.objects.filter(
            publicado=True, destacado=True
        ).select_related('carpeta').order_by('-fecha_publicacion')[:5]
        
        return context


class CarpetaSINACIGDetailView(DetailView):
    """
    Vista de detalle de una carpeta SINACIG
    """
    model = CarpetaSINACIG
    template_name = 'sinacig/carpeta_detail.html'
    context_object_name = 'carpeta'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carpeta = self.object
        
        # Breadcrumb
        context['breadcrumb'] = carpeta.get_ruta_breadcrumb()
        
        # Subcarpetas con conteo de documentos
        context['subcarpetas'] = CarpetaSINACIG.objects.filter(
            padre=carpeta
        ).annotate(
            total_docs=Count('documentos', filter=Q(documentos__publicado=True))
        ).order_by('nombre')
        
        # Documentos de esta carpeta
        context['documentos'] = DocumentoSINACIG.objects.filter(
            carpeta=carpeta,
            publicado=True
        ).order_by('-destacado', '-fecha_publicacion')
        
        # Estadísticas
        context['total_documentos'] = context['documentos'].count()
        context['total_subcarpetas'] = context['subcarpetas'].count()
        context['total_descargas'] = sum(doc.descargas for doc in context['documentos'])
        
        # Documentos destacados y recientes de esta carpeta
        context['documentos_destacados'] = context['documentos'].filter(destacado=True)[:3]
        context['documentos_recientes'] = context['documentos'][:5]
        
        return context


class DocumentoSINACIGDownloadView(View):
    """
    Vista para descargar documentos SINACIG
    """
    def get(self, request, pk):
        documento = get_object_or_404(DocumentoSINACIG, pk=pk, publicado=True)
        documento.incrementar_descargas()
        
        if not documento.archivo:
            raise Http404("Archivo no encontrado")
        
        try:
            response = FileResponse(
                documento.archivo.open('rb'),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{documento.archivo.name.split("/")[-1]}"'
            return response
        except FileNotFoundError:
            raise Http404("Archivo no encontrado en el servidor")


class BusquedaSINACIGView(ListView):
    """
    Vista de búsqueda de documentos SINACIG
    """
    model = DocumentoSINACIG
    template_name = 'sinacig/busqueda.html'
    context_object_name = 'documentos'
    paginate_by = 20
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        categoria_filter = self.request.GET.get('categoria', '')
        tipo_filter = self.request.GET.get('tipo', '')
        
        queryset = DocumentoSINACIG.objects.filter(
            publicado=True
        ).select_related('carpeta')
        
        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(carpeta__nombre__icontains=query)
            )
        
        if categoria_filter:
            queryset = queryset.filter(carpeta__categoria=categoria_filter)
        
        if tipo_filter:
            queryset = queryset.filter(extension=tipo_filter.upper())
        
        return queryset.order_by('-fecha_publicacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['categoria_filter'] = self.request.GET.get('categoria', '')
        context['tipo_filter'] = self.request.GET.get('tipo', '')
        context['categorias'] = CarpetaSINACIG.CATEGORIAS
        context['tipos_archivo'] = DocumentoSINACIG.objects.filter(
            publicado=True
        ).values_list('extension', flat=True).distinct().order_by('extension')
        context['total_resultados'] = self.get_queryset().count()
        return context


class EstadisticasSINACIGView(ListView):
    """
    Vista de estadísticas SINACIG
    """
    model = CarpetaSINACIG
    template_name = 'sinacig/estadisticas.html'
    context_object_name = 'carpetas'
    
    def get_queryset(self):
        return CarpetaSINACIG.objects.filter(
            padre__isnull=True
        ).annotate(
            total_documentos=Count('documentos', filter=Q(documentos__publicado=True))
        ).order_by('-orden', '-nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        context['total_carpetas'] = CarpetaSINACIG.objects.count()
        context['total_documentos'] = DocumentoSINACIG.objects.filter(publicado=True).count()
        context['total_descargas'] = sum(
            doc.descargas for doc in DocumentoSINACIG.objects.filter(publicado=True)
        )
        
        # Documentos más descargados
        context['documentos_populares'] = DocumentoSINACIG.objects.filter(
            publicado=True
        ).select_related('carpeta').order_by('-descargas')[:10]
        
        # Documentos recientes
        context['documentos_recientes'] = DocumentoSINACIG.objects.filter(
            publicado=True
        ).select_related('carpeta').order_by('-fecha_publicacion')[:10]
        
        # Distribución por tipo de archivo
        context['distribucion_tipos'] = DocumentoSINACIG.objects.filter(
            publicado=True
        ).values('extension').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Distribución por categoría
        categorias_stats = []
        for codigo, nombre in CarpetaSINACIG.CATEGORIAS:
            count = DocumentoSINACIG.objects.filter(
                carpeta__categoria=codigo,
                publicado=True
            ).count()
            categorias_stats.append({
                'codigo': codigo,
                'nombre': nombre,
                'total': count
            })
        context['categorias_distribucion'] = categorias_stats
        
        return context