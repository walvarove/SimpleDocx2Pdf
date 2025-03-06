#!/bin/sh
set -e

# This script is used by Koyeb to start the application

# Print environment for debugging
echo "Environment:"
env

# Print current directory
echo "Current directory: $(pwd)"
ls -la

# Try to find and run the application
if [ -f "./docx2pdf" ]; then
  echo "Found executable in current directory"
  exec ./docx2pdf
elif [ -f "/app/docx2pdf" ]; then
  echo "Found executable in /app directory"
  exec /app/docx2pdf
elif [ -f "/docx2pdf" ]; then
  echo "Found executable in root directory"
  exec /docx2pdf
elif [ -f "/usr/local/bin/docx2pdf" ]; then
  echo "Found executable in /usr/local/bin directory"
  exec /usr/local/bin/docx2pdf
else
  echo "ERROR: Could not find docx2pdf executable"
  # Try to build the application if source code is available
  if [ -d "./cmd/server" ]; then
    echo "Found source code, attempting to build"
    go build -o docx2pdf ./cmd/server
    if [ -f "./docx2pdf" ]; then
      echo "Successfully built executable"
      exec ./docx2pdf
    else
      echo "Failed to build executable"
    fi
  fi
  exit 1
fi 