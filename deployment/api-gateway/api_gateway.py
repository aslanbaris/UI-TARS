"""
UI-TARS API Gateway
Handles incoming requests and routes them to appropriate services
"""
import os
import json
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx
import redis
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Environment variables
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model-service:8081")
PARSER_SERVICE_URL = os.getenv("PARSER_SERVICE_URL", "http://parser-service:8082")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Initialize FastAPI app
app = FastAPI(
    title="UI-TARS API Gateway",
    description="API Gateway for UI-TARS GUI Automation System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis client
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None

# Pydantic models
class ActionRequest(BaseModel):
    task: str = Field(..., description="Task description")
    image_base64: Optional[str] = Field(None, description="Base64 encoded screenshot")
    image_url: Optional[str] = Field(None, description="URL to screenshot")
    model_type: str = Field("qwen25vl", description="Model type: qwen25vl, qwen2vl, doubao")
    factor: int = Field(1000, description="Coordinate factor")
    origin_width: int = Field(1920, description="Original screen width")
    origin_height: int = Field(1080, description="Original screen height")

class ActionResponse(BaseModel):
    task_id: str
    status: str
    thought: Optional[str] = None
    action_type: Optional[str] = None
    pyautogui_code: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, str]
    timestamp: str

# Helper functions
async def check_service_health(url: str, timeout: float = 5.0) -> bool:
    """Check if a service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url}/health")
            return response.status_code == 200
    except:
        return False

def cache_set(key: str, value: Any, expire: int = 3600):
    """Set cache with expiration"""
    if redis_client:
        try:
            redis_client.setex(key, expire, json.dumps(value))
        except Exception as e:
            print(f"Cache set error: {e}")

def cache_get(key: str) -> Optional[Any]:
    """Get cached value"""
    if redis_client:
        try:
            value = redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache get error: {e}")
    return None

# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {
        "model_service": "healthy" if await check_service_health(MODEL_SERVICE_URL) else "unhealthy",
        "parser_service": "healthy" if await check_service_health(PARSER_SERVICE_URL) else "unhealthy",
        "redis": "healthy" if redis_client else "unhealthy"
    }

    overall_status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"

    return HealthResponse(
        status=overall_status,
        services=services,
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "UI-TARS API Gateway",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/api/v1/action", response_model=ActionResponse)
async def process_action(request: ActionRequest):
    """
    Process GUI automation action

    1. Send image + prompt to model service
    2. Parse model output to structured format
    3. Generate PyAutoGUI code
    4. Return results
    """
    start_time = time.time()
    task_id = str(uuid.uuid4())

    try:
        # Step 1: Call model service
        model_payload = {
            "task": request.task,
            "image_base64": request.image_base64,
            "image_url": request.image_url,
            "model_type": request.model_type
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            model_response = await client.post(
                f"{MODEL_SERVICE_URL}/generate",
                json=model_payload
            )
            model_response.raise_for_status()
            model_data = model_response.json()

        raw_output = model_data.get("output", "")

        # Step 2: Parse output
        parse_payload = {
            "text": raw_output,
            "factor": request.factor,
            "origin_resized_height": request.origin_height,
            "origin_resized_width": request.origin_width,
            "model_type": request.model_type,
            "image_height": request.origin_height,
            "image_width": request.origin_width
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            parse_response = await client.post(
                f"{PARSER_SERVICE_URL}/parse",
                json=parse_payload
            )
            parse_response.raise_for_status()
            parse_data = parse_response.json()

        processing_time = time.time() - start_time

        # Cache result
        cache_data = {
            "task_id": task_id,
            "request": request.dict(),
            "response": parse_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        cache_set(f"task:{task_id}", cache_data, expire=7200)

        return ActionResponse(
            task_id=task_id,
            status="success",
            thought=parse_data.get("thought"),
            action_type=parse_data.get("action_type"),
            pyautogui_code=parse_data.get("pyautogui_code"),
            execution_result=parse_data.get("execution_result"),
            processing_time=processing_time
        )

    except httpx.HTTPStatusError as e:
        processing_time = time.time() - start_time
        error_msg = f"HTTP error from {e.request.url}: {e.response.status_code}"
        return ActionResponse(
            task_id=task_id,
            status="error",
            error=error_msg,
            processing_time=processing_time
        )

    except Exception as e:
        processing_time = time.time() - start_time
        return ActionResponse(
            task_id=task_id,
            status="error",
            error=str(e),
            processing_time=processing_time
        )

@app.post("/api/v1/action/execute", response_model=ActionResponse)
async def process_and_execute(request: ActionRequest):
    """
    Process action and execute it directly
    """
    start_time = time.time()
    task_id = str(uuid.uuid4())

    try:
        # First get the action
        action_result = await process_action(request)

        if action_result.status != "success" or not action_result.pyautogui_code:
            return action_result

        # Execute the action
        exec_payload = {
            "pyautogui_code": action_result.pyautogui_code
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            exec_response = await client.post(
                f"{PARSER_SERVICE_URL}/execute",
                json=exec_payload
            )
            exec_response.raise_for_status()
            exec_data = exec_response.json()

        action_result.execution_result = exec_data
        action_result.processing_time = time.time() - start_time

        return action_result

    except Exception as e:
        processing_time = time.time() - start_time
        return ActionResponse(
            task_id=task_id,
            status="error",
            error=str(e),
            processing_time=processing_time
        )

@app.get("/api/v1/task/{task_id}")
async def get_task_status(task_id: str):
    """Get task status and results from cache"""
    cached = cache_get(f"task:{task_id}")

    if not cached:
        raise HTTPException(status_code=404, detail="Task not found")

    return cached

@app.get("/api/v1/stats")
async def get_stats():
    """Get system statistics"""
    stats = {
        "total_tasks": 0,
        "successful_tasks": 0,
        "failed_tasks": 0,
        "avg_processing_time": 0
    }

    if redis_client:
        try:
            # Get all task keys
            task_keys = redis_client.keys("task:*")
            stats["total_tasks"] = len(task_keys)

            # You could add more detailed statistics here
        except Exception as e:
            print(f"Stats error: {e}")

    return stats

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
