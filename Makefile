.PHONY: build run docker-build docker-run clean test

# Build the application
build:
	go build -o docx2pdf ./cmd/server

# Run the application
run: build
	./docx2pdf

# Build the Docker image
docker-build:
	docker build -t docx2pdf .

# Run the Docker container
docker-run: docker-build
	docker run -p 8080:8080 docx2pdf

# Run with Docker Compose
docker-compose-up:
	docker-compose up -d

# Stop Docker Compose
docker-compose-down:
	docker-compose down

# Clean build artifacts
clean:
	rm -f docx2pdf
	rm -rf tmp/

# Run tests
test:
	go test -v ./...

# Download dependencies
deps:
	go mod download

# Initialize the project
init: deps build 