from django.views.generic import TemplateView
from solicitudes.models import SolicitudInformacion

class HomeView(TemplateView):
    template_name = "home/index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #modulos del sistema
        context['modulos'] = [
            {
                'nombre': 'Información Pública',
                'descripcion': 'Información pública de oficio. Artículo 10 de la Ley de Acceso a la Información Pública.',
                'icono': 'fa-book-open',
                'color': 'blue',
                'url': 'transparencia:numeral_list',
                'numerales': 29,
                'activo': True
            },
            {
                'nombre': 'COMUDE',
                'descripcion': 'Consejo Municipal de Desarrollo -COMUDE-',
                'icono': 'fa-users',
                'color': 'green',
                'url': 'comude:numeral_list',
                'numerales': 12,
                'activo': True
            },
            {
                'nombre': 'Rendición de cuentas',
                'descripcion': 'Memoria de labores, informes y gestión presupuestaria por resultados',
                'icono': 'fa-chart-line',
                'color': 'yellow',
                'url': 'rendicion_cuentas:numeral_list',
                'numerales': 7,
                'activo': True
            },
            {
                'nombre': 'Informes al Congreso',
                'descripcion': 'Informes periódicos al Congreso de la República de Guatemala, según Decreto 101-97 Art. 17 Ter.',
                'icono': 'fa-solid fa-landmark',
                'color': 'purple',
                'url': 'informes_congreso:numeral_list',
                'numerales': 8,
                'activo': True
            },
            {
                'nombre': 'Control Interno',
                'descripcion': 'SINACIG - Sistema Nacional de Control Interno Gubernamental',
                'icono': 'fa-shield-alt',
                'color': 'red',
                'url': 'sinacig:carpeta_list',
                'numerales': 0,
                'activo': True
            },
        ]
        #contador de solicitudes de información
        context['total_solicitudes'] = SolicitudInformacion.objects.count() 
        
        return context