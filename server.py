#!/usr/bin/env python3
"""
Static file server + Mailchimp contact form handler.
API key lives here, server-side only — never sent to the browser.
"""
import json
import hashlib
import os
import sys
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

MAILCHIMP_API_KEY = os.environ.get("MAILCHIMP_API_KEY", "")
MAILCHIMP_LIST_ID = "6a76b55c63"

if not MAILCHIMP_API_KEY:
    print("ERROR: MAILCHIMP_API_KEY environment variable is not set.")
    sys.exit(1)

MAILCHIMP_DC   = MAILCHIMP_API_KEY.split("-")[-1]
MAILCHIMP_BASE = f"https://{MAILCHIMP_DC}.api.mailchimp.com/3.0"


def subscriber_hash(email: str) -> str:
    return hashlib.md5(email.lower().strip().encode()).hexdigest()


def mc_request(method: str, path: str, data: dict | None = None):
    import base64
    url = f"{MAILCHIMP_BASE}{path}"
    token = base64.b64encode(f"anystring:{MAILCHIMP_API_KEY}".encode()).decode()
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


class Handler(SimpleHTTPRequestHandler):

    def do_OPTIONS(self):
        self._cors()

    def do_POST(self):
        if self.path != "/api/contact":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            self._json(400, {"error": "Invalid JSON"})
            return

        name    = body.get("name", "").strip()
        company = body.get("company", "").strip()
        email   = body.get("email", "").strip().lower()
        message = body.get("message", "").strip()

        if not all([name, email, message]):
            self._json(400, {"error": "Missing required fields"})
            return

        parts = name.split(" ", 1)
        fname = parts[0]
        lname = parts[1] if len(parts) > 1 else ""
        sub_hash = subscriber_hash(email)

        # Upsert subscriber — status_if_new leaves existing subscribers unchanged
        status, resp = mc_request(
            "PUT",
            f"/lists/{MAILCHIMP_LIST_ID}/members/{sub_hash}",
            {
                "email_address": email,
                "status_if_new": "subscribed",
                "merge_fields": {"FNAME": fname, "LNAME": lname},
            },
        )

        if status not in (200, 201):
            detail = resp.get("detail", "Unknown error")
            print(f"[Mailchimp] Member upsert failed ({status}): {detail}")
            self._json(502, {"error": f"Mailchimp error: {detail}"})
            return

        # Add a note with company + message
        note = f"Company: {company}\n\n{message}" if company else message
        note_status, note_resp = mc_request(
            "POST",
            f"/lists/{MAILCHIMP_LIST_ID}/members/{sub_hash}/notes",
            {"note": note},
        )

        if note_status not in (200, 201):
            # Non-fatal — subscriber was added, note just didn't save
            print(f"[Mailchimp] Note failed ({note_status}): {note_resp.get('detail')}")

        self._json(200, {"ok": True})

    def _cors(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json(self, code: int, data: dict):
        payload = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()}  {fmt % args}")


if __name__ == "__main__":
    port = 8080
    server = HTTPServer(("", port), Handler)
    print(f"Server running at http://localhost:{port}")
    server.serve_forever()
