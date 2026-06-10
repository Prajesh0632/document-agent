"""
run_local.py
------------
Local development server — bypasses Azure Functions Core Tools entirely.
Uses Python's built-in HTTP server to expose the same POST /api/nin-extract
endpoint so you can test with curl or Postman without any Azure tooling.

Usage:
    python run_local.py
    python run_local.py --port 8080

Then test with curl:
    curl -X POST http://localhost:7071/api/nin-extract \
         -F "file=@/path/to/nin_document.jpg"

    curl http://localhost:7071/api/health
"""

import argparse
import io
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from email import message_from_bytes
from email.policy import HTTP as HTTP_POLICY

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from document_agent.pipeline import run_pipeline
from config import get_settings

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_local")
settings = get_settings()


class NINHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        logger.info(fmt, *args)

    # ── GET /api/health ──────────────────────────────────────────────────
    def do_GET(self):
        if self.path == "/api/health":
            self._send_text(f"OK - Environment: {settings.environment}")
        else:
            self._send_json({"error": "Not found"}, status=404)

    # ── POST /api/nin-extract ────────────────────────────────────────────
    def do_POST(self):
        if self.path != "/api/nin-extract":
            self._send_json({"error": "Not found"}, status=404)
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json(
                {"error": "Expected multipart/form-data with a 'file' field."},
                status=400,
            )
            return

        # Read body
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)

        # Parse multipart manually
        file_bytes, filename = self._parse_multipart(body, content_type)
        if file_bytes is None:
            self._send_json(
                {"error": "No 'file' field found in multipart body."},
                status=400,
            )
            return

        file_type = "pdf" if (filename or "").lower().endswith(".pdf") else "image"
        logger.info("Processing: %s (%d bytes, type=%s)", filename, len(file_bytes), file_type)

        try:
            final_state = run_pipeline("NIN", file_bytes, file_type=file_type)
            report      = final_state.get("report", {})
            status_code = 400 if report.get("status") == "rejected" else 200
            self._send_json(report, status=status_code)
        except Exception as exc:
            logger.error("Pipeline error: %s", exc, exc_info=True)
            self._send_json({"error": str(exc)}, status=500)

    # ── Helpers ──────────────────────────────────────────────────────────
    def _parse_multipart(self, body: bytes, content_type: str):
        """Extract the first 'file' field from a multipart/form-data body."""
        # Build a fake email message so email.message can parse it
        raw = f"Content-Type: {content_type}\r\n\r\n".encode() + body
        msg = message_from_bytes(raw, policy=HTTP_POLICY)
        for part in msg.walk():
            cd = part.get("Content-Disposition", "")
            if 'name="file"' in cd:
                filename = ""
                if 'filename="' in cd:
                    filename = cd.split('filename="')[1].split('"')[0]
                return part.get_payload(decode=True), filename
        return None, None

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str, status: int = 200):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description="NIN Document Agent — local dev server")
    parser.add_argument("--port", type=int, default=7071, help="Port to listen on (default: 7071)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()

    logger.info("Settings: %s", settings)
    logger.info("Starting local server on http://%s:%d", args.host, args.port)
    logger.info("Endpoints:")
    logger.info("  POST http://%s:%d/api/nin-extract   (multipart file upload)", args.host, args.port)
    logger.info("  GET  http://%s:%d/api/health", args.host, args.port)

    server = HTTPServer((args.host, args.port), NINHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped.")


if __name__ == "__main__":
    main()
