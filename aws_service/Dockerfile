FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from parent directory
COPY pyproject.toml /app/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY aws_service/ /app/aws_service/

# Expose port
EXPOSE 8002

# Set environment variables
ENV PYTHONPATH=/app
ENV AWS_REGION=us-east-1
ENV DYNAMODB_TABLE_DOCUMENTS=DocumentsMetadata
ENV S3_BUCKET=documents-rag-bucket
ENV RAG_SERVICE_URL=http://rag_module:8001
ENV RAG_SERVICE_TIMEOUT=60.0

# Run the application
CMD ["python", "-m", "aws_service.main"]