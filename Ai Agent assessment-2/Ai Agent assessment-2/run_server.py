"""
Interactive Web Application & API Server Runner.
Launches the FastAPI server with live dashboard at http://localhost:8000

Usage:
  python run_server.py
  python run_server.py --port 8080 --reload
"""

import sys
import os
import argparse
import uvicorn

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Run the Applied Agentic AI Web Dashboard & API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--reload", "-r", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    print("=" * 80)
    print("      APPLIED AGENTIC AI - ASSIGNMENT 2 INTERACTIVE WEB DASHBOARD")
    print("=" * 80)
    print(f"[*] Starting server at: http://{args.host}:{args.port}")
    print(f"[*] API Documentation: http://{args.host}:{args.port}/docs")
    print(f"[*] Interactive UI   : http://{args.host}:{args.port}/")
    print("=" * 80 + "\n")

    uvicorn.run("api.server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
