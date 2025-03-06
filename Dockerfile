FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install LibreOffice and required dependencies
RUN apk add --no-cache libreoffice libreoffice-writer msttcorefonts-installer fontconfig && \
    update-ms-fonts && \
    fc-cache -f

# Copy go.mod and go.sum files
COPY go.mod go.sum* ./

# Download and tidy dependencies
RUN go mod tidy

# Copy the source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -o /docx2pdf ./cmd/server

# Final stage
FROM alpine:3.18

WORKDIR /

# Install LibreOffice and required dependencies
RUN apk add --no-cache libreoffice libreoffice-writer msttcorefonts-installer fontconfig && \
    update-ms-fonts && \
    fc-cache -f

# Copy the binary from the builder stage
COPY --from=builder /docx2pdf /docx2pdf

# Create directory for temporary files
RUN mkdir -p /tmp/docx2pdf

# Expose the API port
EXPOSE 8080

# Run the application
CMD ["/docx2pdf"] 