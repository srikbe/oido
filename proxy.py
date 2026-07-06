#!/usr/bin/env python3
"""
Oído — Anthropic API proxy
Forwards POST /api/claude → https://api.anthropic.com/v1/messages
Reads ANTHROPIC_API_KEY from a .env file in the same directory.
No third-party packages required (stdlib only).
"""

import json
import os
import ssl
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT    = 3457
API_URL = 'https://api.anthropic.com/v1/messages'


# ── .env loader ───────────────────────────────────────────────────────────────

def load_env(path):
    """Parse KEY=VALUE lines from a .env file; ignores comments and blanks."""
    result = {}
    try:
        with open(path) as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, val = line.partition('=')
                result[key.strip()] = val.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return result


_root   = os.path.dirname(os.path.abspath(__file__))
_dotenv = load_env(os.path.join(_root, '.env'))
API_KEY = _dotenv.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_API_KEY', '')


# ── CORS headers ──────────────────────────────────────────────────────────────

CORS_HEADERS = {
    'Access-Control-Allow-Origin':  '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
}


# ── Request handler ───────────────────────────────────────────────────────────

class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        status = args[1] if len(args) > 1 else '?'
        print(f'  {self.command:6} {self.path}  →  {status}')

    # ── helpers ──

    def _send_cors(self):
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)

    def _json_reply(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self._send_cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)

    def _forward_reply(self, status, body_bytes):
        self.send_response(status)
        self._send_cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body_bytes)

    # ── CORS preflight ──

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    # ── Proxy ──

    def do_POST(self):
        if self.path != '/api/claude':
            self._json_reply(404, {'error': {'message': f'Unknown path: {self.path}'}})
            return

        if not API_KEY:
            self._json_reply(500, {
                'error': {
                    'message': (
                        'ANTHROPIC_API_KEY is not set. '
                        'Create a .env file in the project root with:\n'
                        'ANTHROPIC_API_KEY=sk-ant-...'
                    )
                }
            })
            return

        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length)

        upstream = urllib.request.Request(
            API_URL,
            data=body,
            headers={
                'Content-Type':      'application/json',
                'x-api-key':         API_KEY,
                'anthropic-version': '2023-06-01',
            },
            method='POST',
        )

        ctx = ssl.create_default_context()  # verifies TLS cert

        try:
            with urllib.request.urlopen(upstream, context=ctx) as resp:
                self._forward_reply(resp.status, resp.read())
        except urllib.error.HTTPError as exc:
            self._forward_reply(exc.code, exc.read())
        except Exception as exc:
            self._json_reply(502, {'error': {'message': f'Proxy error: {exc}'}})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print()
    print('  Oído — Anthropic API proxy')
    print('  ──────────────────────────')

    if API_KEY:
        masked = API_KEY[:14] + '…' + API_KEY[-4:]
        print(f'  ✓  API key   {masked}')
    else:
        print('  ✗  API key   NOT FOUND')
        print('     Create .env in the project root:')
        print('     ANTHROPIC_API_KEY=sk-ant-...')

    print(f'  ✓  Listening  http://localhost:{PORT}')
    print(f'     /api/claude  →  {API_URL}')
    print()

    server = HTTPServer(('localhost', PORT), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Proxy stopped.')
