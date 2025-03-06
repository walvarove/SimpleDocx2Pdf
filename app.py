from flask import Flask, request, jsonify, send_file
import os
import uuid
import json
import pdfkit
import pypandoc
import zipfile
import tempfile
import shutil
import traceback
import logging
from docxtpl import DocxTemplate
from htmldocx import HtmlToDocx
from docx import Document

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

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify(status='ok')

@app.route('/api/v1/convert', methods=['POST'])
def convert_docx_to_pdf():
    # Initialize file paths to None for cleanup in finally block
    docx_path = None
    pdf_path = None
    zip_path = None
    
    try:
        # Check API token
        api_token = request.headers.get('X-API-Token')
        if not api_token or api_token != app.config['API_TOKEN']:
            logger.warning(f"Invalid API token: {api_token}")
            return jsonify(error='Invalid or missing API token'), 401
            
        if 'file' not in request.files:
            logger.warning("No file provided in request")
            return jsonify(error='No file provided'), 400

        file = request.files['file']

        if file.filename == '':
            logger.warning("Empty filename provided")
            return jsonify(error='No file selected'), 400

        if not file.filename.endswith('.docx'):
            logger.warning(f"Invalid file extension: {file.filename}")
            return jsonify(error='Only .docx files are supported'), 400

        # Save the uploaded file
        unique_id = str(uuid.uuid4())
        docx_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}.docx')
        file.save(docx_path)
        logger.info(f"Saved uploaded file to {docx_path}")

        # Convert DOCX to PDF
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}.pdf')
        
        # Using pypandoc for conversion
        logger.info(f"Converting {docx_path} to PDF")
        pypandoc.convert_file(docx_path, 'pdf', outputfile=pdf_path)
        logger.info(f"Conversion successful, PDF saved to {pdf_path}")
        
        # Create a ZIP file containing both DOCX and PDF with maximum compression
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}.zip')
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            # Add the original DOCX file with the original filename
            zipf.write(docx_path, os.path.basename(file.filename))
            # Add the PDF file with the original filename but .pdf extension
            pdf_filename = os.path.splitext(file.filename)[0] + '.pdf'
            zipf.write(pdf_path, pdf_filename)
        logger.info(f"Created ZIP file at {zip_path} with maximum compression")
        
        # Send the ZIP file back to the client
        return send_file(zip_path, as_attachment=True, download_name=f'{os.path.splitext(file.filename)[0]}.zip')
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify(error=f"An unexpected error occurred: {str(e)}"), 500
    finally:
        # Clean up temporary files
        try:
            for file_path in [p for p in [docx_path, pdf_path, zip_path] if p is not None]:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {str(cleanup_error)}")

@app.route('/api/v1/template', methods=['POST'])
def process_template_to_pdf():
    # Initialize file paths to None for cleanup in finally block
    template_path = None
    output_docx_path = None
    pdf_path = None
    zip_path = None
    
    try:
        # Log request details for debugging
        logger.info(f"Received template request with headers: {dict(request.headers)}")
        logger.info(f"Request form data keys: {list(request.form.keys())}")
        logger.info(f"Request files keys: {list(request.files.keys())}")
        
        # Check API token
        api_token = request.headers.get('X-API-Token')
        if not api_token or api_token != app.config['API_TOKEN']:
            logger.warning(f"Invalid API token: {api_token}")
            return jsonify(error='Invalid or missing API token'), 401
        
        # Check if the request has the required parts
        if 'template' not in request.files:
            logger.warning("No template file provided in request")
            return jsonify(error='No template file provided'), 400
        
        # Get the template file
        template_file = request.files['template']
        if template_file.filename == '' or not template_file.filename.endswith('.docx'):
            logger.warning(f"Invalid template file: {template_file.filename}")
            return jsonify(error='Invalid template file. Must be a .docx file'), 400
        
        # Get the data and htmlData from the request
        data = {}
        html_data = {}
        
        if 'data' in request.form:
            try:
                data_str = request.form['data']
                logger.info(f"Raw data string: {data_str[:100]}...")  # Log first 100 chars
                data = json.loads(data_str)
                logger.info(f"Parsed data: {data.keys()}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in data field: {str(e)}")
                logger.error(f"Invalid JSON data: {request.form['data'][:100]}...")  # Log first 100 chars
                return jsonify(error=f'Invalid JSON in data field: {str(e)}'), 400
        else:
            logger.warning("No data field provided in request")
        
        if 'htmlData' in request.form:
            try:
                html_data_str = request.form['htmlData']
                logger.info(f"Raw htmlData string: {html_data_str[:100]}...")  # Log first 100 chars
                html_data = json.loads(html_data_str)
                logger.info(f"Parsed htmlData: {html_data.keys()}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in htmlData field: {str(e)}")
                logger.error(f"Invalid JSON htmlData: {request.form['htmlData'][:100]}...")  # Log first 100 chars
                return jsonify(error=f'Invalid JSON in htmlData field: {str(e)}'), 400
        else:
            logger.warning("No htmlData field provided in request")
        
        # Get the output filename (optional)
        output_filename = request.form.get('filename', os.path.splitext(template_file.filename)[0])
        if not output_filename.endswith('.docx'):
            output_filename = output_filename + '.docx'
        logger.info(f"Using output filename: {output_filename}")
        
        # Create unique IDs for the files
        unique_id = str(uuid.uuid4())
        template_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_template.docx')
        output_docx_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_output.docx')
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_output.pdf')
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_output.zip')
        
        # Save the template file
        template_file.save(template_path)
        logger.info(f"Saved template file to {template_path}")
        
        # Process the template with docxtpl
        logger.info("Processing template with docxtpl")
        doc = DocxTemplate(template_path)
        
        # Process HTML content and add it to the context
        html_converter = HtmlToDocx()
        for key, html_content in html_data.items():
            try:
                # Create a temporary document for the HTML content
                temp_doc = Document()
                html_converter.add_html_to_document(html_content, temp_doc)
                # Add the HTML document to the data context
                data[key] = temp_doc
                logger.info(f"Processed HTML content for key: {key}")
            except Exception as html_error:
                logger.error(f"Error processing HTML for key {key}: {str(html_error)}")
                return jsonify(error=f"Error processing HTML content for '{key}': {str(html_error)}"), 500
        
        # Render the template with the data
        try:
            doc.render(data)
            doc.save(output_docx_path)
            logger.info(f"Template rendered and saved to {output_docx_path}")
        except Exception as render_error:
            logger.error(f"Template rendering error: {str(render_error)}")
            return jsonify(error=f"Template rendering failed: {str(render_error)}"), 500
        
        # Convert the processed DOCX to PDF
        try:
            logger.info(f"Converting {output_docx_path} to PDF")
            pypandoc.convert_file(output_docx_path, 'pdf', outputfile=pdf_path)
            logger.info(f"Conversion successful, PDF saved to {pdf_path}")
        except Exception as pandoc_error:
            logger.error(f"PDF conversion error: {str(pandoc_error)}")
            return jsonify(error=f"PDF conversion failed: {str(pandoc_error)}"), 500
        
        # Create a ZIP file containing both DOCX and PDF with maximum compression
        try:
            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                # Add the processed DOCX file with the provided filename
                zipf.write(output_docx_path, output_filename)
                # Add the PDF file with the provided filename but .pdf extension
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
            for file_path in [p for p in [template_path, output_docx_path, pdf_path, zip_path] if p is not None]:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {str(cleanup_error)}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port) 