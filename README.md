# DOCX to PDF Converter API

A simple REST API service that converts DOCX files to PDF using Python and LibreOffice. It also supports template processing with data and HTML content.

## Features

- RESTful API for converting DOCX files to PDF
- Template processing with data and HTML content
- Returns both DOCX and PDF files in a ZIP archive
- Docker and Docker Compose support for easy deployment
- Configurable file size limits and temporary directory
- Clean-up of temporary files after conversion
- API token authentication
- Ready for deployment to Koyeb

## Requirements

- Docker and Docker Compose

## Quick Start

1. Clone this repository:
   ```
   git clone https://github.com/walvarove/docx2pdf.git
   cd docx2pdf
   ```

2. Start the service using Docker Compose:
   ```
   docker-compose up -d
   ```

3. The API will be available at `http://localhost:8080`

## API Endpoints

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "ok"
}
```

### Convert DOCX to PDF

```
POST /api/v1/convert
```

Request:
- Header: `X-API-Token: Bkbxl2376APMv99y77HmGWk2teBODjXO`
- Content-Type: `multipart/form-data`
- Form field: `file` (DOCX file)

Response:
- A ZIP file containing both the original DOCX file and the converted PDF file

### Process Template with Data and HTML

```
POST /api/v1/template
```

Request:
- Header: `X-API-Token: Bkbxl2376APMv99y77HmGWk2teBODjXO`
- Content-Type: `multipart/form-data`
- Form fields:
  - `template` (DOCX template file)
  - `data` (JSON string with template variables)
  - `htmlData` (JSON string with HTML content to be inserted)
  - `filename` (Optional: custom filename for the output files)

Example data:
```json
{
  "name": "John Doe",
  "company": "ACME Inc.",
  "date": "2023-01-01"
}
```

Example htmlData:
```json
{
  "content": "<h1>Hello World</h1><p>This is <b>HTML</b> content</p>",
  "signature": "<p>Sincerely,</p><p><i>John Doe</i></p>"
}
```

Response:
- A ZIP file containing both the processed DOCX file and the converted PDF file

## Configuration

The service can be configured using environment variables in the `docker-compose.yml` file:

- `PORT`: The port the server listens on (default: 8080)
- `MAX_CONTENT_LENGTH`: Maximum file size in bytes (default: 10MB)
- `API_TOKEN`: Authentication token for API requests (default: Bkbxl2376APMv99y77HmGWk2teBODjXO)

## Deployment

### Deploying to Koyeb

1. Create a Koyeb account at [koyeb.com](https://koyeb.com)

2. Install the Koyeb CLI:
   ```
   curl -fsSL https://cli.koyeb.com/install.sh | sh
   ```

3. Login to Koyeb:
   ```
   koyeb login
   ```

4. Deploy the application using the koyeb.yaml configuration:
   ```
   koyeb app create --name docx2pdf --file koyeb.yaml
   ```

5. Or deploy directly from GitHub:
   ```
   koyeb app init docx2pdf --git github.com/walvarove/docx2pdf --git-branch main --buildpack heroku/buildpacks:20
   ```

## Development

### Prerequisites

- Python 3.11 or higher
- LibreOffice
- Pandoc

### Building from Source

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python app.py
   ```

## Example Usage

### Converting a DOCX file to PDF

```bash
curl -X POST \
     -H "X-API-Token: Bkbxl2376APMv99y77HmGWk2teBODjXO" \
     -F "file=@/path/to/document.docx" \
     -o document.zip \
     http://localhost:8080/api/v1/convert
```

### Processing a template with data and HTML

```bash
curl -X POST \
     -H "X-API-Token: Bkbxl2376APMv99y77HmGWk2teBODjXO" \
     -F "template=@/path/to/template.docx" \
     -F 'data={"name":"John Doe","company":"ACME Inc."}' \
     -F 'htmlData={"content":"<h1>Hello World</h1><p>This is <b>HTML</b> content</p>"}' \
     -F "filename=processed_document.docx" \
     -o processed_document.zip \
     http://localhost:8080/api/v1/template
```

## License

MIT 