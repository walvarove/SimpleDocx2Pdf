package handlers

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockConverter is a mock implementation of the converter.Converter interface
type MockConverter struct {
	mock.Mock
}

func (m *MockConverter) ConvertDocxToPdf(docxPath string) (string, error) {
	args := m.Called(docxPath)
	return args.String(0), args.Error(1)
}

func TestHealthCheck(t *testing.T) {
	// Set Gin to test mode
	gin.SetMode(gin.TestMode)

	// Create a test router
	router := gin.Default()
	router.GET("/health", healthCheck)

	// Create a test request
	req, _ := http.NewRequest("GET", "/health", nil)
	resp := httptest.NewRecorder()

	// Serve the request
	router.ServeHTTP(resp, req)

	// Assert the response
	assert.Equal(t, http.StatusOK, resp.Code)
	assert.Contains(t, resp.Body.String(), "ok")
}

// Note: Testing the convert handler would require more complex setup
// including multipart form data and mocking the file system operations.
// This is left as an exercise for a more comprehensive test suite.
