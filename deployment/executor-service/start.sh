#!/bin/bash

# Start Xvfb (X Virtual Frame Buffer)
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!

# Wait for Xvfb to start
sleep 2

# Start Fluxbox window manager
echo "Starting Fluxbox..."
fluxbox &
FLUXBOX_PID=$!

# Start x11vnc for remote access
echo "Starting x11vnc..."
x11vnc -display :99 -forever -shared -rfbport 5900 -nopw &
VNC_PID=$!

# Wait for services to start
sleep 2

# Start the Python application
echo "Starting Executor Service..."
python3 executor_service.py

# If the Python app exits, kill background processes
kill $XVFB_PID $FLUXBOX_PID $VNC_PID
