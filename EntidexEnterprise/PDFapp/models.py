from django.db import models


class PDFDocument(models.Model):
    numero_caso = models.CharField(max_length=100)
    titulo = models.CharField(max_length=255)
    fecha = models.DateField()
    tipo_documento = models.CharField(max_length=100)
    jurisdiccion = models.CharField(max_length=100)
    archivo_pdf = models.FileField(upload_to='archivos/')
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.titulo)

class PDFInteraccion(models.Model):
    pdf_document = models.ForeignKey(
        'PDFDocument', 
        on_delete=models.CASCADE, 
        related_name='interacciones'
    )
    prompt = models.TextField()
    respuesta = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interacción con: {self.pdf_document.titulo} - {self.creado_en.strftime('%Y-%m-%d %H:%M:%S')}"