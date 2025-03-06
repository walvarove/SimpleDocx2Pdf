package main

import (
	"fmt"
	"log"
	"os"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/walvarove/docx2pdf/api/handlers"
	"github.com/walvarove/docx2pdf/internal/converter"
)

func main() {
	// Set up environment variables with defaults
	port := getEnvWithDefault("PORT", "8080")
	tempDir := getEnvWithDefault("TEMP_DIR", "/tmp/docx2pdf")
	maxFileSizeStr := getEnvWithDefault("MAX_FILE_SIZE", "10485760") // 10MB default

	maxFileSize, err := strconv.ParseInt(maxFileSizeStr, 10, 64)
	if err != nil {
		log.Fatalf("Invalid MAX_FILE_SIZE: %v", err)
	}

	// Ensure temp directory exists
	if err := os.MkdirAll(tempDir, 0755); err != nil {
		log.Fatalf("Failed to create temp directory: %v", err)
	}

	// Initialize converter service
	converterService := converter.NewLibreOfficeConverter(tempDir)

	// Initialize router
	router := gin.Default()
	router.SetTrustedProxies(nil)

	// Set maximum multipart form memory
	router.MaxMultipartMemory = maxFileSize

	// Register routes
	handlers.RegisterRoutes(router, converterService, maxFileSize)

	// Start server
	log.Printf("Starting server on port %s", port)
	if err := router.Run(fmt.Sprintf(":%s", port)); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

func getEnvWithDefault(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}
