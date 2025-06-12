from os import confstr
import pydoc
from flask import app, jsonify


@app.route('/listar-pdfs', methods=['GET'])
def listar_pdfs():
    print("SAFJHSAKJFSKJFHJSHFJHSLFKs")
    try:
        conn = pydoc.connect(confstr)
        cursor = conn.cursor()
        cursor.execute("SELECT titulo, fecha, pdf_path FROM PDFapp_pdfdocument")
        rows = cursor.fetchall()
        conn.close()

        documentos = []
        for row in rows:
            documentos.append({
                "titulo": row[0],
                "fecha": row[1].strftime("%Y-%m-%d"),
                "pdf_path": row[2]
            })
        print("documentos")
        print(documentos)
        return jsonify(documentos)
    except Exception as e:
        print("e")
        print(e)
        return jsonify({"mensaje": f"Error: {str(e)}"}), 500
