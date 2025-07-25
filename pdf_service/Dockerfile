FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from parent directory
COPY pyproject.toml /app/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY pdf_service/ /app/pdf_service/

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV STORAGE_DIR=/app/uploads

# Run the application
CMD ["python", "-m", "pdf_service.main"]