"""Run with: uv run main.py"""
import uvicorn

from app.main import app

if __name__ == "__main__":
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=2004))
    app.state.server = server  # lets the idle watcher shut down gracefully
    server.run()
