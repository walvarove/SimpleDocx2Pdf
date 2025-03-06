from flask import Flask, request, jsonify, send_file
import os
import uuid
import json
import pdfkit
import zipfile
import tempfile
import shutil
import traceback
import logging
import subprocess
import re
from io import StringIO, BytesIO
from docxtpl import DocxTemplate, RichText
from htmldocx import HtmlToDocx
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn
from docx.enum.style import WD_STYLE_TYPE
import html
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = '/tmp/docx2pdf'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
app.config['API_TOKEN'] = os.environ.get('API_TOKEN', 'Bkbxl2376APMv99y77HmGWk2teBODjXO')

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to convert DOCX to PDF using various methods
def convert_to_pdf(input_path, output_path):
    """
    Try multiple methods to convert DOCX to PDF
    """
    methods_tried = []

    try:
        logger.info("Attempting conversion with LibreOffice")
        methods_tried.append("libreoffice")
        cmd = [
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', os.path.dirname(output_path),
            input_path
        ]
        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode == 0:
            base_name = os.path.basename(input_path)
            base_name_without_ext = os.path.splitext(base_name)[0]
            libreoffice_output = os.path.join(os.path.dirname(output_path), f"{base_name_without_ext}.pdf")

            if libreoffice_output != output_path:
                shutil.move(libreoffice_output, output_path)

            logger.info("Conversion with LibreOffice successful")
            return True
        else:
            logger.warning(f"LibreOffice conversion failed: {process.stderr}")
    except Exception as e:
        logger.warning(f"LibreOffice conversion failed: {str(e)}")

    try:
        logger.info("Attempting conversion with unoconv")
        methods_tried.append("unoconv")
        cmd = [
            'unoconv',
            '-f', 'pdf',
            '-o', output_path,
            input_path
        ]
        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode == 0:
            logger.info("Conversion with unoconv successful")
            return True
        else:
            logger.warning(f"Unoconv conversion failed: {process.stderr}")
    except Exception as e:
        logger.warning(f"Unoconv conversion failed: {str(e)}")

    raise Exception(f"All conversion methods failed. Methods tried: {', '.join(methods_tried)}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify(status='ok')

@app.route('/api/v1/template', methods=['POST'])
def process_template_to_pdf():
    template_path = None
    output_docx_path = None
    pdf_path = None
    zip_path = None
    temp_files = []

    try:
        logger.info(f"Received template request with headers: {dict(request.headers)}")
        logger.info(f"Request form data keys: {list(request.form.keys())}")
        logger.info(f"Request files keys: {list(request.files.keys())}")

        api_token = request.headers.get('X-API-Token')
        if not api_token or api_token != app.config['API_TOKEN']:
            logger.warning(f"Invalid API token: {api_token}")
            return jsonify(error='Invalid or missing API token'), 401

        if 'template' not in request.files:
            logger.warning("No template file provided in request")
            return jsonify(error='No template file provided'), 400

        template_file = request.files['template']
        if template_file.filename == '' or not template_file.filename.endswith('.docx'):
            logger.warning(f"Invalid template file: {template_file.filename}")
            return jsonify(error='Invalid template file. Must be a .docx file'), 400

        data = {}
        html_data = {}

        if 'data' in request.form:
            try:
                data_str = request.form['data']
                logger.info(f"Raw data string: {data_str}")
                data = json.loads(data_str)
                logger.info(f"Parsed data keys: {list(data.keys())}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in data field: {str(e)}")
                return jsonify(error=f'Invalid JSON in data field: {str(e)}'), 400

        unique_id = str(uuid.uuid4())
        template_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_template.docx')
        output_docx_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_output.docx')
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_output.pdf')
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_output.zip')

        # Save the template file
        template_file.save(template_path)
        logger.info(f"Saved template file to {template_path}")

        # Initialize the DocxTemplate with the template file
        doc = DocxTemplate(template_path)

        # Process HTML content if provided
        if 'htmlData' in request.form:
            try:
                html_data_str = request.form['htmlData']
                logger.info(f"Raw htmlData string: {html_data_str}")
                html_data = json.loads(html_data_str)
                logger.info(f"Parsed htmlData keys: {list(html_data.keys())}")

                # Process each HTML content
                for key, value in html_data.items():
                    logger.info(f"Processing HTML for key: {key}")
                    
                    # Parse HTML content
                    soup = BeautifulSoup(value, 'html.parser')
                    
                    # Process list items
                    if soup.find('ul'):
                        # Create a new document for the list content
                        list_doc = Document()
                        
                        for li in soup.find_all('li'):
                            # Create a paragraph for each list item
                            p = list_doc.add_paragraph()
                            
                            # Add bullet point
                            p.add_run('• ')
                            
                            # Process the content of the list item
                            for element in li.contents:
                                if isinstance(element, str):
                                    text = element.strip()
                                    if text:
                                        p.add_run(text)
                                else:
                                    if element.name == 'b':
                                        run = p.add_run(element.get_text().strip())
                                        run.bold = True
                                        if element.find('u'):
                                            run.underline = True
                                    elif element.name == 'u':
                                        run = p.add_run(element.get_text().strip())
                                        run.underline = True
                                        if element.find('b'):
                                            run.bold = True
                                    elif element.name == 'i':
                                        run = p.add_run(element.get_text().strip())
                                        run.italic = True
                            # Add a line break after each list item
                            p.add_run('\n')
                        
                        # Save the list document to a temporary file
                        temp_list_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_{key}_list.docx')
                        list_doc.save(temp_list_path)
                        temp_files.append(temp_list_path)
                        
                        # Create a subdocument from the temporary file
                        subdoc = doc.new_subdoc(temp_list_path)
                        data[key] = subdoc
                    
                    if soup.find('p'):
                        rt = RichText()
                        for p in soup.find_all('p'):
                            rt.add(p.get_text().strip())
                        data[key] = rt
                    
                    logger.info(f"Added formatted content for key: {key}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in htmlData field: {str(e)}")
                return jsonify(error=f'Invalid JSON in htmlData field: {str(e)}'), 400
            except Exception as e:
                logger.error(f"Error processing HTML content: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify(error=f"Error processing HTML content: {str(e)}"), 500

        output_filename = request.form.get('filename', os.path.splitext(template_file.filename)[0])
        if not output_filename.endswith('.docx'):
            output_filename = output_filename + '.docx'
        logger.info(f"Using output filename: {output_filename}")

        # Render the template with the context
        logger.info(f"Rendering template with context keys: {list(data.keys())}")
        doc.render(data)
        doc.save(output_docx_path)
        logger.info(f"Rendered template and saved to {output_docx_path}")

        # Convert the processed DOCX to PDF
        try:
            logger.info(f"Converting {output_docx_path} to PDF")
            convert_to_pdf(output_docx_path, pdf_path)
            logger.info(f"Conversion successful, PDF saved to {pdf_path}")
        except Exception as conversion_error:
            logger.error(f"PDF conversion error: {str(conversion_error)}")
            return jsonify(error=f"PDF conversion failed: {str(conversion_error)}"), 500
        
        try:
            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                zipf.write(output_docx_path, output_filename)
                pdf_filename = os.path.splitext(output_filename)[0] + '.pdf'
                zipf.write(pdf_path, pdf_filename)
            logger.info(f"Created ZIP file at {zip_path} with maximum compression")
        except Exception as zip_error:
            logger.error(f"Error creating ZIP file: {str(zip_error)}")
            return jsonify(error=f"Failed to create ZIP file: {str(zip_error)}"), 500
        
        # Send the ZIP file back to the client
        return send_file(zip_path, as_attachment=True, download_name=f'{os.path.splitext(output_filename)[0]}.zip')
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify(error=f"An unexpected error occurred: {str(e)}"), 500
    finally:
        # Clean up temporary files
        try:
            for file_path in [p for p in [template_path, output_docx_path, pdf_path, zip_path] + temp_files if p is not None]:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {str(cleanup_error)}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port) 