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
