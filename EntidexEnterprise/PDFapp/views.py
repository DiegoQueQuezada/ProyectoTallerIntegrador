from django.shortcuts import render
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import PDFDocument
from langchain.llms import Ollama
from pypdf import PdfReader
from langchain.prompts import PromptTemplate
from django.conf import settings
from django.core.files.storage import default_storage
# pylint: disable=no-member
# Create your views here.
def indexView(request):
    """..."""
    return render(request, "index.html")

def pdfView(request):
    """..."""
    return render(request, "pdfView.html")

def archivosView(request):
    """..."""
    return render(request, "archivosView.html")


@csrf_exempt
def upload_pdf(request):
    print("ASLKDHASJKLDHLAJKSDJKASHKJLASHDASKJDLJAS")
    if request.method == "POST":
        try:
            # Guardar el archivo PDF
            pdf_file = request.FILES["file"]
            relative_path = f"uploads/{pdf_file.name}"
            file_path = default_storage.save(relative_path, pdf_file)
            absolute_file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            print(f"Archivo guardado en: {absolute_file_path}")

            # Leer texto del PDF
            reader = PdfReader(absolute_file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()

            # Guardar en el modelo
            PDFDocument.objects.create(title=pdf_file.name, file=relative_path)

            # Procesar pregunta con LangChain y Ollama
            question = request.POST.get("question", "¿De qué trata este documento?")
            llm = Ollama(model="gemma:2b")
            prompt_template = PromptTemplate.from_template(
                "Texto del PDF:\n{text}\nPregunta: {question}"
            )
            formatted_prompt = prompt_template.format(
                text=text, question=question
            )  # Renderiza el prompt

            # Generar respuesta del modelo
            answer = llm(formatted_prompt)

            print("Respuesta:", answer)
            return JsonResponse({"answer": str(answer)})

        except FileNotFoundError as e:
            return JsonResponse(
                {"error": f"No se pudo encontrar el archivo: {str(e)}"}, status=500
            )
        except Exception as e:
            return JsonResponse(
                {"error": f"Error procesando el archivo: {str(e)}"}, status=500
            )

    return render(request, "pdfapp/upload.html")
