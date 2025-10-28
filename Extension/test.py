#!/usr/bin/env python3
"""
Simple Test Server for Tube Snatcher Extension
Just a basic health check endpoint to test connectivity
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

app = FastAPI(title="Tube Snatcher Test Server")

# More permissive CORS for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/")
async def root():
    """Root endpoint for health check"""
    response = Response(
        content='{"status": "healthy", "timestamp": "' + datetime.now().isoformat() + '", "message": "Test server is running!"}',
        media_type="application/json"
    )
    # Add CSP header to allow extension connections
    response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self' http://127.0.0.1:2004 http://localhost:2004 chrome-extension://*;"
    return response

@app.get("/")
async def root():
    """Root endpoint"""
    response = Response(
        content='{"message": "Tube Snatcher Test Server is running!"}',
        media_type="application/json"
    )
    # Add CSP header to allow extension connections
    response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self' http://127.0.0.1:2004 http://localhost:2004 chrome-extension://*;"
    return response



@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for debugging"""
    print(f"[{datetime.now()}] {request.method} {request.url}")
    print(f"  Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    print(f"  Response: {response.status_code}")
    return response

if __name__ == "__main__":
    print("Starting Test Server on http://127.0.0.1:2004")
    print("Health check: http://127.0.0.1:2004/")
    print("Press Ctrl+C to stop")
    uvicorn.run(app, host="127.0.0.1", port=2004)
