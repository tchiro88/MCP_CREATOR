# Outlook MCP Service Dockerfile
# Production-ready container with Playwright and Chromium

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and system dependencies
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY outlook_web_client.py .
COPY server.py .

# Create session directory for persistent storage
RUN mkdir -p /app/session && chmod 777 /app/session

# Environment variables with defaults
ENV OUTLOOK_SESSION_DIR=/app/session \
    OUTLOOK_HEADLESS=true \
    OUTLOOK_TIMEOUT=30000 \
    PYTHONUNBUFFERED=1

# Expose port for HTTP transport (if needed in future)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the MCP server
CMD ["python", "-u", "server.py"]
