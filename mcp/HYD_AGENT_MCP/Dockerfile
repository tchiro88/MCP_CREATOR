FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py .
COPY database_interface.py .
COPY schematic_parser.py .
COPY flow_analyzer.py .
COPY doc_manager.py .
COPY server.py .

# Create necessary directories
RUN mkdir -p schematics manufacturer_docs machines database

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose stdio for MCP communication
# (MCP uses stdio, not HTTP ports)

# Run the server
CMD ["python", "server.py"]
