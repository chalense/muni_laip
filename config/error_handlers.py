"""
Handlers personalizados para páginas de error
"""
from django.shortcuts import render


def handler404(request, exception):
    """
    Handler personalizado para error 404 (Página no encontrada)
    """
    return render(request, '404.html', status=404)


def handler500(request):
    """
    Handler personalizado para error 500 (Error del servidor)
    Nota: No recibe 'exception' como parámetro
    """
    return render(request, '500.html', status=500)


def handler403(request, exception):
    """
    Handler personalizado para error 403 (Acceso prohibido)
    """
    return render(request, '403.html', status=403)


def handler400(request, exception):
    """
    Handler personalizado para error 400 (Solicitud incorrecta)
    """
    return render(request, '400.html', status=400)