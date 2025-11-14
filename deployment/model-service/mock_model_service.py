"""
Mock Model Service for Testing
Simulates UI-TARS model responses without GPU requirements
"""
import time
import random
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="UI-TARS Mock Model Service",
    description="Mock service for testing without GPU",
    version="1.0.0-mock"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class GenerateRequest(BaseModel):
    task: str
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    model_type: str = "qwen25vl"
    max_tokens: int = 400
    temperature: float = 0.0

class GenerateResponse(BaseModel):
    output: str
    model: str
    processing_time: float

# Mock responses for different task types
MOCK_RESPONSES = {
    "click": [
        "Thought: I can see a login button in the center of the screen. I should click on it to proceed with the login process.\nAction: click(start_box='(960,540)')",
        "Thought: There's a submit button at the bottom right. I'll click it to submit the form.\nAction: click(start_box='(1200,900)')",
        "Thought: I notice a settings icon in the top right corner. Let me click on it.\nAction: click(start_box='(1800,100)')",
    ],
    "type": [
        "Thought: I see a text input field that requires username. I'll type the username here.\nAction: type(content='testuser')",
        "Thought: The password field is visible and empty. I should enter the password.\nAction: type(content='password123')",
        "Thought: There's a search box at the top. I'll type my search query.\nAction: type(content='UI-TARS automation')",
    ],
    "scroll": [
        "Thought: The content continues below. I need to scroll down to see more.\nAction: scroll(start_box='(960,540)', direction='down')",
        "Thought: I need to go back to the top of the page.\nAction: scroll(start_box='(960,540)', direction='up')",
    ],
    "drag": [
        "Thought: I need to select this text by dragging from start to end.\nAction: drag(start_box='(300,400)', end_box='(700,400)')",
        "Thought: I'll drag this element to the new position.\nAction: select(start_box='(500,300)', end_box='(800,600)')",
    ],
    "default": [
        "Thought: Analyzing the screen to determine the best action to take.\nAction: click(start_box='(960,540)')",
    ]
}

def generate_mock_response(task: str) -> str:
    """Generate a mock response based on task keywords"""
    task_lower = task.lower()

    # Determine response type based on keywords
    if any(word in task_lower for word in ["click", "press", "button", "tap"]):
        responses = MOCK_RESPONSES["click"]
    elif any(word in task_lower for word in ["type", "enter", "input", "write"]):
        responses = MOCK_RESPONSES["type"]
    elif any(word in task_lower for word in ["scroll", "down", "up"]):
        responses = MOCK_RESPONSES["scroll"]
    elif any(word in task_lower for word in ["drag", "select", "move"]):
        responses = MOCK_RESPONSES["drag"]
    else:
        responses = MOCK_RESPONSES["default"]

    return random.choice(responses)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mock-model-service",
        "mode": "testing",
        "gpu_required": False
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "UI-TARS Mock Model Service",
        "version": "1.0.0-mock",
        "status": "running",
        "note": "This is a mock service for testing without GPU"
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate mock model response
    Simulates model inference delay
    """
    # Simulate processing time
    processing_time = random.uniform(0.5, 2.0)
    time.sleep(processing_time)

    # Generate mock response
    output = generate_mock_response(request.task)

    return GenerateResponse(
        output=output,
        model="UI-TARS-1.5-7B-MOCK",
        processing_time=processing_time
    )

@app.get("/info")
async def get_info():
    """Get model information"""
    return {
        "model_id": "ByteDance-Seed/UI-TARS-1.5-7B",
        "mode": "mock",
        "capabilities": [
            "GUI action recognition",
            "Coordinate prediction",
            "Action planning"
        ],
        "supported_actions": [
            "click", "double_click", "right_click",
            "type", "hotkey", "scroll",
            "drag", "select"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)
