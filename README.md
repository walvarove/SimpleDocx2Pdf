# DOCX to PDF Converter API

A simple REST API service that converts DOCX files to PDF using LibreOffice.

## Features

- RESTful API for converting DOCX files to PDF
- Docker and Docker Compose support for easy deployment
- Configurable file size limits and temporary directory
- Clean-up of temporary files after conversion
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
- Content-Type: `multipart/form-data`
- Form field: `file` (DOCX file)

Response:
- The converted PDF file

## Configuration

The service can be configured using environment variables in the `docker-compose.yml` file:

- `PORT`: The port the server listens on (default: 8080)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 10MB)
- `TEMP_DIR`: Directory for temporary files (default: /tmp/docx2pdf)

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

- Go 1.21 or higher
- LibreOffice

### Building from Source

1. Install dependencies:
   ```
   go mod tidy
   ```

2. Build the application:
   ```
   go build -o bin/docx2pdf ./cmd/server
   ```

3. Run the application:
   ```
   ./bin/docx2pdf
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