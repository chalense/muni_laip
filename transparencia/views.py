from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_GET
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Prefetch
from django.http import FileResponse, Http404
from django.views import View
from .models import Numeral, Carpeta, Documento


class NumeralListView(ListView):
    """
    Vista principal que muestra todos los numerales activos del Artículo 10
    """
    model = Numeral
    template_name = 'transparencia/numeral_list.html'
    context_object_name = 'numerales'
    
    def get_queryset(self):
        """
        Retorna solo numerales activos con estadísticas de documentos
        """
        return Numeral.objects.filter(activo=True).annotate(
            total_documentos=Count(
                'documentos',
                filter=Q(documentos__publicado=True)
            ),
            total_carpetas=Count(
                'carpetas',
                filter=Q(carpetas__padre__isnull=True)
            )
        ).select_related().prefetch_related(
            Prefetch(
                'documentos',
                queryset=Documento.objects.filter(
                    publicado=True,
                    carpeta__isnull=True
                ).order_by('-destacado', '-fecha_publicacion')
            )
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        context['total_numerales'] = self.get_queryset().count()
        context['total_documentos_global'] = Documento.objects.filter(
            publicado=True
        ).count()
        
        # Documentos destacados globales
        context['documentos_destacados'] = Documento.objects.filter(
            publicado=True,
            destacado=True
        ).select_related('numeral', 'carpeta').order_by('-fecha_publicacion')[:5]
        
        return context


class NumeralDetailView(DetailView):
    """
    Vista detallada de un numeral específico mostrando su estructura de carpetas
    y documentos organizados jerárquicamente
    """
    model = Numeral
    template_name = 'transparencia/numeral_detail.html'
    context_object_name = 'numeral'
    slug_field = 'slug'
    
    def get_queryset(self):
        """Solo mostrar numerales activos"""
        return Numeral.objects.filter(activo=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        numeral = self.object
        
        # Obtener carpetas raíz (años) con sus estadísticas
        carpetas_raiz = Carpeta.objects.filter(
            numeral=numeral,
            padre__isnull=True
        ).annotate(
            total_docs=Count(
                'documentos',
                filter=Q(documentos__publicado=True)
            )
        ).order_by('-orden', '-nombre')
        
        # Construir estructura jerárquica completa
        estructura = []
        for carpeta_raiz in carpetas_raiz:
            estructura.append({
                'carpeta': carpeta_raiz,
                'subcarpetas': self._construir_arbol(carpeta_raiz)
            })
        
        context['estructura_carpetas'] = estructura
        
        # Documentos sin carpeta (raíz del numeral)
        context['documentos_raiz'] = Documento.objects.filter(
            numeral=numeral,
            carpeta__isnull=True,
            publicado=True
        ).order_by('-destacado', '-fecha_publicacion')
        
        # Estadísticas del numeral
        context['total_documentos'] = Documento.objects.filter(
            numeral=numeral,
            publicado=True
        ).count()
        
        context['total_carpetas'] = Carpeta.objects.filter(
            numeral=numeral
        ).count()
        
        context['total_descargas'] = sum(
            doc.descargas for doc in Documento.objects.filter(
                numeral=numeral,
                publicado=True
            )
        )
        
        # Documentos destacados del numeral
        context['documentos_destacados'] = Documento.objects.filter(
            numeral=numeral,
            publicado=True,
            destacado=True
        ).select_related('carpeta').order_by('-fecha_publicacion')[:3]
        
        # Documentos recientes
        context['documentos_recientes'] = Documento.objects.filter(
            numeral=numeral,
            publicado=True
        ).select_related('carpeta').order_by('-fecha_publicacion')[:5]
        
        return context
    
    def _construir_arbol(self, carpeta_padre):
        """
        Construye recursivamente el árbol de carpetas y documentos
        """
        subcarpetas = Carpeta.objects.filter(
            padre=carpeta_padre
        ).annotate(
            total_docs=Count(
                'documentos',
                filter=Q(documentos__publicado=True)
            )
        ).order_by('-orden', 'nombre').prefetch_related(
            Prefetch(
                'documentos',
                queryset = Documento.objects.filter(
                    publicado=True).order_by('-destacado', '-fecha_publicacion')
            )
        )
        
        estructura = []
        for subcarpeta in subcarpetas:
            # Obtener documentos de esta subcarpeta
            documentos = subcarpeta.documentos.all() # Gracias al prefetch_related
            
            estructura.append({
                'carpeta': subcarpeta,
                'documentos': documentos,
                'subcarpetas': self._construir_arbol(subcarpeta)
            })
        
        return estructura


class CarpetaDetailView(DetailView):
    """
    Vista detallada de una carpeta específica con sus documentos y subcarpetas
    """
    model = Carpeta
    template_name = 'transparencia/carpeta_detail.html'
    context_object_name = 'carpeta'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carpeta = self.object
        
        # Breadcrumb (ruta de navegación)
        context['breadcrumb'] = carpeta.get_ruta_breadcrumb()
        
        # Subcarpetas
        context['subcarpetas'] = Carpeta.objects.filter(
            padre=carpeta
        ).annotate(
            total_docs=Count(
                'documentos',
                filter=Q(documentos__publicado=True)
            )
        ).order_by('-orden', 'nombre')
        
        # Documentos de esta carpeta
        context['documentos'] = Documento.objects.filter(
            carpeta=carpeta,
            publicado=True
        ).order_by('-destacado', '-fecha_publicacion')
        
        # Estadísticas
        context['total_documentos'] = context['documentos'].count()
        context['total_subcarpetas'] = context['subcarpetas'].count()
        
        return context


class DocumentoDownloadView(View):
    """
    Vista para descargar documentos e incrementar el contador de descargas
    """
    def get(self, request, pk):
        documento = get_object_or_404(
            Documento,
            pk=pk,
            publicado=True
        )
        
        # Incrementar contador de descargas
        documento.incrementar_descargas()
        
        # Verificar que el archivo existe
        if not documento.archivo:
            raise Http404("Archivo no encontrado")
        
        try:
            # Retornar el archivo
            response = FileResponse(
                documento.archivo.open('rb'),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{documento.archivo.name.split("/")[-1]}"'
            return response
        except FileNotFoundError:
            raise Http404("Archivo no encontrado en el servidor")


class BusquedaView(ListView):
    """
    Vista de búsqueda de documentos en todo el sistema
    """
    model = Documento
    template_name = 'transparencia/busqueda.html'
    context_object_name = 'documentos'
    paginate_by = 20
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        numeral_filter = self.request.GET.get('numeral', '')
        tipo_filter = self.request.GET.get('tipo', '')
        
        queryset = Documento.objects.filter(publicado=True).select_related(
            'numeral', 'carpeta'
        )
        
        # Filtro por búsqueda de texto
        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(numeral__titulo_corto__icontains=query)
            )
        
        # Filtro por numeral
        if numeral_filter:
            queryset = queryset.filter(numeral__codigo=numeral_filter)
        
        # Filtro por tipo de archivo
        if tipo_filter:
            queryset = queryset.filter(extension=tipo_filter.upper())
        
        return queryset.order_by('-fecha_publicacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        numeral = self.object
        
        # # Parámetros de búsqueda
        # context['query'] = self.request.GET.get('q', '')
        # context['numeral_filter'] = self.request.GET.get('numeral', '')
        # context['tipo_filter'] = self.request.GET.get('tipo', '')
        
        # # Numerales para el filtro
        # context['numerales'] = Numeral.objects.filter(activo=True).order_by('codigo')
        
        # # Tipos de archivo disponibles
        # context['tipos_archivo'] = Documento.objects.filter(
        #     publicado=True
        # ).values_list('extension', flat=True).distinct().order_by('extension')
        
        # # Total de resultados
        # context['total_resultados'] = self.get_queryset().count()
        
        # return context
        
        carpeta_raiz = Carpeta.objects.filter(
            numeral=numeral, padre__isnull=True
        ).annotate(
            total_docs=Count('documentos', filter=Q(documentos__publicado=True))
        ).order_by('-orden', '-nombre').prefetch_related(
            Prefetch('documentos',
                queryset=Documento.objects.filter(
                    publicado=True).order_by('-destacado', '-fecha_publicacion')
        ))
        
        estructura = []
        for carpeta in carpeta_raiz:
            estructura.append({
                'carpeta': carpeta,
                'subcarpetas': self._construir_arbol(carpeta_raiz)
            })
        
        context['estructura_carpetas'] = estructura


class EstadisticasView(ListView):
    """
    Vista de estadísticas generales del sistema
    """
    model = Numeral
    template_name = 'transparencia/estadisticas.html'
    context_object_name = 'numerales'
    
    def get_queryset(self):
        return Numeral.objects.filter(activo=True).annotate(
            total_documentos=Count(
                'documentos',
                filter=Q(documentos__publicado=True)
            ),
            total_descargas=Count('documentos__descargas')
        ).order_by('codigo')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas globales
        context['total_numerales'] = Numeral.objects.filter(activo=True).count()
        context['total_documentos'] = Documento.objects.filter(publicado=True).count()
        context['total_carpetas'] = Carpeta.objects.count()
        
        total_descargas = sum(
            doc.descargas for doc in Documento.objects.filter(publicado=True)
        )
        context['total_descargas'] = total_descargas
        
        # Documentos más descargados
        context['documentos_populares'] = Documento.objects.filter(
            publicado=True
        ).select_related('numeral', 'carpeta').order_by('-descargas')[:10]
        
        # Documentos recientes
        context['documentos_recientes'] = Documento.objects.filter(
            publicado=True
        ).select_related('numeral', 'carpeta').order_by('-fecha_publicacion')[:10]
        
        # Distribución por tipo de archivo
        from django.db.models import Count
        context['distribucion_tipos'] = Documento.objects.filter(
            publicado=True
        ).values('extension').annotate(
            total=Count('id')
        ).order_by('-total')
        
        return context
    
@staff_member_required
@require_GET
def get_carpetas_por_numeral(request):
    """
    Vista AJAX para obtener carpetas filtradas por numeral
    Usada en el admin para filtrado dinámico
    """
    numeral_id = request.GET.get('numeral_id')
    app = request.GET.get('app', 'transparencia')
    
    if not numeral_id:
        return JsonResponse({'carpetas': []})
    
    try:
        # Importar el modelo correcto según la app
        if app == 'transparencia':
            from .models import Carpeta
            modelo_carpeta = Carpeta
        elif app == 'comude':
            from comude.models import CarpetaComude as modelo_carpeta
        elif app == 'rendicion_cuentas':
            from rendicion_cuentas.models import CarpetaRendicion as modelo_carpeta
        elif app == 'informes_congreso':
            from informes_congreso.models import CarpetaInformesCongreso as modelo_carpeta
        else:
            return JsonResponse({'carpetas': []})
        
        # Obtener carpetas del numeral
        carpetas = modelo_carpeta.objects.filter(
            numeral_id=numeral_id
        ).select_related('padre', 'numeral').order_by('-orden', '-nombre')
        
        # Construir lista con rutas completas
        carpetas_data = []
        for carpeta in carpetas:
            carpetas_data.append({
                'id': carpeta.id,
                'nombre': carpeta.nombre,
                'ruta_completa': carpeta.get_ruta_completa(),
                'nivel': carpeta.nivel()
            })
        
        return JsonResponse({'carpetas': carpetas_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)