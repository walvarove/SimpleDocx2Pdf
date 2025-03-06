package handlers

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/walvarove/docx2pdf/internal/converter"
)

// RegisterRoutes sets up the API routes
func RegisterRoutes(router *gin.Engine, converter converter.Converter, maxFileSize int64) {
	// Health check endpoint
	router.GET("/health", healthCheck)

	// API endpoints
	api := router.Group("/api/v1")
	{
		api.POST("/convert", createConvertHandler(converter, maxFileSize))
	}
}

// healthCheck handles the health check endpoint
func healthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "ok",
	})
}

// createConvertHandler creates a handler for the convert endpoint
func createConvertHandler(converter converter.Converter, maxFileSize int64) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Get the file from the request
		file, err := c.FormFile("file")
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "No file provided or invalid file",
			})
			return
		}

		// Check file size
		if file.Size > maxFileSize {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": fmt.Sprintf("File too large. Maximum size is %d bytes", maxFileSize),
			})
			return
		}

		// Check file extension
		if filepath.Ext(file.Filename) != ".docx" {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "Only .docx files are supported",
			})
			return
		}

		// Create a unique filename for the uploaded file
		tempDir := os.Getenv("TEMP_DIR")
		if tempDir == "" {
			tempDir = "/tmp/docx2pdf"
		}

		// Ensure temp directory exists
		if err := os.MkdirAll(tempDir, 0755); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to create temporary directory",
			})
			return
		}

		// Generate a unique ID for this conversion
		conversionID := uuid.New().String()

		// Create paths for the input and output files
		docxPath := filepath.Join(tempDir, conversionID+".docx")

		// Save the uploaded file
		if err := c.SaveUploadedFile(file, docxPath); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to save uploaded file",
			})
			return
		}

		// Convert the file
		pdfPath, err := converter.ConvertDocxToPdf(docxPath)
		if err != nil {
			// Clean up the uploaded file
			os.Remove(docxPath)

			c.JSON(http.StatusInternalServerError, gin.H{
				"error": fmt.Sprintf("Conversion failed: %v", err),
			})
			return
		}

		// Serve the PDF file
		c.FileAttachment(pdfPath, filepath.Base(file.Filename)+".pdf")

		// Clean up files in a separate goroutine
		go func() {
			defer os.Remove(docxPath)
			defer os.Remove(pdfPath)
			defer os.RemoveAll(filepath.Dir(pdfPath))
		}()
	}
}
