from django.test import TestCase
from .views import guardar_vectorstore_para_pdf
from langchain_chroma import Chroma
import os
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
User = get_user_model()

class GuardarVectorstoreParaPDFTest(TestCase):
    def test_guarda_chunks_texto_y_ocr(self):
        # Ruta a un PDF de prueba con texto y/o imagen
        archivo_path = os.path.join(BASE_DIR, "tests", "resources", "ACEPTACION.pdf")
        numero_caso = "TEST123"
        guardar_vectorstore_para_pdf(archivo_path, numero_caso)
        vectorstore_dir = f"./chroma_dbs/{numero_caso}"
        self.assertTrue(os.path.exists(vectorstore_dir))
        vector_store = Chroma(
            collection_name=f"collection_{numero_caso}",
            persist_directory=vectorstore_dir,
        )
        docs = vector_store.get()
        # Verifica que hay al menos un chunk de texto digital o de OCR
        tiene_texto = any("textoGeneral:" in d for d in docs["documents"])
        tiene_ocr = any("imagen:" in d for d in docs["documents"])
        self.assertTrue(tiene_texto or tiene_ocr, "No se extrajo texto digital ni OCR del PDF de prueba.")


class GuardarPDFViewTest(TestCase):
    def setUp(self):
        # Crear usuario de prueba usando el modelo personalizado
        self.user = User.objects.create_user(username="sandro123", password="terrible")

    def test_guardar_pdf_ok(self):
        # Loguear usuario de prueba
        self.client.login(username="sandro123", password="terrible")
        archivo_path = os.path.join(BASE_DIR, "tests", "resources", "ACEPTACION.pdf")
        with open(archivo_path, "rb") as f:
            archivo = SimpleUploadedFile("test.pdf", f.read(), content_type="application/pdf")
        response = self.client.post(reverse("guardar_pdf"), {
            "numero_caso": "TEST123",
            "titulo": "Test",
            "fecha": "2025-07-04",
            "tipo_documento": "Prueba",
            "jurisdiccion": "Test",
            "archivo_pdf": archivo,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Archivo guardado correctamente", response.json()["mensaje"])


class ConsultarPDFViewTest(TestCase):
    def setUp(self):
        # Crear usuario y PDF de prueba
        self.user = User.objects.create_user(username="sandro123", password="terrible")
        self.client.login(username="sandro123", password="terrible")
        archivo_path = os.path.join(BASE_DIR, "tests", "resources", "ACEPTACION.pdf")
        with open(archivo_path, "rb") as f:
            archivo = SimpleUploadedFile("test.pdf", f.read(), content_type="application/pdf")
        response = self.client.post(reverse("guardar_pdf"), {
            "numero_caso": "TEST123",
            "titulo": "Test",
            "fecha": "2025-07-04",
            "tipo_documento": "Prueba",
            "jurisdiccion": "Test",
            "archivo_pdf": archivo,
        })
        self.assertEqual(response.status_code, 200)

    def test_consulta_de_que_trata(self):
        # Consulta: "De que trata el archivo"
        response = self.client.post(
            reverse("consultar_pdf"),
            data=json.dumps({"pdf_id": "TEST123", "question": "De que trata el archivo"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("answer", response.json())

    def test_consulta_quienes_intervienen(self):
        # Consulta: "Quienes son los que intervienen"
        response = self.client.post(
            reverse("consultar_pdf"),
            data=json.dumps({"pdf_id": "TEST123", "question": "Quienes son los que intervienen"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("answer", response.json())
