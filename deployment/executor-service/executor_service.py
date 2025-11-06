"""
UI-TARS Executor Service
Executes PyAutoGUI commands in a virtual display environment
"""
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import redis
import pyautogui
import pyperclip
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
DISPLAY = os.getenv("DISPLAY", ":99")

# Initialize FastAPI app
app = FastAPI(
    title="UI-TARS Executor Service",
    description="Execution service for PyAutoGUI automation",
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

# Configure PyAutoGUI
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.5

# Pydantic models
class ExecuteRequest(BaseModel):
    code: str = Field(..., description="PyAutoGUI code to execute")
    screenshot_before: bool = Field(False, description="Take screenshot before execution")
    screenshot_after: bool = Field(True, description="Take screenshot after execution")

class ExecuteResponse(BaseModel):
    status: str
    execution_id: str
    message: Optional[str] = None
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    error: Optional[str] = None
    execution_time: float

class ScreenshotResponse(BaseModel):
    status: str
    screenshot_path: str
    timestamp: str

# Helper functions
def take_screenshot() -> str:
    """Take a screenshot and save it"""
    screenshots_dir = "/app/screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(screenshots_dir, filename)

    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        return filepath
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None

def execute_pyautogui_code(code: str) -> Dict[str, Any]:
    """
    Execute PyAutoGUI code safely
    """
    result = {
        "success": False,
        "message": None,
        "error": None
    }

    try:
        # Create a safe execution environment
        safe_globals = {
            "pyautogui": pyautogui,
            "pyperclip": pyperclip,
            "time": time,
            "__builtins__": __builtins__
        }

        # Execute the code
        exec(code, safe_globals)

        result["success"] = True
        result["message"] = "Code executed successfully"

    except Exception as e:
        result["error"] = str(e)
        print(f"Execution error: {e}")

    return result

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if display is available
        screen_size = pyautogui.size()

        return {
            "status": "healthy",
            "service": "executor-service",
            "display": DISPLAY,
            "screen_size": {"width": screen_size[0], "height": screen_size[1]},
            "redis": "connected" if redis_client else "disconnected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "UI-TARS Executor Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/execute", response_model=ExecuteResponse)
async def execute_action(request: ExecuteRequest):
    """
    Execute PyAutoGUI code
    """
    execution_id = str(uuid.uuid4())
    start_time = time.time()

    screenshot_before_path = None
    screenshot_after_path = None

    try:
        # Take screenshot before execution
        if request.screenshot_before:
            screenshot_before_path = take_screenshot()

        # Execute the code
        exec_result = execute_pyautogui_code(request.code)

        # Take screenshot after execution
        if request.screenshot_after:
            time.sleep(1)  # Wait for UI to update
            screenshot_after_path = take_screenshot()

        execution_time = time.time() - start_time

        if exec_result["success"]:
            return ExecuteResponse(
                status="success",
                execution_id=execution_id,
                message=exec_result["message"],
                screenshot_before=screenshot_before_path,
                screenshot_after=screenshot_after_path,
                execution_time=execution_time
            )
        else:
            return ExecuteResponse(
                status="error",
                execution_id=execution_id,
                error=exec_result["error"],
                screenshot_before=screenshot_before_path,
                screenshot_after=screenshot_after_path,
                execution_time=execution_time
            )

    except Exception as e:
        execution_time = time.time() - start_time
        return ExecuteResponse(
            status="error",
            execution_id=execution_id,
            error=str(e),
            execution_time=execution_time
        )

@app.post("/screenshot", response_model=ScreenshotResponse)
async def capture_screenshot():
    """
    Take a screenshot of the current display
    """
    try:
        filepath = take_screenshot()

        if filepath:
            return ScreenshotResponse(
                status="success",
                screenshot_path=filepath,
                timestamp=datetime.now().isoformat()
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to capture screenshot")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/screen/info")
async def get_screen_info():
    """Get screen information"""
    try:
        screen_size = pyautogui.size()
        mouse_position = pyautogui.position()

        return {
            "screen_width": screen_size[0],
            "screen_height": screen_size[1],
            "mouse_x": mouse_position[0],
            "mouse_y": mouse_position[1],
            "display": DISPLAY
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mouse/move")
async def move_mouse(x: int, y: int, duration: float = 0.5):
    """Move mouse to coordinates"""
    try:
        pyautogui.moveTo(x, y, duration=duration)
        return {"status": "success", "x": x, "y": y}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mouse/click")
async def click_mouse(x: Optional[int] = None, y: Optional[int] = None, button: str = "left"):
    """Click mouse at coordinates"""
    try:
        if x is not None and y is not None:
            pyautogui.click(x, y, button=button)
        else:
            pyautogui.click(button=button)

        return {"status": "success", "x": x, "y": y, "button": button}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/keyboard/type")
async def type_text(text: str):
    """Type text using pyautogui"""
    try:
        pyautogui.write(text)
        return {"status": "success", "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
