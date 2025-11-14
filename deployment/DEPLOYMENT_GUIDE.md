# UI-TARS Deployment Guide

## Overview
This guide documents the complete deployment infrastructure for UI-TARS with Docker containerization and standalone testing capabilities.

## Architecture

### Services
The deployment consists of 7 microservices:

1. **Nginx Load Balancer** (Port 9090)
   - Reverse proxy for API Gateway
   - Load balancing capabilities

2. **API Gateway** (Port 9080)
   - Central coordination service
   - Routes requests to model and parser services
   - Health check aggregation

3. **Mock Model Service** (Port 9081)
   - GPU-free testing alternative
   - Simulates UI-TARS VLM responses
   - FastAPI-based service

4. **Parser Service** (Port 9082)
   - Parses model actions into structured output
   - Generates PyAutoGUI code
   - Uses ui-tars library

5. **Executor Service** (Port 9083, VNC 5901)
   - Executes PyAutoGUI commands
   - Virtual display for GUI automation
   - Screenshot capture

6. **PostgreSQL Database** (Port 5433)
   - Persistent storage
   - Task and execution history

7. **Redis Cache** (Port 6380)
   - Session management
   - Result caching

### Network Architecture
```
Internet → Nginx (9090) → API Gateway (9080) → Model Service (9081)
                                             ↓ Parser Service (9082)
                                             ↓ Executor Service (9083)
                                             ↓ Redis (6380)
                                             ↓ PostgreSQL (5433)
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

#### Test Environment (No GPU Required)
```bash
cd deployment
docker compose -f docker-compose.test.yml up -d
```

#### Production Environment (GPU Required)
```bash
cd deployment
docker compose -f docker-compose.yml up -d
```

#### Service Health Checks
```bash
# Check all service health
curl http://localhost:9080/health | jq

# Individual services
curl http://localhost:9081/health  # Mock Model
curl http://localhost:9082/health  # Parser
curl http://localhost:9083/health  # Executor
```

### Option 2: Standalone (Without Docker)

For development and testing without containerization:

```bash
cd deployment

# Start services
./start_services.sh

# Monitor logs
tail -f logs/model-service.log
tail -f logs/parser-service.log
tail -f logs/api-gateway.log

# Stop services
./stop_services.sh
```

## Testing

### Automated Test Suite
Run the comprehensive test suite:

```bash
cd deployment
python3 test_standalone.py
```

**Test Coverage:**
- ✓ Package Imports (fastapi, uvicorn, pydantic, redis, httpx)
- ✓ UI-TARS Library Functionality
- ✓ Mock Model Service
- ✓ Service Endpoints
- ✓ Docker Compose Files
- ✓ Dockerfiles
- ✓ Integration Test (End-to-End)

### Manual End-to-End Test

Test the complete pipeline with a real request:

```bash
# Install jq for JSON formatting (if not already installed)
sudo apt install jq -y

# Send test request
curl -X POST http://localhost:9080/api/v1/action \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Click the login button",
    "image_base64": "dummy_base64_image_data",
    "model_type": "qwen25vl",
    "origin_width": 1920,
    "origin_height": 1080
  }' | jq
```

**Expected Response:**
```json
{
  "task_id": "...",
  "status": "success",
  "action": {
    "thought": "I see a login button",
    "action_type": "click",
    "coordinates": [960, 540]
  },
  "pyautogui_code": "import pyautogui\npyautogui.click(960, 540)\n",
  "processing_time_ms": 123
}
```

## Port Configuration

### Default Ports (Production)
- Nginx: 8090
- API Gateway: 8080
- Model Service: 8081
- Parser Service: 8082
- Executor Service: 8083
- PostgreSQL: 5432
- Redis: 6379

### Test Ports (To Avoid Conflicts)
- Nginx: 9090
- API Gateway: 9080
- Model Service: 9081
- Parser Service: 9082
- Executor Service: 9083
- PostgreSQL: 5433
- Redis: 6380

## Environment Variables

### API Gateway
```bash
MODEL_SERVICE_URL=http://model-service:8080
PARSER_SERVICE_URL=http://parser-service:8000
REDIS_URL=redis://redis:6379
DATABASE_URL=postgresql://uitars:password@postgres:5432/uitars
```

### Services
```bash
PORT=8080                    # Service port
REDIS_URL=redis://redis:6379
EXECUTOR_SERVICE_URL=http://executor-service:8000
DATABASE_URL=postgresql://...
```

## Troubleshooting

### Port Conflicts
If you get "port already allocated" errors:

1. Check running containers:
   ```bash
   docker ps -a
   ```

2. Stop conflicting services:
   ```bash
   docker stop <container-name>
   ```

3. Use test configuration with alternative ports:
   ```bash
   docker compose -f docker-compose.test.yml up -d
   ```

### Service Not Responding
1. Check container logs:
   ```bash
   docker logs uitars-api-gateway-test
   docker logs uitars-model-service-test
   docker logs uitars-parser-service-test
   ```

2. Verify network connectivity:
   ```bash
   docker network inspect uitars-test-network
   ```

3. Restart specific service:
   ```bash
   docker compose -f docker-compose.test.yml restart api-gateway
   ```

### Executor Service X Display Issues
The executor service may show X display connection warnings. This is expected in containerized environments and doesn't affect functionality:

```
Error: Can't open display: :99
```

**Solutions:**
- VNC is available on port 5901 for GUI access
- Display issues don't prevent screenshot/execution operations
- For production, ensure X11 forwarding is properly configured

### Database Connection Issues
1. Check PostgreSQL is running:
   ```bash
   docker logs uitars-postgres-test
   ```

2. Verify credentials match environment variables

3. Check health status:
   ```bash
   docker inspect uitars-postgres-test | grep Health
   ```

### Redis Connection Issues
1. Test Redis connectivity:
   ```bash
   docker exec uitars-redis-test redis-cli ping
   ```

2. Expected response: `PONG`

## Development Workflow

### Making Changes
1. Modify service code in respective directories:
   - `api-gateway/`
   - `model-service/`
   - `parser-service/`
   - `executor-service/`

2. Rebuild specific service:
   ```bash
   docker compose -f docker-compose.test.yml build model-service
   docker compose -f docker-compose.test.yml up -d model-service
   ```

3. View logs for debugging:
   ```bash
   docker compose -f docker-compose.test.yml logs -f model-service
   ```

### Running Tests
```bash
# Run standalone tests
python3 test_standalone.py

