package converter

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// Converter defines the interface for document conversion
type Converter interface {
	ConvertDocxToPdf(docxPath string) (string, error)
}

// LibreOfficeConverter implements the Converter interface using LibreOffice
type LibreOfficeConverter struct {
	tempDir string
}

// NewLibreOfficeConverter creates a new LibreOfficeConverter instance
func NewLibreOfficeConverter(tempDir string) *LibreOfficeConverter {
	return &LibreOfficeConverter{
		tempDir: tempDir,
	}
}

// ConvertDocxToPdf converts a DOCX file to PDF using LibreOffice
func (c *LibreOfficeConverter) ConvertDocxToPdf(docxPath string) (string, error) {
	// Create a temporary output directory
	outputDir := filepath.Join(c.tempDir, filepath.Base(docxPath)+"_output")
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return "", fmt.Errorf("failed to create output directory: %w", err)
	}

	// Get the base filename without extension
	baseFilename := filepath.Base(docxPath)
	baseFilename = baseFilename[:len(baseFilename)-len(filepath.Ext(baseFilename))]

	// Expected output PDF path
	pdfPath := filepath.Join(outputDir, baseFilename+".pdf")

	// Run LibreOffice to convert the file
	cmd := exec.Command(
		"libreoffice",
		"--headless",
		"--convert-to", "pdf",
		"--outdir", outputDir,
		docxPath,
	)

	// Capture command output for debugging
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("conversion failed: %w, output: %s", err, string(output))
	}

	// Check if the PDF was created
	if _, err := os.Stat(pdfPath); os.IsNotExist(err) {
		return "", fmt.Errorf("PDF file was not created: %s", pdfPath)
	}

	return pdfPath, nil
}
