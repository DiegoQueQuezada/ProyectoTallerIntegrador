from flask import Flask, render_template, request, jsonify
import pyodbc
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Conexión a SQL Server con autenticación de Windows
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-HMENEI9\\SQLSERVER;"
    "DATABASE=TallerIntegrador;"
    "Trusted_Connection=yes;"
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registrar-pdf', methods=['POST'])
def registrar_pdf():
    try:
        numero_caso = request.form.get('numeroCaso')
        titulo = request.form.get('titulo')
        fecha = request.form.get('fecha')
        tipo_documento = request.form.get('tipoDocumento')
        jurisdiccion = request.form.get('jurisdiccion')
        pdf = request.files.get('pdfFile')

        if not all([numero_caso, titulo, fecha, tipo_documento, jurisdiccion, pdf]):
            return jsonify({"mensaje": "Faltan campos"}), 400

        # Guardar archivo PDF en el servidor
        filename = secure_filename(pdf.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pdf.save(file_path)

        # Guardar en la base de datos
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Documentos (numero_caso, titulo, fecha, tipo_documento, jurisdiccion, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (numero_caso, titulo, fecha, tipo_documento, jurisdiccion, file_path))
        conn.commit()
        conn.close()

        return jsonify({"mensaje": "Documento registrado correctamente."})
    except Exception as e:
        return jsonify({"mensaje": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
