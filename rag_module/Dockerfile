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
COPY rag_module/ /app/rag_module/

# Expose port
EXPOSE 8001

# Set environment variables
ENV PYTHONPATH=/app
ENV CHUNK_SIZE=1000
ENV CHUNK_OVERLAP=200
ENV TOP_K=5
ENV EMBEDDING_MODEL=text-embedding-3-small
ENV LLM_MODEL=gpt-3.5-turbo
ENV MAX_TOKENS=1000
ENV TEMPERATURE=0.7
ENV EMBEDDING_DIMENSION=1536
ENV PINECONE_METRIC=cosine
ENV PINECONE_CLOUD=aws
ENV PINECONE_REGION=us-east-1
ENV PDF_SERVICE_URL=http://pdf_service:8000
ENV PDF_SERVICE_TIMEOUT=30.0
ENV METRICS_TIMEOUT=30.0

# Run the application
CMD ["python", "-m", "rag_module.main"]