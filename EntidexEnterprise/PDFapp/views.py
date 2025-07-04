# pylint: disable=no-member
from django.contrib.auth import logout
import traceback
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import *
from django.http import JsonResponse
from django.contrib import messages
from .models import PDFDocument, PDFInteraccion  # Asegurate de importar tus modelos
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from django.shortcuts import render
from langchain.llms import Ollama
from pypdf import PdfReader
from langchain.prompts import PromptTemplate
from django.conf import settings
from .langchain_pipeline import construir_graph_con, Document
from django.core.files.storage import default_storage
from langchain_text_splitters import RecursiveCharacterTextSplitter
import datetime
import os
import json
import hashlib
import shutil
from langchain.schema import Document
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
import os
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import re


@login_required
def home(request):
    # Muestra solo los PDFs del usuario autenticado
    pdfs = PDFDocument.objects.filter(usuario=request.user)
    return render(request, "home.html", {"pdfs": pdfs})


@login_required
def indexView(request):
    return render(request, "vistaPrincipal.html")  # Crea este template luego


@login_required
def archivosView(request):
    # Aquí renderizas tu archivo HTML
    return render(request, "vistaConsultar.html")


@login_required
def pdfView(request):
    return render(request, "vistaPDF.html")


# pylint: disable=no-member
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import PDFDocument


