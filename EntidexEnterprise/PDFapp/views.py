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


def presentationView(request):
    """..."""
    return render(request, "presentacion.html")


def pdfView(request):
    """..."""
    return render(request, "pdfView.html")


def archivosView(request):
    """..."""
    return render(request, "archivosView.html")


@csrf_exempt
def upload_pdf(request):
    if request.method == "POST":
        try:
            pdf_file = request.FILES["file"]
            relative_path = f"uploads/{pdf_file.name}"
            absolute_file_path = os.path.join(settings.MEDIA_ROOT, relative_path)

            # Verificar si el archivo ya existe en uploads/
            if default_storage.exists(relative_path):
                print(f"El archivo {pdf_file.name} ya existe, no se guarda de nuevo.")
            else:
                # Guardar el archivo porque no existe
                default_storage.save(relative_path, pdf_file)
                print(f"Archivo guardado en: {absolute_file_path}")

            # Leer el texto del PDF (del archivo que ya está en uploads/)
            reader = PdfReader(absolute_file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()

            # Procesar la pregunta
            question = request.POST.get("question", "¿De qué trata este documento?")
            from langchain_ollama import OllamaLLM

            llm = OllamaLLM(model="gemma:2b")
            prompt_template = PromptTemplate.from_template(
                "Texto del PDF:\n{text}\nPregunta: {question}"
            )
            formatted_prompt = prompt_template.format(text=text, question=question)

            answer = llm.invoke(formatted_prompt)

            return JsonResponse({"answer": str(answer)})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return render(request, "pdfapp/upload.html")
