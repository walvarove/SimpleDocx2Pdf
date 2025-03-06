# DOCX to PDF Converter API

A simple REST API service that converts DOCX files to PDF using LibreOffice.

## Features

- RESTful API for converting DOCX files to PDF
- Docker and Docker Compose support for easy deployment
- Configurable file size limits and temporary directory
- Clean-up of temporary files after conversion

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
- Content-Type: `multipart/form-data`
- Form field: `file` (DOCX file)

Response:
- The converted PDF file

## Configuration

The service can be configured using environment variables in the `docker-compose.yml` file:

- `PORT`: The port the server listens on (default: 8080)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 10MB)
- `TEMP_DIR`: Directory for temporary files (default: /tmp/docx2pdf)

## Development

### Prerequisites

- Go 1.21 or higher
- LibreOffice

### Building from Source

1. Install dependencies:
   ```
   go mod download
   ```

2. Build the application:
   ```
   go build -o docx2pdf ./cmd/server
   ```

3. Run the application:
   ```
   ./docx2pdf
   ```

## Example Usage

Using curl to convert a DOCX file:

```bash
curl -X POST -F "file=@/path/to/document.docx" \
     -o converted.pdf \
     http://localhost:8080/api/v1/convert
```

## License

MIT 