@login_required
@require_POST
@csrf_exempt
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

        # Verifica si ya existe un documento con ese número de caso para ese usuario
        if PDFDocument.objects.filter(
            numero_caso=numero_caso, usuario=request.user
        ).exists():
            return JsonResponse(
                {
                    "error": f"Ya existe un documento con el número de caso {numero_caso}."
                },
                status=400,
            )

        # Crear y guardar el objeto PDF asociado al usuario logueado
        obj = PDFDocument.objects.create(
            usuario=request.user,  # 👈 Aquí se relaciona con el usuario
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
        print(traceback.format_exc())  # Te muestra la traza completa
        return JsonResponse({"error": str(e)}, status=500)


def loginView(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("index")  # Redirige a la vista protegida
        else:
            return render(
                request, "vistaLogin.html", {"error": "Credenciales inválidas"}
            )
    return render(request, "vistaLogin.html")


def guardar_vectorstore_para_pdf(archivo_path, numero_caso):
    vectorstore_dir = f"./chroma_dbs/{numero_caso}"
    os.makedirs(vectorstore_dir, exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = []

    reader = PdfReader(archivo_path)
    num_paginas = len(reader.pages)
    imagenes = convert_from_path(archivo_path, dpi=400, fmt="jpeg")

    for i, page in enumerate(reader.pages):
        # --- TEXTO DIGITAL ---
        page_text = page.extract_text()
        if page_text and page_text.strip():
            chunks = splitter.split_text(page_text)
            print(f"[DEBUG] Página {i+1} - Texto extraído:")
            print(page_text)
            print(f"[DEBUG] Página {i+1} - Chunks generados:")
            for idx, chunk in enumerate(chunks):
                print(f"Chunk {idx+1}:\n{chunk}\n{'-'*40}")
                docs.append(Document(
                    page_content=f"textoGeneral: {chunk}",
                    metadata={"pagina": i + 1, "fuente": "digital"}
                ))
        # --- OCR SIEMPRE ---
        try:
            img = imagenes[i]
            texto_pagina_ocr = pytesseract.image_to_string(img, lang="spa")
            print(f"[DEBUG] OCR Página {i+1} - Texto extraído:")
            print(texto_pagina_ocr)
            if texto_pagina_ocr.strip():
                chunks_ocr = splitter.split_text(texto_pagina_ocr)
                print(f"[DEBUG] OCR Página {i+1} - Chunks generados:")
                for idx, chunk in enumerate(chunks_ocr):
                    print(f"Chunk OCR {idx+1}:\n{chunk}\n{'-'*40}")
                    docs.append(Document(
                        page_content=f"imagen: {chunk}",
                        metadata={"pagina": i + 1, "fuente": "ocr_tesseract"}
                    ))
        except Exception as e:
            print(f"⚠️ Error en OCR página {i+1}: {e}")

    if not docs:
        raise ValueError("❌ No se pudo extraer texto del PDF, ni con OCR.")

    # Crear el vectorstore
    vector_store = Chroma(
        collection_name=f"collection_{numero_caso}",
        embedding_function=HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        ),
        persist_directory=vectorstore_dir,
    )

    vector_store.add_documents(docs)
    with open(os.path.join(vectorstore_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump({"total_paginas": num_paginas}, f)

    print(f"✅ Embeddings guardados en: {vectorstore_dir} (Total chunks: {len(docs)})")

    # Responder preguntas tipo "de que trata la pagina X"
    for i in range(num_paginas):
        pregunta = f"de que trata la pagina {i+1}"
        # Buscar los chunks de esa página
        pagina_chunks = [doc.page_content for doc in docs if doc.metadata.get("pagina") == i+1]
        print(f"[DEBUG] Pregunta: '{pregunta}'")
        print(f"[DEBUG] Chunks usados para la respuesta:")
        for idx, chunk in enumerate(pagina_chunks):
            print(f"Chunk {idx+1}:\n{chunk}\n{'-'*40}")
        # Aquí podrías invocar el modelo si quieres una respuesta automática
        # Por ahora solo loguea los chunks que se usarían


@login_required
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


from django.db.models import Q
import os


@login_required
@require_GET
@csrf_exempt
def listar_pdfs(request):
    query = request.GET.get("q", "")

    # 👇 Filtra solo los PDFs del usuario logueado
    pdfs = PDFDocument.objects.filter(usuario=request.user)

    # 👇 Si hay una búsqueda, aplica filtro por título
    if query:
        pdfs = pdfs.filter(titulo__icontains=query)

    pdfs = pdfs.order_by("-creado_en")

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


# @login_required
# @require_POST
# @csrf_exempt
# def eliminar_pdf(request):
#     """Elimina un PDF por ID"""
#     try:
#         pdf_id = request.POST.get("id")
#         if not pdf_id:
#             return JsonResponse({"error": "ID no proporcionado"}, status=400)

#         documento = PDFDocument.objects.get(id=pdf_id)
#         documento.archivo_pdf.delete()  # Elimina el archivo físico
#         documento.delete()  # Elimina el registro

#         return JsonResponse({"success": True})

#     except PDFDocument.DoesNotExist:
#         return JsonResponse({"error": "Documento no encontrado"}, status=404)
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)

from .langchain_pipeline import construir_graph_auxiliar

@login_required
@require_POST
@csrf_exempt
def consultar_pdf(request):
    try:
        data = json.loads(request.body)
        numero_caso = data.get("pdf_id")
        pregunta = data.get("question")

        if not numero_caso or not pregunta:
            return JsonResponse({"error": "Faltan datos"}, status=400)

        try:
            documento = PDFDocument.objects.get(numero_caso=numero_caso)
        except PDFDocument.DoesNotExist:
            return JsonResponse(
                {"error": "No se encontró el documento PDF"}, status=404
            )

        vectorstore_dir = f"./chroma_dbs/{numero_caso}"
        if not os.path.exists(vectorstore_dir):
            return JsonResponse(
                {"error": "No se encontró el vector store para ese caso"}, status=404
            )

        vector_store = Chroma(
            collection_name=f"collection_{numero_caso}",
            embedding_function=HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            ),
            persist_directory=vectorstore_dir,
        )

        # Detectar si la pregunta pide una página específica
        match = re.search(r"p[aá]gina[s]? (\d+)", pregunta, re.IGNORECASE)
        context = []
        if match:
            pagina = int(match.group(1))
            docs = vector_store.get(where={"pagina": pagina})
            if docs and "documents" in docs and len(docs["documents"]) > 0:
                context = docs["documents"]  # Lista de strings (chunks)
                print(f"[DEBUG] Chunks extraídos para página {pagina}:")
                for idx, chunk in enumerate(context):
                    print(f"Chunk {idx+1}:\n{chunk}\n{'-'*40}")
                # Usar grafo auxiliar SOLO con estos chunks
                graph_aux = construir_graph_auxiliar()
                state = {"question": pregunta, "context": context, "answer": ""}
                state = graph_aux.invoke(state)
                respuesta = state["answer"]
                # ...guardar y devolver respuesta...
                PDFInteraccion.objects.create(
                    pdf_document=documento, prompt=pregunta, respuesta=respuesta
                )
                return JsonResponse({"answer": respuesta})
            
        # 💡 Construir el grafo con este vector_store específico
        graph = construir_graph_con(vector_store)

        state = {"question": pregunta, "context": context, "answer": ""}
        state = graph.invoke(state)

        respuesta = state["answer"]
        print("RESPUESTA")
        print(respuesta)
        PDFInteraccion.objects.create(
            pdf_document=documento, prompt=pregunta, respuesta=respuesta
        )
        return JsonResponse({"answer": respuesta})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_GET
@csrf_exempt
def obtener_interacciones(request, numero_caso):
    try:
        documento = PDFDocument.objects.get(numero_caso=numero_caso)
        interacciones = PDFInteraccion.objects.filter(pdf_document=documento).order_by(
            "creado_en"
        )

        data = {
            "interacciones": [
                {
                    "prompt": i.prompt,
                    "respuesta": i.respuesta,
                    "fecha": i.creado_en.isoformat(),
                }
                for i in interacciones
            ]
        }

        return JsonResponse(data)

    except PDFDocument.DoesNotExist:
        return JsonResponse({"interacciones": []})


@login_required
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


@login_required
def obtener_pdf(request, pdf_id):
    try:
        pdf = PDFDocument.objects.get(id=pdf_id)
        return JsonResponse(
            {
                "id": pdf.id,
                "numero_caso": pdf.numero_caso,
                "titulo": pdf.titulo,
                "fecha": pdf.fecha.isoformat(),
                "tipo_documento": pdf.tipo_documento,
                "jurisdiccion": pdf.jurisdiccion,
            }
        )
    except PDFDocument.DoesNotExist:
        return JsonResponse({"error": "PDF no encontrado"}, status=404)


@login_required
@csrf_exempt
@require_POST
def editar_pdf(request):
    try:
        pdf_id = request.POST.get("pdf_id")
        pdf = PDFDocument.objects.get(id=pdf_id)
    except PDFDocument.DoesNotExist:
        return JsonResponse({"success": False, "error": "PDF no encontrado"})

    # Actualizar campos básicos
    pdf.numero_caso = request.POST.get("numero_caso")
    pdf.titulo = request.POST.get("titulo")
    pdf.fecha = request.POST.get("fecha")
    pdf.tipo_documento = request.POST.get("tipo_documento")
    pdf.jurisdiccion = request.POST.get("jurisdiccion")

    nuevo_pdf = request.FILES.get("archivo_pdf")
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

    return JsonResponse({"success": True})


def logoutView(request):
    logout(request)
    messages.success(request, "Sesión cerrada con éxito.")
    return redirect("login")