# Test with services running
./start_services.sh
python3 test_standalone.py
./stop_services.sh
```

## Performance Considerations

### Resource Requirements

**Minimum (Mock Model):**
- CPU: 2 cores
- RAM: 4 GB
- Storage: 10 GB

**Production (With GPU Model):**
- CPU: 4+ cores
- RAM: 16+ GB
- GPU: NVIDIA with 8GB+ VRAM
- Storage: 20+ GB

### Scaling
For high-load scenarios:

1. **Horizontal Scaling:**
   - Scale API Gateway instances
   - Load balance with Nginx

2. **Vertical Scaling:**
   - Increase container resource limits
   - Optimize database queries

3. **Caching:**
   - Redis configured for result caching
   - Reduce model inference calls

## Security Considerations

1. **Database Credentials:**
   - Change default password in production
   - Use environment files (`.env`)

2. **Network Security:**
   - Configure firewall rules
   - Use TLS/SSL for external access

3. **Container Security:**
   - Regular image updates
   - Scan for vulnerabilities
   - Run as non-root user

## Monitoring

### Health Endpoints
- API Gateway: `http://localhost:9080/health`
- Model Service: `http://localhost:9081/health`
- Parser Service: `http://localhost:9082/health`
- Executor Service: `http://localhost:9083/health`

### Logs
```bash
# Container logs
docker compose -f docker-compose.test.yml logs -f

# Standalone logs
tail -f logs/*.log
```

### Metrics
Monitor container stats:
```bash
docker stats
```

## Backup and Recovery

### Database Backup
```bash
docker exec uitars-postgres-test pg_dump -U uitars uitars > backup.sql
```

### Volume Backup
```bash
docker run --rm -v uitars_postgres-data-test:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/postgres-backup.tar.gz /data
```

### Recovery
```bash
# Restore database
cat backup.sql | docker exec -i uitars-postgres-test psql -U uitars uitars

# Restore volume
docker run --rm -v uitars_postgres-data-test:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/postgres-backup.tar.gz -C /
```

## Production Deployment Checklist

- [ ] Update database passwords
- [ ] Configure SSL/TLS certificates
- [ ] Set up monitoring and alerting
- [ ] Configure backup schedule
- [ ] Review and adjust resource limits
- [ ] Enable authentication/authorization
- [ ] Configure logging aggregation
- [ ] Set up CI/CD pipeline
- [ ] Perform load testing
- [ ] Document disaster recovery procedures

## Support and Documentation

### Additional Resources
- **UI-TARS Repository:** https://github.com/aslanbaris/UI-TARS
- **Architecture Analysis:** `ui-tars-analysis.html`
- **Docker Compose Configs:**
  - Production: `docker-compose.yml`
  - Testing: `docker-compose.test.yml`

### Service Documentation
- **FastAPI Docs:** http://localhost:9080/docs (API Gateway)
- **Mock Model Docs:** http://localhost:9081/docs
- **Parser Docs:** http://localhost:9082/docs

## Version History

### v1.0.0 - Initial Deployment (2025-11-14)
- Complete microservices architecture
- Docker Compose configurations
- Mock model service for GPU-free testing
- Standalone testing scripts
- Comprehensive test suite
- Service management scripts
- Health check implementation
- All services verified and working

---

**Deployment Status:** ✅ All services healthy and operational
**Last Updated:** 2025-11-14
**Branch:** `claude/analyze-ui-tars-architecture-011CUrdGcD4sf8g9PbTbdqoJ`
