"""
Executable entrypoint to start the ManiGit Research Web Server.

Usage:
    python -m web.backend.server [--port 8000]
"""

import argparse
import sys
from web.backend.app import create_app
from web.backend.service import ManiGitWebService


def main():
    parser = argparse.ArgumentParser(description="Start ManiGit Web Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()

    service = ManiGitWebService()
    server = create_app(service=service, port=args.port)

    print(f"ManiGit Web Interface running at http://127.0.0.1:{args.port}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()


if __name__ == "__main__":
    main()
