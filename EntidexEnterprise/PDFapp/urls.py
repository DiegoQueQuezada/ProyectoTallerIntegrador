from django.urls import path
from . import views

urlpatterns = [
    path("guardar-pdf/", views.guardar_pdf, name="guardar_pdf"),
    path("archivos/", views.archivosView, name="archivos"),
    path("pdfView/", views.pdfView, name="pdfView"),
    path("pdfapp/upload/", views.upload_pdf, name="pdfViewUpload"),
]
