FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libreoffice \
    fonts-liberation \
    wkhtmltopdf \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and install the latest Pandoc version
RUN PANDOC_VERSION=$(wget -qO- https://api.github.com/repos/jgm/pandoc/releases/latest | grep '"tag_name":' | cut -d '"' -f 4) && \
    wget https://github.com/jgm/pandoc/releases/download/$PANDOC_VERSION/pandoc-$PANDOC_VERSION-linux-amd64.tar.gz && \
    tar -xvzf pandoc-$PANDOC_VERSION-linux-amd64.tar.gz && \
    cp -r pandoc-$PANDOC_VERSION/bin/* /usr/local/bin/ && \
    rm -rf pandoc-$PANDOC_VERSION pandoc-$PANDOC_VERSION-linux-amd64.tar.gz

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the API port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
