FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    iptables \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the app code
COPY . .

# Set environment variables for Docker
ENV DOCKER_HOST=unix:///var/run/docker.sock
ENV TINI_SUBREAPER=true

# Command to run the app
CMD ["python3", "main.py"]
