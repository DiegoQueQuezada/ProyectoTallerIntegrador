from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import PDFDocument
from django.shortcuts import render
import datetime
import os

def indexView(request):
    return render(request, "index.html")  # Crea este template luego
def archivosView(request):
    # Aquí renderizas tu archivo HTML
    return render(request, "archivosView.html")
def pdfView(request):
    return render(request, 'pdfView.html')
@csrf_exempt
@require_POST
def guardar_pdf(request):
    try:
        numero_caso = request.POST.get('numero_caso')
        titulo = request.POST.get('titulo')
        fecha = request.POST.get('fecha')
        tipo_documento = request.POST.get('tipo_documento')
        jurisdiccion = request.POST.get('jurisdiccion')
        archivo_pdf = request.FILES.get('archivo_pdf')

        if not archivo_pdf:
            return JsonResponse({'error': 'No se proporcionó ningún archivo PDF.'}, status=400)

        # Crear y guardar el objeto en la base de datos usando el modelo
        PDFDocument.objects.create(
            numero_caso=numero_caso,
            titulo=titulo,
            fecha=fecha,
            tipo_documento=tipo_documento,
            jurisdiccion=jurisdiccion,
            archivo_pdf=archivo_pdf
        )

        return JsonResponse({'mensaje': 'Archivo guardado correctamente', 'nombre': archivo_pdf.name})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)