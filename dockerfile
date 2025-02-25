FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py .
COPY config.json .

# Create directory for output data
RUN mkdir -p /app/output_data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CONFIG_PATH=/app/config.json

# Expose port for dashboard
EXPOSE 8050

# Set entrypoint
ENTRYPOINT ["python"]
