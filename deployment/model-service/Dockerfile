# Model Service Dockerfile
# Uses HuggingFace Text Generation Inference

FROM ghcr.io/huggingface/text-generation-inference:3.2.1

# Environment variables are set in docker-compose.yml:
# - CUDA_GRAPHS=0
# - PAYLOAD_LIMIT=8000000
# - MAX_INPUT_LENGTH=65536
# - MAX_TOTAL_TOKENS=65537
# - MODEL_ID=ByteDance-Seed/UI-TARS-1.5-7B
# - HF_TOKEN

# Model will be automatically downloaded from HuggingFace Hub
# on first startup using the MODEL_ID and HF_TOKEN

EXPOSE 8080

# The entrypoint is already defined in the base image
# It will launch text-generation-launcher with the provided environment variables
