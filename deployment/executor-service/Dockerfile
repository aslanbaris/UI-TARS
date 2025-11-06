FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    xvfb \
    x11vnc \
    fluxbox \
    scrot \
    python3-tk \
    python3-dev \
    xdotool \
    wmctrl \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY executor_service.py .
COPY start.sh .

# Make start script executable
RUN chmod +x start.sh

# Setup VNC
ENV DISPLAY=:99

# Expose ports
EXPOSE 8000 5900

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start services
CMD ["./start.sh"]
