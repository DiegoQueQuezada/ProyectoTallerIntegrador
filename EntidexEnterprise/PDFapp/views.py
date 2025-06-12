from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import *
from django.http import JsonResponse
from .models import PDFDocument
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from django.shortcuts import render
from langchain.llms import Ollama
from pypdf import PdfReader
from langchain.prompts import PromptTemplate
from django.conf import settings
from .langchain_pipeline import graph, vector_store, Document  # Importa lo necesario
from django.core.files.storage import default_storage
import datetime
import os
import json
import hashlib
import shutil

def indexView(request):
    return render(request, "index.html")  # Crea este template luego


def archivosView(request):
    # Aquí renderizas tu archivo HTML
    return render(request, "archivosView.html")


def pdfView(request):
    return render(request, "pdfView.html")


@csrf_exempt
@require_POST
def guardar_pdf(request):
    try:
        numero_caso = request.POST.get("numero_caso")
        titulo = request.POST.get("titulo")
        fecha = request.POST.get("fecha")
        tipo_documento = request.POST.get("tipo_documento")
        jurisdiccion = request.POST.get("jurisdiccion")
        archivo_pdf = request.FILES.get("archivo_pdf")

        if not archivo_pdf:
            return JsonResponse(
                {"error": "No se proporcionó ningún archivo PDF."}, status=400
            )

        # Crear y guardar el objeto en la base de datos usando el modelo
        PDFDocument.objects.create(
            numero_caso=numero_caso,
            titulo=titulo,
            fecha=fecha,
            tipo_documento=tipo_documento,
            jurisdiccion=jurisdiccion,
            archivo_pdf=archivo_pdf,
        )

        return JsonResponse(
            {"mensaje": "Archivo guardado correctamente", "nombre": archivo_pdf.name}
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def upload_pdf(request):
    global vector_store
    if request.method == "POST":
        try:
            pdf_file = request.FILES["file"]
            relative_path = f"uploads/{pdf_file.name}"
            absolute_file_path = os.path.join(settings.MEDIA_ROOT, relative_path)

            # Guardar archivo si no existe
            if not default_storage.exists(relative_path):
                default_storage.save(relative_path, pdf_file)

            # Calcular hash del archivo guardado
            current_hash = file_hash(absolute_file_path)

            # Leer un archivo donde guardas el último hash para comparar
            hash_file_path = "./chroma_langchain_db/last_hash.txt"
            last_hash = None
            if os.path.exists(hash_file_path):
                with open(hash_file_path, "r") as f:
                    last_hash = f.read().strip()

            if current_hash != last_hash:
                # Es un archivo nuevo o modificado, entonces borrar DB y crear nueva
                shutil.rmtree("./chroma_langchain_db", ignore_errors=True)

                vector_store = Chroma(
                    collection_name="example_collectionV2",
                    embedding_function=HuggingFaceEmbeddings(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    ),
                    persist_directory="./chroma_langchain_db",
                )

                # Leer texto PDF
                reader = PdfReader(absolute_file_path)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                from langchain_core.documents import Document

                doc = Document(page_content=text)
                vector_store.add_documents([doc])

                # Guardar hash para futuras comparaciones
                os.makedirs("./chroma_langchain_db", exist_ok=True)
                with open(hash_file_path, "w") as f:
                    f.write(current_hash)

            else:
                # Si es el mismo archivo, solo carga el vector_store sin borrar
                vector_store = Chroma(
                    collection_name="example_collectionV2",
                    embedding_function=HuggingFaceEmbeddings(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    ),
                    persist_directory="./chroma_langchain_db",
                )

            question = request.POST.get("question", "¿De qué trata este documento?")
            state = {"question": question, "context": [], "answer": ""}
            state = graph.invoke(state)
            return JsonResponse({"answer": state["answer"]})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no soportado"}, status=405)

def file_hash(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

@csrf_exempt
@require_GET
def listar_pdfs(request):
    # Filtrar por búsqueda si existe
    query = request.GET.get('q', '')
    if query:
        pdfs = PDFDocument.objects.filter(titulo__icontains=query)
    else:
        pdfs = PDFDocument.objects.all().order_by('-creado_en')
    
    # Preparar los datos para JSON
    archivos_list = []
    for pdf in pdfs:
        archivos_list.append({
            'id': pdf.id,
            'numero_caso': pdf.numero_caso,
            'titulo': pdf.titulo,
            'fecha': pdf.fecha.strftime('%Y-%m-%d') if pdf.fecha else None,
            'tipo_documento': pdf.tipo_documento,
            'jurisdiccion': pdf.jurisdiccion,
            'pdf_url': request.build_absolute_uri(os.path.join(settings.MEDIA_URL, str(pdf.archivo_pdf))) if pdf.archivo_pdf else None,
            'creado_en': pdf.creado_en.strftime('%Y-%m-%d %H:%M:%S') if pdf.creado_en else None
        })
    
    response_data = {
        'success': True,
        'count': len(archivos_list),
        'results': archivos_list,
        'search_query': query
    }
    
    return JsonResponse(response_data, safe=False)

@csrf_exempt
@require_POST
def eliminar_pdf(request):
    """Elimina un PDF por ID"""
    try:
        pdf_id = request.POST.get('id')
        if not pdf_id:
            return JsonResponse({'error': 'ID no proporcionado'}, status=400)

        documento = PDFDocument.objects.get(id=pdf_id)
        documento.archivo_pdf.delete()  # Elimina el archivo físico
        documento.delete()  # Elimina el registro

        return JsonResponse({'success': True})

    except PDFDocument.DoesNotExist:
        return JsonResponse({'error': 'Documento no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@csrf_exempt
@require_POST
def consultar_pdf(request):
    try:
        data = json.loads(request.body)
        pdf_id = data.get('pdf_id')
        question = data.get('question')
        
        if not pdf_id or not question:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        # Obtener el documento PDF
        pdf_doc = PDFDocument.objects.get(id=pdf_id)
        pdf_path = os.path.join(settings.MEDIA_ROOT, str(pdf_doc.archivo_pdf))
        
        # Procesar el PDF y responder la pregunta (usando tu lógica existente)
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        # Aquí usarías tu pipeline de LangChain para responder
        state = {"question": question, "context": text, "answer": ""}
        state = graph.invoke(state)
        
        print("DATAAAAAA");
        print(state['answer']);
        return JsonResponse({'answer': state['answer']})
        
    except PDFDocument.DoesNotExist:
        return JsonResponse({'error': 'Documento no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)