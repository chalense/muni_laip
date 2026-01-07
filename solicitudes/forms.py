from django import forms
from .models import SolicitudInformacion


class SolicitudInformacionForm(forms.ModelForm):
    """
    Formulario para crear solicitudes de información pública
    """
    
    class Meta:
        model = SolicitudInformacion
        fields = [
            'nombre_completo',
            'lugar_residencia',
            'telefono',
            'correo_electronico',
            'medio_entrega',
            'genero',
            'solicitud',
        ]
        widgets = {
            'nombre_completo': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ingrese su nombre completo'
            }),
            'lugar_residencia': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Aldea, caserío, barrio, municipio, departamento'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0000-0000 ó +502 0000-0000',
                'type': 'tel'
            }),
            'correo_electronico': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'ejemplo@correo.com'
            }),
            'medio_entrega': forms.RadioSelect(attrs={
                'class': 'mr-2'
            }),
            'genero': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'solicitud': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 6,
                'placeholder': 'Describa claramente la información que solicita. Sea lo más específico posible para facilitar la búsqueda.'
            }),
        }
        labels = {
            'nombre_completo': 'Nombres y apellidos',
            'lugar_residencia': 'Lugar de residencia',
            'telefono': 'Teléfono',
            'correo_electronico': 'Correo electrónico',
            'medio_entrega': 'Medio de entrega',
            'genero': 'Género',
            'solicitud': 'Solicitud',
        }
        help_texts = {
            'medio_entrega': 'Medio en que requiere la información solicitada. Si no indica el medio, se enviará al correo electrónico proporcionado.',
            'genero': 'Opcional: seleccione el género.',
            'solicitud': 'Descripción clara y precisa de la información solicitada. Con el fin de brindar un mejor servicio, además de describir la información que solicita, se sugiere proporcionar todos los datos que considere que puedan facilitar la búsqueda de dicha información (Fechas, nombres, números de expediente, etc.).',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que género tenga opción vacía
        self.fields['genero'].required = False
        self.fields['genero'].empty_label = "Seleccione una opción (opcional)"