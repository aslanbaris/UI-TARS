# UI-TARS Quick Start Guide

## 🚀 Quick Commands

### Start Services (Docker)
```bash
cd deployment
docker compose -f docker-compose.test.yml up -d
```

### Check Status
```bash
# All services health
curl http://localhost:9080/health | jq

# Individual services
curl http://localhost:9081/health  # Mock Model
curl http://localhost:9082/health  # Parser
curl http://localhost:9083/health  # Executor
```

### Test End-to-End
```bash
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

### View Logs
```bash
# All services
docker compose -f docker-compose.test.yml logs -f

# Specific service
docker logs uitars-api-gateway-test -f
docker logs uitars-model-service-test -f
docker logs uitars-parser-service-test -f
```

### Stop Services
```bash
docker compose -f docker-compose.test.yml down
```

### Clean Up (Remove all data)
```bash
docker compose -f docker-compose.test.yml down -v
```

---

## 🔧 Standalone Mode (Without Docker)

### Start
```bash
cd deployment
./start_services.sh
```

### Monitor
```bash
tail -f logs/model-service.log
tail -f logs/parser-service.log
tail -f logs/api-gateway.log
```

### Stop
```bash
./stop_services.sh
```

---

## 🧪 Run Tests

### Automated Test Suite
```bash
cd deployment
python3 test_standalone.py
```

Expected: `7/7 tests passed`

---

## 📍 Service URLs

| Service | URL |
|---------|-----|
| Nginx | http://localhost:9090 |
| API Gateway | http://localhost:9080 |
| API Docs | http://localhost:9080/docs |
| Mock Model | http://localhost:9081 |
| Parser | http://localhost:9082 |
| Executor | http://localhost:9083 |
| PostgreSQL | localhost:5433 |
| Redis | localhost:6380 |

---

## 🔍 Troubleshooting

### Services won't start
```bash
# Check what's using the ports
sudo lsof -i :9080
sudo lsof -i :9081
sudo lsof -i :9082

# Stop conflicting containers
docker ps -a
docker stop <container-id>
```

### Service not responding
```bash
# Restart specific service
docker compose -f docker-compose.test.yml restart api-gateway

# View detailed logs
docker logs uitars-api-gateway-test --tail 100
```

### Clean slate restart
```bash
# Stop everything
docker compose -f docker-compose.test.yml down -v

# Remove all UI-TARS containers
docker ps -a | grep uitars | awk '{print $1}' | xargs docker rm -f

# Start fresh
docker compose -f docker-compose.test.yml up -d
```

---

## 📊 Monitor Resources

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Network inspect
docker network inspect uitars-test-network
```

---

## 🛠️ Development

### Rebuild after code changes
```bash
# Rebuild specific service
docker compose -f docker-compose.test.yml build model-service
docker compose -f docker-compose.test.yml up -d model-service

# Rebuild all
docker compose -f docker-compose.test.yml build
docker compose -f docker-compose.test.yml up -d
```

### Access container shell
```bash
docker exec -it uitars-api-gateway-test bash
docker exec -it uitars-model-service-test bash
docker exec -it uitars-parser-service-test bash
```

### Database access
```bash
docker exec -it uitars-postgres-test psql -U uitars -d uitars
```

### Redis CLI
```bash
docker exec -it uitars-redis-test redis-cli
```

---

## 📝 Common Issues

### "Port already allocated"
- Another service is using the port
- Use `docker ps -a` to find conflicts
- Change ports in `docker-compose.test.yml`

### "Connection refused"
- Service might be starting (wait 10-15 seconds)
- Check logs: `docker logs <container-name>`
- Verify network: `docker network ls`

### "No such file or directory"
- Ensure you're in `/deployment` directory
- Check Docker is running: `docker ps`
- Verify files exist: `ls -la`

---

## 📚 Documentation

- **Full Guide:** `DEPLOYMENT_GUIDE.md`
- **Test Results:** `TESTING_RESULTS.md`
- **Architecture:** `../ui-tars-analysis.html`

---

**Quick Health Check:**
```bash
curl -s http://localhost:9080/health | jq -r '.status'
```
Expected output: `healthy`
