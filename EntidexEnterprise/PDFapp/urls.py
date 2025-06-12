from django.urls import path
from . import views

urlpatterns = [
    path('', views.indexView, name='index'),
    path("guardar-pdf/", views.guardar_pdf, name="guardar_pdf"),
    path("archivos/", views.archivosView, name="archivos"),
    path('listar-pdfs/', views.listar_pdfs, name='listar_pdfs'),
    path('eliminar-pdf/', views.eliminar_pdf, name='eliminar_pdf'),
    path("pdfView/", views.pdfView, name="pdfView"),
    path("pdfapp/upload/", views.upload_pdf, name="upload2_pdf"),
    path("listar_pdfs/", views.listar_pdfs, name="upload_pdf"),
    path('consultar-pdf/', views.consultar_pdf, name='consultar_pdf'),
]


