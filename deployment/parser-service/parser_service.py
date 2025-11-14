"""
UI-TARS Parser Service
Handles parsing of LLM outputs and PyAutoGUI code generation
"""
import os
import json
from typing import Optional, Dict, Any, List

import httpx
import redis
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import ui-tars library
from ui_tars.action_parser import (
    parse_action_to_structure_output,
    parsing_response_to_pyautogui_code
)

# Environment variables
EXECUTOR_SERVICE_URL = os.getenv("EXECUTOR_SERVICE_URL", "http://executor-service:8083")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Initialize FastAPI app
app = FastAPI(
    title="UI-TARS Parser Service",
    description="Parsing service for UI-TARS GUI Automation",
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
class ParseRequest(BaseModel):
    text: str = Field(..., description="LLM output text")
    factor: int = Field(1000, description="Coordinate factor")
    origin_resized_height: int = Field(1080, description="Original image height")
    origin_resized_width: int = Field(1920, description="Original image width")
    model_type: str = Field("qwen25vl", description="Model type")
    image_height: int = Field(1080, description="Target screen height")
    image_width: int = Field(1920, description="Target screen width")
    max_pixels: int = Field(16384 * 28 * 28, description="Max pixels")
    min_pixels: int = Field(100 * 28 * 28, description="Min pixels")

class ParseResponse(BaseModel):
    status: str
    thought: Optional[str] = None
    action_type: Optional[str] = None
    action_inputs: Optional[Dict[str, Any]] = None
    pyautogui_code: Optional[str] = None
    structured_output: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class ExecuteRequest(BaseModel):
    pyautogui_code: str = Field(..., description="PyAutoGUI code to execute")

class ExecuteResponse(BaseModel):
    status: str
    result: Optional[str] = None
    error: Optional[str] = None

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "parser-service",
        "redis": "connected" if redis_client else "disconnected"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "UI-TARS Parser Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/parse", response_model=ParseResponse)
async def parse_action(request: ParseRequest):
    """
    Parse LLM output to structured format and generate PyAutoGUI code
    """
    try:
        # Step 1: Parse to structured output
        structured_output = parse_action_to_structure_output(
            text=request.text,
            factor=request.factor,
            origin_resized_height=request.origin_resized_height,
            origin_resized_width=request.origin_resized_width,
            model_type=request.model_type,
            max_pixels=request.max_pixels,
            min_pixels=request.min_pixels
        )

        if not structured_output or len(structured_output) == 0:
            return ParseResponse(
                status="error",
                error="Failed to parse action - empty output"
            )

        # Get the first action (most recent)
        action = structured_output[0] if isinstance(structured_output, list) else structured_output

        # Step 2: Generate PyAutoGUI code
        pyautogui_code = parsing_response_to_pyautogui_code(
            responses=structured_output,
            image_height=request.image_height,
            image_width=request.image_width,
            input_swap=True
        )

        return ParseResponse(
            status="success",
            thought=action.get("thought"),
            action_type=action.get("action_type"),
            action_inputs=action.get("action_inputs"),
            pyautogui_code=pyautogui_code,
            structured_output=structured_output
        )

    except Exception as e:
        return ParseResponse(
            status="error",
            error=str(e)
        )

@app.post("/execute", response_model=ExecuteResponse)
async def execute_action(request: ExecuteRequest):
    """
    Forward execution request to executor service
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{EXECUTOR_SERVICE_URL}/execute",
                json={"code": request.pyautogui_code}
            )
            response.raise_for_status()
            result = response.json()

        return ExecuteResponse(
            status="success",
            result=result.get("message", "Executed successfully")
        )

    except httpx.HTTPStatusError as e:
        return ExecuteResponse(
            status="error",
            error=f"Executor service error: {e.response.status_code}"
        )

    except Exception as e:
        return ExecuteResponse(
            status="error",
            error=str(e)
        )

@app.post("/parse-and-execute")
async def parse_and_execute(request: ParseRequest):
    """
    Parse action and execute it immediately
    """
    try:
        # Parse action
        parse_result = await parse_action(request)

        if parse_result.status != "success" or not parse_result.pyautogui_code:
            return {
                "status": "error",
                "error": parse_result.error or "Failed to parse action",
                "parse_result": parse_result.dict()
            }

        # Execute action
        exec_request = ExecuteRequest(pyautogui_code=parse_result.pyautogui_code)
        exec_result = await execute_action(exec_request)

        return {
            "status": "success",
            "parse_result": parse_result.dict(),
            "execution_result": exec_result.dict()
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8082))
    uvicorn.run(app, host="0.0.0.0", port=port)
