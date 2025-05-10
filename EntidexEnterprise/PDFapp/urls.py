from django.urls import path
from . import views

urlpatterns = [
    path("pdfView/", views.pdfView, name="pdfView"),
    path("upload/", views.upload_pdf, name="upload_pdf"),
]
