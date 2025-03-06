#!/bin/sh
set -e

# Print current directory and list files for debugging
echo "Current directory: $(pwd)"
ls -la

# Run the application
exec ./docx2pdf 