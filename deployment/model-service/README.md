# UI-TARS Model Service

This service runs the UI-TARS 1.5 7B model using HuggingFace Text Generation Inference (TGI).

## Requirements

- **GPU**: NVIDIA GPU with CUDA support (L40S, A100, or similar)
- **VRAM**: Minimum 48GB for 7B model
- **HuggingFace Token**: Required to download the model

## Configuration

The model service is configured through environment variables in docker-compose.yml:

```yaml
environment:
  - CUDA_GRAPHS=0              # Disable CUDA graphs (avoid deployment failures)
  - PAYLOAD_LIMIT=8000000      # Allow large image payloads
  - MAX_INPUT_LENGTH=65536     # Maximum input tokens
  - MAX_TOTAL_TOKENS=65537     # Maximum total tokens
  - HF_TOKEN=${HF_TOKEN}       # Your HuggingFace API token
  - MODEL_ID=ByteDance-Seed/UI-TARS-1.5-7B
```

## Usage

The model will be automatically downloaded on first startup. This may take several minutes depending on your internet connection.

### API Endpoint

```
POST http://model-service:8080/generate
```

### Example Request

```python
import requests

response = requests.post(
    "http://localhost:8081/generate",
    json={
        "inputs": "Click the login button",
        "parameters": {
            "max_new_tokens": 400,
            "temperature": 0.0
        }
    }
)

print(response.json())
```

## Scaling

For production deployments with higher load:

1. **Multiple Replicas**: Scale the model service horizontally
2. **Load Balancing**: Use Nginx to distribute requests
3. **Batching**: Enable batch inference in TGI settings

## Troubleshooting

### Model Download Issues
- Ensure HF_TOKEN is valid
- Check internet connectivity
- Verify model name is correct

### GPU Issues
- Verify NVIDIA drivers are installed
- Check CUDA version compatibility
- Ensure docker has GPU access (nvidia-docker)

### Memory Issues
- Monitor GPU memory usage
- Reduce batch size if OOM occurs
- Consider using quantized model versions
