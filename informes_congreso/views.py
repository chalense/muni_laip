from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Prefetch
from django.http import FileResponse, Http404
from django.views import View
from .models import NumeralInformesCongreso, CarpetaInformesCongreso, DocumentoInformesCongreso


class NumeralInformesCongresoListView(ListView):
    model = NumeralInformesCongreso
    template_name = 'informes_congreso/numeral_list.html'
    context_object_name = 'numerales'
    
    def get_queryset(self):
        return NumeralInformesCongreso.objects.filter(activo=True).annotate(
            total_documentos=Count('documentos', filter=Q(documentos__publicado=True)),
            total_carpetas=Count('carpetas', filter=Q(carpetas__padre__isnull=True))
        ).select_related().prefetch_related(
            Prefetch(
                'documentos',
                queryset=DocumentoInformesCongreso.objects.filter(publicado=True, carpeta__isnull=True).order_by('-destacado', '-fecha_publicacion')
            )
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_numerales'] = self.get_queryset().count()
        context['total_documentos_global'] = DocumentoInformesCongreso.objects.filter(publicado=True).count()
        context['documentos_destacados'] = DocumentoInformesCongreso.objects.filter(
            publicado=True, destacado=True
        ).select_related('numeral', 'carpeta').order_by('-fecha_publicacion')[:5]
        
        # Marco legal específico
        context['marco_legal'] = {
            'decreto': 'Decreto 101-97',
            'articulo': 'Artículo 17 Ter',
            'descripcion': 'Los sujetos obligados a las disposiciones de la presente Ley, con el propósito de brindar a la ciudadanía guatemalteca transparencia en la gestión pública, además de cumplir con la entrega de información y documentación con la periodicidad que establece esta Ley, deberán mostrar y actualizar por lo menos cada treinta (30) días, a través de sus sitios web de acceso libre, abierto y gratuito de datos, y por escrito a las Comisiones de Probidad, de Finanzas Públicas y Moneda y a la Extraordinaria Nacional por la Transparencia, del Congreso de la República de Guatemala.'
        }
        
        return context


class NumeralInformesCongresoDetailView(DetailView):
    model = NumeralInformesCongreso
    template_name = 'informes_congreso/numeral_detail.html'
    context_object_name = 'numeral'
    slug_field = 'slug'
    
    def get_queryset(self):
        return NumeralInformesCongreso.objects.filter(activo=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        numeral = self.object
        
        carpetas_raiz = CarpetaInformesCongreso.objects.filter(
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
        context['documentos_raiz'] = DocumentoInformesCongreso.objects.filter(
            numeral=numeral, carpeta__isnull=True, publicado=True
        ).order_by('-destacado', '-fecha_publicacion')
        
        context['total_documentos'] = DocumentoInformesCongreso.objects.filter(numeral=numeral, publicado=True).count()
        context['total_carpetas'] = CarpetaInformesCongreso.objects.filter(numeral=numeral).count()
        context['total_descargas'] = sum(doc.descargas for doc in DocumentoInformesCongreso.objects.filter(numeral=numeral, publicado=True))
        
        context['documentos_destacados'] = DocumentoInformesCongreso.objects.filter(
            numeral=numeral, publicado=True, destacado=True
        ).select_related('carpeta').order_by('-fecha_publicacion')[:3]
        
        context['documentos_recientes'] = DocumentoInformesCongreso.objects.filter(
            numeral=numeral, publicado=True
        ).select_related('carpeta').order_by('-fecha_publicacion')[:5]
        
        return context
    
    def _construir_arbol(self, carpeta_padre):
        subcarpetas = CarpetaInformesCongreso.objects.filter(padre=carpeta_padre).annotate(
            total_docs=Count('documentos', filter=Q(documentos__publicado=True))
        ).order_by('-orden', 'nombre')
        
        estructura = []
        for subcarpeta in subcarpetas:
            documentos = DocumentoInformesCongreso.objects.filter(
                carpeta=subcarpeta, publicado=True
            ).order_by('-destacado', '-fecha_publicacion')
            
            estructura.append({
                'carpeta': subcarpeta,
                'documentos': documentos,
                'subcarpetas': self._construir_arbol(subcarpeta)
            })
        return estructura


class CarpetaInformesCongresoDetailView(DetailView):
    model = CarpetaInformesCongreso
    template_name = 'informes_congreso/carpeta_detail.html'
    context_object_name = 'carpeta'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carpeta = self.object
        
        context['breadcrumb'] = carpeta.get_ruta_breadcrumb()
        context['subcarpetas'] = CarpetaInformesCongreso.objects.filter(padre=carpeta).annotate(
            total_docs=Count('documentos', filter=Q(documentos__publicado=True))
        ).order_by('-orden', 'nombre')
        
        context['documentos'] = DocumentoInformesCongreso.objects.filter(
            carpeta=carpeta, publicado=True
        ).order_by('-destacado', '-fecha_publicacion')
        
        context['total_documentos'] = context['documentos'].count()
        context['total_subcarpetas'] = context['subcarpetas'].count()
        return context


class DocumentoInformesCongresoDownloadView(View):
    def get(self, request, pk):
        documento = get_object_or_404(DocumentoInformesCongreso, pk=pk, publicado=True)
        documento.incrementar_descargas()
        
        if not documento.archivo:
            raise Http404("Archivo no encontrado")
        
        try:
            response = FileResponse(documento.archivo.open('rb'), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{documento.archivo.name.split("/")[-1]}"'
            return response
        except FileNotFoundError:
            raise Http404("Archivo no encontrado en el servidor")


class BusquedaInformesCongresoView(ListView):
    model = DocumentoInformesCongreso
    template_name = 'informes_congreso/busqueda.html'
    context_object_name = 'documentos'
    paginate_by = 20
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        numeral_filter = self.request.GET.get('numeral', '')
        tipo_filter = self.request.GET.get('tipo', '')
        
        queryset = DocumentoInformesCongreso.objects.filter(publicado=True).select_related('numeral', 'carpeta')
        
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
        context['numerales'] = NumeralInformesCongreso.objects.filter(activo=True).order_by('codigo')
        context['tipos_archivo'] = DocumentoInformesCongreso.objects.filter(publicado=True).values_list('extension', flat=True).distinct().order_by('extension')
        context['total_resultados'] = self.get_queryset().count()
        return context


class EstadisticasInformesCongresoView(ListView):
    model = NumeralInformesCongreso
    template_name = 'informes_congreso/estadisticas.html'
    context_object_name = 'numerales'
    
    def get_queryset(self):
        return NumeralInformesCongreso.objects.filter(activo=True).annotate(
            total_documentos=Count('documentos', filter=Q(documentos__publicado=True)),
            total_descargas=Count('documentos__descargas')
        ).order_by('codigo')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_numerales'] = NumeralInformesCongreso.objects.filter(activo=True).count()
        context['total_documentos'] = DocumentoInformesCongreso.objects.filter(publicado=True).count()
        context['total_carpetas'] = CarpetaInformesCongreso.objects.count()
        context['total_descargas'] = sum(doc.descargas for doc in DocumentoInformesCongreso.objects.filter(publicado=True))
        context['documentos_populares'] = DocumentoInformesCongreso.objects.filter(publicado=True).select_related('numeral', 'carpeta').order_by('-descargas')[:10]
        context['documentos_recientes'] = DocumentoInformesCongreso.objects.filter(publicado=True).select_related('numeral', 'carpeta').order_by('-fecha_publicacion')[:10]
        
        from django.db.models import Count
        context['distribucion_tipos'] = DocumentoInformesCongreso.objects.filter(publicado=True).values('extension').annotate(total=Count('id')).order_by('-total')
        return context