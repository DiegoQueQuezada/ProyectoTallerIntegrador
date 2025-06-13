# import os
# import uuid
# from datetime import datetime
# import pyodbc
# from flask import Flask, request, redirect, url_for, render_template

# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'uploads'

# # ==============================================
# # FUNCIONES DE CONEXIÓN A LA BASE DE DATOS
# # ==============================================

# def conectar_sqlserver():
#     try:
#         # Cadena de conexión para autenticación de Windows
#         server = 'DESKTOP-HMENEI9\SQLSERVER'
#         database = 'TallerIntegrador'
#         conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
        
#         conn = pyodbc.connect(conn_str)
#         print("Conexión exitosa a SQL Server")
#         return conn
#     except Exception as e:
#         print(f"Error al conectar a SQL Server: {e}")
#         return None

# def crear_tabla_documentos():
#     conn = conectar_sqlserver()
#     if conn:
#         try:
#             cursor = conn.cursor()
#             cursor.execute("""
#             IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Documentos' AND xtype='U')
#             CREATE TABLE Documentos (
#                 Id INT IDENTITY(1,1) PRIMARY KEY,
#                 NumeroCaso NVARCHAR(50) NOT NULL,
#                 Titulo NVARCHAR(100) NOT NULL,
#                 Fecha DATE NOT NULL,
#                 TipoDocumento NVARCHAR(50) NOT NULL,
#                 TipoDocumentoOtro NVARCHAR(50) NULL,
#                 Jurisdiccion NVARCHAR(50) NOT NULL,
#                 NombreArchivo NVARCHAR(255) NOT NULL,
#                 RutaArchivo NVARCHAR(255) NOT NULL,
#                 FechaRegistro DATETIME DEFAULT GETDATE()
#             )
#             """)
#             conn.commit()
#             print("Tabla 'Documentos' creada o ya existente")
#         except Exception as e:
#             print(f"Error al crear tabla: {e}")
#         finally:
#             conn.close()

# # ==============================================
# # FUNCIONES DE MANEJO DE DATOS
# # ==============================================

# def guardar_documento(datos, archivo):
#     conn = conectar_sqlserver()
#     if conn:
#         try:
#             # Generar nombre único para el archivo
#             nombre_original = archivo.filename
#             extension = os.path.splitext(nombre_original)[1]
#             nombre_unico = f"{uuid.uuid4()}{extension}"
#             ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_unico)
            
#             # Guardar archivo físicamente
#             os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
#             archivo.save(ruta_guardado)
            
#             # Determinar el tipo de documento final
#             tipo_documento_final = datos['tipoDocumento']
#             if datos['tipoDocumento'] == 'otro' and datos.get('otherDocument'):
#                 tipo_documento_final = datos['otherDocument']
            
#             cursor = conn.cursor()
#             cursor.execute("""
#             INSERT INTO Documentos (
#                 NumeroCaso, Titulo, Fecha, TipoDocumento, TipoDocumentoOtro, 
#                 Jurisdiccion, NombreArchivo, RutaArchivo
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#             """, 
#             (
#                 datos['numeroCaso'],
#                 datos['titulo'],
#                 datetime.strptime(datos['fecha'], '%Y-%m-%d').date(),
#                 tipo_documento_final,
#                 datos.get('otherDocument', None),
#                 datos['jurisdiccion'],
#                 nombre_original,
#                 ruta_guardado
#             ))
#             conn.commit()
#             return True
#         except Exception as e:
#             print(f"Error al guardar documento: {e}")
#             # Eliminar archivo si hubo error en la base de datos
#             if os.path.exists(ruta_guardado):
#                 os.remove(ruta_guardado)
#             return False
#         finally:
#             conn.close()
#     return False

# # ==============================================
# # RUTAS DE LA APLICACIÓN FLASK
# # ==============================================

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/guardar-pdf', methods=['POST'])
# def guardar_pdf():
#     if request.method == 'POST':
#         # Obtener datos del formulario
#         datos = {
#             'numeroCaso': request.form.get('Numerodecaso'),
#             'titulo': request.form.get('titulo'),
#             'fecha': request.form.get('fecha'),
#             'tipoDocumento': request.form.get('tipoDocumento'),
#             'otherDocument': request.form.get('otherDocument'),
#             'jurisdiccion': request.form.get('jurisdiccion')
#         }
        
#         # Obtener archivo
#         archivo = request.files.get('pdfFile')
        
#         if archivo and archivo.filename != '':
#             if guardar_documento(datos, archivo):
#                 return redirect(url_for('exito'))
#             else:
#                 return "Error al guardar el documento", 500
#         else:
#             return "No se proporcionó archivo PDF", 400

# @app.route('/exito')
# def exito():
#     return "Documento guardado exitosamente"

# # ==============================================
# # INICIALIZACIÓN DE LA APLICACIÓN
# # ==============================================

# if __name__ == '__main__':
#     # Crear la tabla al iniciar (solo una vez)
#     crear_tabla_documentos()
    
#     # Asegurarse que la carpeta de uploads existe
#     os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
#     app.run(debug=True)