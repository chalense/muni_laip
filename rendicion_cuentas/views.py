from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Prefetch
from django.http import FileResponse, Http404
from django.views import View
from .models import NumeralRendicion, CarpetaRendicion, DocumentoRendicion


class NumeralRendicionListView(ListView):
    model = NumeralRendicion
    template_name = 'rendicion_cuentas/numeral_list.html'
    context_object_name = 'numerales'
    
    def get_queryset(self):
        return NumeralRendicion.objects.filter(activo=True).annotate(
            total_documentos=Count('documentos', filter=Q(documentos__publicado=True)),
            total_carpetas=Count('carpetas', filter=Q(carpetas__padre__isnull=True))
        ).select_related().prefetch_related(
            Prefetch(
                'documentos',
                queryset=DocumentoRendicion.objects.filter(publicado=True, carpeta__isnull=True).order_by('-destacado', '-fecha_publicacion')
            )
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_numerales'] = self.get_queryset().count()
        context['total_documentos_global'] = DocumentoRendicion.objects.filter(publicado=True).count()
        context['documentos_destacados'] = DocumentoRendicion.objects.filter(
            publicado=True, destacado=True
        ).select_related('numeral', 'carpeta').order_by('-fecha_publicacion')[:5]
        return context


class NumeralRendicionDetailView(DetailView):
    model = NumeralRendicion
    template_name = 'rendicion_cuentas/numeral_detail.html'
    context_object_name = 'numeral'
    slug_field = 'slug'
    
    def get_queryset(self):
        return NumeralRendicion.objects.filter(activo=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        numeral = self.object
        
        carpetas_raiz = CarpetaRendicion.objects.filter(
            numeral=numeral, padre__isnull=True
        ).annotate(
            total_docs=Count('documentos', filter=Q(documentos__publicado=True))
        ).order_by('-orden', '-nombre')
        
        estructura = []
        for carpeta_raiz in carpetas_raiz:
            estructura.append({
                'carpeta': carpeta_raiz,
                'subcarpetas': self._construir_arbol(carpeta_raiz)
            })
        
        context['estructura_carpetas'] = estructura
        context['documentos_raiz'] = DocumentoRendicion.objects.filter(
            numeral=numeral, carpeta__isnull=True, publicado=True
        ).order_by('-destacado', '-fecha_publicacion')
        
        context['total_documentos'] = DocumentoRendicion.objects.filter(numeral=numeral, publicado=True).count()
        context['total_carpetas'] = CarpetaRendicion.objects.filter(numeral=numeral).count()
        context['total_descargas'] = sum(doc.descargas for doc in DocumentoRendicion.objects.filter(numeral=numeral, publicado=True))
        
        context['documentos_destacados'] = DocumentoRendicion.objects.filter(
            numeral=numeral, publicado=True, destacado=True
        ).select_related('carpeta').order_by('-fecha_publicacion')[:3]
        
        context['documentos_recientes'] = DocumentoRendicion.objects.filter(
            numeral=numeral, publicado=True
        ).select_related('carpeta').order_by('-fecha_publicacion')[:5]
        
        return context
    
    def _construir_arbol(self, carpeta_padre):
        subcarpetas = CarpetaRendicion.objects.filter(padre=carpeta_padre).annotate(
            total_docs=Count('documentos', filter=Q(documentos__publicado=True))
        ).order_by('-orden', 'nombre')
        
        estructura = []
        for subcarpeta in subcarpetas:
            documentos = DocumentoRendicion.objects.filter(
                carpeta=subcarpeta, publicado=True
            ).order_by('-destacado', '-fecha_publicacion')
            
            estructura.append({
                'carpeta': subcarpeta,
                'documentos': documentos,
                'subcarpetas': self._construir_arbol(subcarpeta)
            })
        return estructura


class CarpetaRendicionDetailView(DetailView):
    model = CarpetaRendicion
    template_name = 'rendicion_cuentas/carpeta_detail.html'
    context_object_name = 'carpeta'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carpeta = self.object
        
        context['breadcrumb'] = carpeta.get_ruta_breadcrumb()
        context['subcarpetas'] = CarpetaRendicion.objects.filter(padre=carpeta).annotate(
            total_docs=Count('documentos', filter=Q(documentos__publicado=True))
        ).order_by('-orden', 'nombre')
        
        context['documentos'] = DocumentoRendicion.objects.filter(
            carpeta=carpeta, publicado=True
        ).order_by('-destacado', '-fecha_publicacion')
        
        context['total_documentos'] = context['documentos'].count()
        context['total_subcarpetas'] = context['subcarpetas'].count()
        return context


class DocumentoRendicionDownloadView(View):
    def get(self, request, pk):
        documento = get_object_or_404(DocumentoRendicion, pk=pk, publicado=True)
        documento.incrementar_descargas()
        
        if not documento.archivo:
            raise Http404("Archivo no encontrado")
        
        try:
            response = FileResponse(documento.archivo.open('rb'), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{documento.archivo.name.split("/")[-1]}"'
            return response
        except FileNotFoundError:
            raise Http404("Archivo no encontrado en el servidor")


class BusquedaRendicionView(ListView):
    model = DocumentoRendicion
    template_name = 'rendicion_cuentas/busqueda.html'
    context_object_name = 'documentos'
    paginate_by = 20
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        numeral_filter = self.request.GET.get('numeral', '')
        tipo_filter = self.request.GET.get('tipo', '')
        
        queryset = DocumentoRendicion.objects.filter(publicado=True).select_related('numeral', 'carpeta')
        
        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(numeral__titulo_corto__icontains=query)
            )
        
        if numeral_filter:
            queryset = queryset.filter(numeral__codigo=numeral_filter)
        
        if tipo_filter:
            queryset = queryset.filter(extension=tipo_filter.upper())
        
        return queryset.order_by('-fecha_publicacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['numeral_filter'] = self.request.GET.get('numeral', '')
        context['tipo_filter'] = self.request.GET.get('tipo', '')
        context['numerales'] = NumeralRendicion.objects.filter(activo=True).order_by('codigo')
        context['tipos_archivo'] = DocumentoRendicion.objects.filter(publicado=True).values_list('extension', flat=True).distinct().order_by('extension')
        context['total_resultados'] = self.get_queryset().count()
        return context


class EstadisticasRendicionView(ListView):
    model = NumeralRendicion
    template_name = 'rendicion_cuentas/estadisticas.html'
    context_object_name = 'numerales'
    
    def get_queryset(self):
        return NumeralRendicion.objects.filter(activo=True).annotate(
            total_documentos=Count('documentos', filter=Q(documentos__publicado=True)),
            total_descargas=Count('documentos__descargas')
        ).order_by('codigo')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_numerales'] = NumeralRendicion.objects.filter(activo=True).count()
        context['total_documentos'] = DocumentoRendicion.objects.filter(publicado=True).count()
        context['total_carpetas'] = CarpetaRendicion.objects.count()
        context['total_descargas'] = sum(doc.descargas for doc in DocumentoRendicion.objects.filter(publicado=True))
        context['documentos_populares'] = DocumentoRendicion.objects.filter(publicado=True).select_related('numeral', 'carpeta').order_by('-descargas')[:10]
        context['documentos_recientes'] = DocumentoRendicion.objects.filter(publicado=True).select_related('numeral', 'carpeta').order_by('-fecha_publicacion')[:10]
        
        from django.db.models import Count
        context['distribucion_tipos'] = DocumentoRendicion.objects.filter(publicado=True).values('extension').annotate(total=Count('id')).order_by('-total')
        return context