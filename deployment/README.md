# UI-TARS Container Deployment

Complete containerized deployment setup for UI-TARS GUI automation system.

## 📚 Documentation Index

**Choose your deployment path:**

- 🚀 **[QUICK_START.md](QUICK_START.md)** - Quick commands and common operations
- 🧪 **[Testing without GPU](#testing-without-gpu)** - Use mock model service (see below)
- 📖 **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide with troubleshooting
- ✅ **[TESTING_RESULTS.md](TESTING_RESULTS.md)** - Validation results and test reports
- 🏗️ **[Production Setup](#-quick-start)** - GPU-based production deployment (this page)

---

## 🧪 Testing Without GPU

For development and testing **without GPU requirements**, use the mock model service:

```bash
# Use test configuration (no GPU needed)
docker compose -f docker-compose.test.yml up -d

# Check health
curl http://localhost:9080/health | jq

# Run automated tests
python3 test_standalone.py

# Stop services
docker compose -f docker-compose.test.yml down
```

**Test Environment Ports:** 9080-9083, 9090 (to avoid conflicts)

See **[QUICK_START.md](QUICK_START.md)** for complete testing guide.

---

## 🏭 Production Deployment (GPU Required)

The following sections describe **production deployment** with GPU support:

## 🏗️ Architecture

```
┌─────────────┐
│   Nginx     │ (Load Balancer)
│   Port 80   │
└──────┬──────┘
       │
┌──────▼──────────┐
│  API Gateway    │
│   Port 8080     │
└─────┬───────────┘
      │
      ├──────────────────┬─────────────────┬──────────────┐
      │                  │                 │              │
┌─────▼────────┐  ┌─────▼────────┐  ┌────▼──────┐  ┌───▼────┐
│ Model Service│  │Parser Service│  │  Executor │  │ Redis  │
│  (HF TGI)    │  │ (ui-tars)    │  │ (PyAutoGUI│  │ Cache  │
│  Port 8081   │  │  Port 8082   │  │ + VNC)    │  │        │
│  + GPU       │  │              │  │ Port 8083 │  │        │
└──────────────┘  └──────────────┘  └───────────┘  └────────┘
                                          │
                                    ┌─────▼──────┐
                                    │ PostgreSQL │
                                    │  Database  │
                                    └────────────┘
```

## 📋 Prerequisites

### System Requirements
- **Docker** 20.10+ with Docker Compose v2
- **NVIDIA Docker** (for GPU support)
- **GPU**: NVIDIA GPU with 48GB+ VRAM (for 7B model)
- **RAM**: 32GB+ system RAM
- **Disk**: 100GB+ free space

### NVIDIA Docker Installation

```bash
# Install NVIDIA Docker
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/aslanbaris/UI-TARS.git
cd UI-TARS/deployment

# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

**Required environment variables:**
- `DB_PASSWORD`: PostgreSQL database password
- `HF_TOKEN`: Your HuggingFace API token (get it from https://huggingface.co/settings/tokens)

### 2. Build Services

```bash
# Build all containers
docker-compose build

# Or build specific service
docker-compose build api-gateway
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Verify Deployment

```bash
# Check API Gateway health
curl http://localhost:8080/health

# Check all services
curl http://localhost:8080/api/v1/stats
```

## 🧪 Testing

### Test API Gateway

```bash
# Health check
curl http://localhost/health

# Get service info
curl http://localhost/
```

### Test with Example Request

```python
import requests
import base64

# Load an image
with open("screenshot.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

# Make request
response = requests.post(
    "http://localhost/api/v1/action",
    json={
        "task": "Click the login button",
        "image_base64": image_base64,
        "model_type": "qwen25vl",
        "origin_width": 1920,
        "origin_height": 1080
    }
)

print(response.json())
```

### VNC Access to Executor

The executor service runs a VNC server for remote desktop access:

```bash
# Connect via VNC client
vnc://localhost:5900

# Or use VNC viewer
vncviewer localhost:5900
```

## 📊 Service Details

### API Gateway (Port 8080)
- **Routes requests** to appropriate services
- **Caches results** in Redis
- **Rate limiting** and security headers
- **Health monitoring**

**Endpoints:**
- `GET /health` - Health check
- `POST /api/v1/action` - Process GUI action
- `POST /api/v1/action/execute` - Process and execute
- `GET /api/v1/task/{task_id}` - Get task status
- `GET /api/v1/stats` - System statistics

### Model Service (Port 8081)
- **HuggingFace TGI** with UI-TARS 1.5 7B
- **GPU-accelerated** inference
- **Automatic model download** on first start
- **OpenAI-compatible API**

### Parser Service (Port 8082)
- **Parses LLM outputs** using ui-tars library
- **Generates PyAutoGUI code**
- **Coordinates execution** requests

### Executor Service (Port 8083)
- **Executes PyAutoGUI code** in virtual display
- **VNC server** for remote access (port 5900)
- **Screenshot capture**
- **Mouse/keyboard control**

## 🔧 Configuration

### Scaling Services

```bash
# Scale executor service to 3 instances
docker-compose up -d --scale executor-service=3

# Scale parser service
docker-compose up -d --scale parser-service=2
```

### Resource Limits

Edit `docker-compose.yml` to adjust resource limits:

```yaml
services:
  api-gateway:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## 📝 Management Commands

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart specific service
docker-compose restart api-gateway
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway

# Last 100 lines
docker-compose logs --tail=100 model-service
```

### Access Container Shell

```bash
# API Gateway
docker-compose exec api-gateway /bin/bash

# Executor (check display)
docker-compose exec executor-service /bin/bash
echo $DISPLAY
```

## 🔍 Monitoring

### Service Health

```bash
# Check all services
docker-compose ps

# Detailed health info
curl http://localhost:8080/health | jq
```

### Resource Usage

```bash
# Docker stats
docker stats

# Specific container
docker stats uitars-model-service
```

### Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U uitars -d uitars

# View tables
\dt

# Query tasks
SELECT * FROM tasks LIMIT 10;
```

### Redis

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check keys
KEYS *

# Get task info
GET task:xxx
```

## 🐛 Troubleshooting

### Model Service Not Starting

```bash
# Check GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Check model service logs
docker-compose logs model-service

# Verify HF_TOKEN
docker-compose exec model-service env | grep HF_TOKEN
```

### Executor Display Issues

```bash
# Check Xvfb
docker-compose exec executor-service ps aux | grep Xvfb

# Test display
docker-compose exec executor-service python3 -c "import pyautogui; print(pyautogui.size())"
```

### Connection Issues

```bash
# Check network
docker network ls
docker network inspect uitars-network

# Test connectivity
docker-compose exec api-gateway curl http://model-service:8081/health
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose logs postgres
```

## 🔐 Security

### Production Checklist

- [ ] Change default passwords in `.env`
- [ ] Enable HTTPS in nginx.conf
- [ ] Add authentication to API Gateway
- [ ] Restrict VNC access (firewall rules)
- [ ] Enable PostgreSQL SSL
- [ ] Set up Redis password
- [ ] Configure rate limiting
- [ ] Enable audit logging

### SSL/TLS Setup

```bash
# Generate self-signed certificate (for testing)
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem

# Uncomment HTTPS server block in nginx.conf
# Restart nginx
docker-compose restart nginx
```

## 📈 Performance Tuning

### Model Service

```yaml
# In docker-compose.yml
environment:
  - MAX_BATCH_PREFILL_TOKENS=8192
  - MAX_BATCH_TOTAL_TOKENS=16384
  - MAX_CONCURRENT_REQUESTS=128
```

### API Gateway

```yaml
# Increase workers
CMD ["uvicorn", "api_gateway:app", "--workers", "8"]
```

### Nginx

```nginx
# In nginx.conf
worker_processes 4;
worker_connections 2048;
```

## 🗂️ Directory Structure

```
deployment/
├── docker-compose.yml          # Main orchestration file
├── .env.example                # Environment template
├── .env                        # Your environment (git-ignored)
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
├── api-gateway/
│   ├── Dockerfile
│   ├── api_gateway.py
│   └── requirements.txt
├── model-service/
│   ├── Dockerfile
│   └── README.md
├── parser-service/
│   ├── Dockerfile
│   ├── parser_service.py
│   └── requirements.txt
├── executor-service/
│   ├── Dockerfile
│   ├── executor_service.py
│   ├── requirements.txt
│   └── start.sh
└── nginx/
    └── nginx.conf
```

## 📚 Additional Resources

- **UI-TARS Documentation**: https://github.com/aslanbaris/UI-TARS
- **HuggingFace Model**: https://huggingface.co/ByteDance-Seed/UI-TARS-1.5-7B
- **Paper**: https://arxiv.org/abs/2501.12326
- **Website**: https://seed-tars.com/

## 🤝 Support

For issues and questions:
- GitHub Issues: https://github.com/aslanbaris/UI-TARS/issues
- Discord: https://discord.gg/pTXwYVjfcs

## 📄 License

Apache 2.0 - See LICENSE file for details
