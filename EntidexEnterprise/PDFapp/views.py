from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import *
from django.http import JsonResponse
from .models import PDFDocument, PDFInteraccion  # Asegurate de importar tus modelos
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from django.shortcuts import render
from langchain.llms import Ollama
from pypdf import PdfReader
from langchain.prompts import PromptTemplate
from django.conf import settings
from .langchain_pipeline import graph, vector_store, Document  # Importa lo necesario
from django.core.files.storage import default_storage
from langchain_text_splitters import RecursiveCharacterTextSplitter
import datetime
import os
import json
import hashlib
import shutil


def indexView(request):
    return render(request, "vistaPrincipal.html")  # Crea este template luego


def archivosView(request):
    # Aquí renderizas tu archivo HTML
    return render(request, "vistaConsultar.html")


def pdfView(request):
    return render(request, "vistaPDF.html")


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
        obj = PDFDocument.objects.create(
            numero_caso=numero_caso,
            titulo=titulo,
            fecha=fecha,
            tipo_documento=tipo_documento,
            jurisdiccion=jurisdiccion,
            archivo_pdf=archivo_pdf,
        )
        guardar_vectorstore_para_pdf(obj.archivo_pdf.path, numero_caso)

        return JsonResponse(
            {"mensaje": "Archivo guardado correctamente", "nombre": archivo_pdf.name}
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def guardar_vectorstore_para_pdf(archivo_path, numero_caso):
    vectorstore_dir = f"./chroma_dbs/{numero_caso}"
    os.makedirs(vectorstore_dir, exist_ok=True)

    # Leer y procesar el PDF
    reader = PdfReader(archivo_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    # Dividir en chunks (mejor para embeddings)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = splitter.split_documents([Document(page_content=text)])

    # Crear y guardar el vector store
    vector_store = Chroma(
        collection_name=f"collection_{numero_caso}",
        embedding_function=HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        ),
        persist_directory=vectorstore_dir,
    )
    vector_store.add_documents(docs)
    
    


@csrf_exempt
def upload_pdf(request):
    global vector_store
    if request.method == "POST":
        try:
            pdf_file = request.FILES["file"]
            relative_path = f"archivos/{pdf_file.name}"
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
    query = request.GET.get("q", "")
    if query:
        pdfs = PDFDocument.objects.filter(titulo__icontains=query)
    else:
        pdfs = PDFDocument.objects.all().order_by("-creado_en")

    # Preparar los datos para JSON
    archivos_list = []
    for pdf in pdfs:
        archivos_list.append(
            {
                "id": pdf.id,
                "numero_caso": pdf.numero_caso,
                "titulo": pdf.titulo,
                "fecha": pdf.fecha.strftime("%Y-%m-%d") if pdf.fecha else None,
                "tipo_documento": pdf.tipo_documento,
                "jurisdiccion": pdf.jurisdiccion,
                "pdf_url": (
                    request.build_absolute_uri(
                        os.path.join(settings.MEDIA_URL, str(pdf.archivo_pdf))
                    )
                    if pdf.archivo_pdf
                    else None
                ),
                "creado_en": (
                    pdf.creado_en.strftime("%Y-%m-%d %H:%M:%S")
                    if pdf.creado_en
                    else None
                ),
            }
        )

    response_data = {
        "success": True,
        "count": len(archivos_list),
        "results": archivos_list,
        "search_query": query,
    }

    return JsonResponse(response_data, safe=False)


@csrf_exempt
@require_POST
def eliminar_pdf(request):
    """Elimina un PDF por ID"""
    try:
        pdf_id = request.POST.get("id")
        if not pdf_id:
            return JsonResponse({"error": "ID no proporcionado"}, status=400)

        documento = PDFDocument.objects.get(id=pdf_id)
        documento.archivo_pdf.delete()  # Elimina el archivo físico
        documento.delete()  # Elimina el registro

        return JsonResponse({"success": True})

    except PDFDocument.DoesNotExist:
        return JsonResponse({"error": "Documento no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@csrf_exempt
def consultar_pdf(request):
    try:
        data = json.loads(request.body)
        numero_caso = data.get("pdf_id")
        pregunta = data.get("question")

        if not numero_caso or not pregunta:
            return JsonResponse({"error": "Faltan datos"}, status=400)

        # Buscar el documento asociado
        try:
            documento = PDFDocument.objects.get(numero_caso=numero_caso)
        except PDFDocument.DoesNotExist:
            return JsonResponse({"error": "No se encontró el documento PDF"}, status=404)

        # Cargar el vectorstore
        vectorstore_dir = f"./chroma_dbs/{numero_caso}"
        if not os.path.exists(vectorstore_dir):
            return JsonResponse({"error": "No se encontró el vector store para ese caso"}, status=404)

        vector_store = Chroma(
            collection_name=f"collection_{numero_caso}",
            embedding_function=HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            ),
            persist_directory=vectorstore_dir,
        )

        # Ejecutar el grafo de razonamiento
        state = {"question": pregunta, "context": [], "answer": ""}
        state = graph.invoke(state)

        respuesta = state["answer"]

        # Guardar la interacción
        PDFInteraccion.objects.create(
            pdf_document=documento,
            prompt=pregunta,
            respuesta=respuesta
        )

        return JsonResponse({"answer": respuesta})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

@require_GET
@csrf_exempt
def obtener_interacciones(request, numero_caso):
    try:
        documento = PDFDocument.objects.get(numero_caso=numero_caso)
        interacciones = PDFInteraccion.objects.filter(pdf_document=documento).order_by('creado_en')

        data = {
            "interacciones": [
                {
                    "prompt": i.prompt,
                    "respuesta": i.respuesta,
                    "fecha": i.creado_en.isoformat()
                }
                for i in interacciones
            ]
        }

        return JsonResponse(data)

    except PDFDocument.DoesNotExist:
        return JsonResponse({"interacciones": []})    


@require_POST
@csrf_exempt
def eliminar_pdf(request):
    from django.views.decorators.csrf import csrf_exempt
    import json

    try:
        data = json.loads(request.body)
        pdf_id = data.get("pdf_id")
        if not pdf_id:
            return JsonResponse({"error": "ID no proporcionado"}, status=400)

        pdf = PDFDocument.objects.get(id=pdf_id)

        # Eliminar el archivo físico
        if pdf.archivo_pdf and os.path.isfile(pdf.archivo_pdf.path):
            os.remove(pdf.archivo_pdf.path)

        # Eliminar de la BD
        pdf.delete()

        return JsonResponse({"success": True})
    except PDFDocument.DoesNotExist:
        return JsonResponse({"error": "PDF no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

def obtener_pdf(request, pdf_id):
    try:
        pdf = PDFDocument.objects.get(id=pdf_id)
        return JsonResponse({
            'id': pdf.id,
            'numero_caso': pdf.numero_caso,
            'titulo': pdf.titulo,
            'fecha': pdf.fecha.isoformat(),
            'tipo_documento': pdf.tipo_documento,
            'jurisdiccion': pdf.jurisdiccion,
        })
    except PDFDocument.DoesNotExist:
        return JsonResponse({'error': 'PDF no encontrado'}, status=404)
    

@csrf_exempt
@require_POST
def editar_pdf(request):
    try:
        pdf_id = request.POST.get('pdf_id')
        pdf = PDFDocument.objects.get(id=pdf_id)
    except PDFDocument.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'PDF no encontrado'})

    # Actualizar campos básicos
    pdf.numero_caso = request.POST.get('numero_caso')
    pdf.titulo = request.POST.get('titulo')
    pdf.fecha = request.POST.get('fecha')
    pdf.tipo_documento = request.POST.get('tipo_documento')
    pdf.jurisdiccion = request.POST.get('jurisdiccion')

    nuevo_pdf = request.FILES.get('archivo_pdf')
    if nuevo_pdf:
        # Eliminar vectorstore antiguo (solo si cambia el archivo)
        vectorstore_dir = f"./chroma_dbs/{pdf.numero_caso}"
        if os.path.exists(vectorstore_dir):
            shutil.rmtree(vectorstore_dir)

        # Guardar el nuevo archivo
        pdf.archivo_pdf = nuevo_pdf

    pdf.save()

    # Volver a generar embeddings solo si hay un nuevo archivo
    if nuevo_pdf:
        guardar_vectorstore_para_pdf(pdf.archivo_pdf.path, pdf.numero_caso)

    return JsonResponse({'success': True})