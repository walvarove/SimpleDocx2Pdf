from flask import Flask, request, jsonify, send_file
import os
import uuid
import json
import pdfkit
import pypandoc
import zipfile
import tempfile
import shutil
from docxtpl import DocxTemplate
from htmldocx import HtmlToDocx
from docx import Document

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = '/tmp/docx2pdf'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
app.config['API_TOKEN'] = os.environ.get('API_TOKEN', 'Bkbxl2376APMv99y77HmGWk2teBODjXO')

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify(status='ok')

@app.route('/api/v1/convert', methods=['POST'])
def convert_docx_to_pdf():
    # Check API token
    api_token = request.headers.get('X-API-Token')
    if not api_token or api_token != app.config['API_TOKEN']:
        return jsonify(error='Invalid or missing API token'), 401
        
    if 'file' not in request.files:
        return jsonify(error='No file provided'), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify(error='No file selected'), 400

    if not file.filename.endswith('.docx'):
        return jsonify(error='Only .docx files are supported'), 400

    # Save the uploaded file
    unique_id = str(uuid.uuid4())
    docx_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}.docx')
    file.save(docx_path)

    # Convert DOCX to PDF
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}.pdf')
    try:
        # Using pypandoc for conversion
        pypandoc.convert_file(docx_path, 'pdf', outputfile=pdf_path)
        
        # Create a ZIP file containing both DOCX and PDF
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add the original DOCX file with the original filename
            zipf.write(docx_path, os.path.basename(file.filename))
            # Add the PDF file with the original filename but .pdf extension
            pdf_filename = os.path.splitext(file.filename)[0] + '.pdf'
            zipf.write(pdf_path, pdf_filename)
        
        # Send the ZIP file back to the client
        return send_file(zip_path, as_attachment=True, download_name=f'{os.path.splitext(file.filename)[0]}.zip')
    
    except Exception as e:
        return jsonify(error=f'Conversion failed: {str(e)}'), 500
    finally:
        # Clean up temporary files
        for file_path in [docx_path, pdf_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

@app.route('/api/v1/template', methods=['POST'])
def process_template_to_pdf():
    # Check API token
    api_token = request.headers.get('X-API-Token')
    if not api_token or api_token != app.config['API_TOKEN']:
        return jsonify(error='Invalid or missing API token'), 401
    
    # Check if the request has the required parts
    if 'template' not in request.files:
        return jsonify(error='No template file provided'), 400
    
    # Get the template file
    template_file = request.files['template']
    if template_file.filename == '' or not template_file.filename.endswith('.docx'):
        return jsonify(error='Invalid template file. Must be a .docx file'), 400
    
    # Get the data and htmlData from the request
    data = {}
    html_data = {}
    
    if 'data' in request.form:
        try:
            data = json.loads(request.form['data'])
        except json.JSONDecodeError:
            return jsonify(error='Invalid JSON in data field'), 400
    
    if 'htmlData' in request.form:
        try:
            html_data = json.loads(request.form['htmlData'])
        except json.JSONDecodeError:
            return jsonify(error='Invalid JSON in htmlData field'), 400
    
    # Get the output filename (optional)
    output_filename = request.form.get('filename', os.path.splitext(template_file.filename)[0])
    if not output_filename.endswith('.docx'):
        output_filename = output_filename + '.docx'
    
    # Create unique IDs for the files
    unique_id = str(uuid.uuid4())
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_template.docx')
    output_docx_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_output.docx')
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_output.pdf')
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_output.zip')
    
    # Save the template file
    template_file.save(template_path)
    
    try:
        # Process the template with docxtpl
        doc = DocxTemplate(template_path)
        
        # Process HTML content and add it to the context
        html_converter = HtmlToDocx()
        for key, html_content in html_data.items():
            # Create a temporary document for the HTML content
            temp_doc = Document()
            html_converter.add_html_to_document(html_content, temp_doc)
            # Add the HTML document to the data context
            data[key] = temp_doc
        
        # Render the template with the data
        doc.render(data)
        doc.save(output_docx_path)
        
        # Convert the processed DOCX to PDF
        pypandoc.convert_file(output_docx_path, 'pdf', outputfile=pdf_path)
        
        # Create a ZIP file containing both DOCX and PDF
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add the processed DOCX file with the provided filename
            zipf.write(output_docx_path, output_filename)
            # Add the PDF file with the provided filename but .pdf extension
            pdf_filename = os.path.splitext(output_filename)[0] + '.pdf'
            zipf.write(pdf_path, pdf_filename)
        
        # Send the ZIP file back to the client
        return send_file(zip_path, as_attachment=True, download_name=f'{os.path.splitext(output_filename)[0]}.zip')
    
    except Exception as e:
        return jsonify(error=f'Template processing failed: {str(e)}'), 500
    finally:
        # Clean up temporary files
        for file_path in [template_path, output_docx_path, pdf_path, zip_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 