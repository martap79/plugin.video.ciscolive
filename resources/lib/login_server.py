"""
Browser-based login flow for Cisco Live on-demand.

Implements a two-screen authentication pattern common in TV/Kodi addons:

1. Plugin starts a local HTTP server on localhost
2. Shows a URL (and QR code) on the Kodi screen for the user
3. User opens the URL on their phone/computer browser
4. The local server redirects them to Cisco SSO (SAML) login
5. After SAML login, RainFocus redirects to our callback with ssoToken
6. Server exchanges ssoToken for JWT via RainFocus login API
7. Plugin detects JWT received, stores it, shows success

The ssoToken approach works because RainFocus appends ?ssoToken=xxx to
whatever URL is specified in the rfparam parameter of the SAML request.
This is a server-side token exchange - no cross-domain cookie issues.

Fallback: manual JWT token entry if ssoToken flow fails.
"""

import json
import os
import socket
import threading
import time

try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
except ImportError:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

try:
    from urllib.parse import parse_qs, urlparse, urlencode
except ImportError:
    from urlparse import parse_qs, urlparse
    from urllib import urlencode

from . import auth

# SAML SSO configuration
SAML_BASE_URL = (
    "https://events.rainfocus.com/ev:cisco/clondemand/samlRequest"
)
SSO_PROFILE_ID = "saml:jUN6c3A5jl"

# How long to wait for the user to complete login (seconds)
LOGIN_TIMEOUT = 300  # 5 minutes

# ---------------------------------------------------------------------------
# HTML pages
# ---------------------------------------------------------------------------

PAGE_LANDING = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cisco Live - Kodi Login</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .card {{
            background: #16213e;
            border-radius: 16px;
            padding: 40px;
            max-width: 480px;
            width: 90%;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }}
        h1 {{ color: #049fd9; margin-bottom: 16px; font-size: 24px; }}
        p {{ color: #aab; line-height: 1.6; margin-bottom: 20px; }}
        .btn {{
            display: inline-block;
            background: #049fd9;
            color: #fff;
            text-decoration: none;
            padding: 14px 32px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            transition: background 0.2s;
        }}
        .btn:hover {{ background: #0380b0; }}
        .step {{ color: #7a8; font-size: 14px; margin-top: 24px; }}
        .logo {{ font-size: 48px; margin-bottom: 16px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">&#127909;</div>
        <h1>Cisco Live for Kodi</h1>
        <p>Click the button below to sign in with your Cisco account.
           After logging in, you'll be automatically connected to Kodi.</p>
        <a href="{saml_url}" class="btn">Sign in with Cisco</a>
        <p class="step">Sign in with your Cisco account to access the full video library</p>
    </div>
</body>
</html>"""

PAGE_SUCCESS = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cisco Live - Login Complete</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .card {{
            background: #16213e;
            border-radius: 16px;
            padding: 40px;
            max-width: 480px;
            width: 90%;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }}
        h1 {{ color: #2ecc71; margin-bottom: 16px; }}
        p {{ color: #aab; line-height: 1.6; margin-bottom: 12px; }}
        .logo {{ font-size: 64px; margin-bottom: 16px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">&#10004;&#65039;</div>
        <h1>Login Complete!</h1>
        <p>Your Cisco account has been linked to Kodi.</p>
        <p>You can close this browser tab and return to Kodi.</p>
    </div>
</body>
</html>"""

PAGE_FAILURE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cisco Live - Login Issue</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .card {{
            background: #16213e;
            border-radius: 16px;
            padding: 40px;
            max-width: 520px;
            width: 90%;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }}
        h1 {{ color: #e67e22; margin-bottom: 16px; font-size: 22px; }}
        p {{ color: #aab; line-height: 1.6; margin-bottom: 16px; font-size: 15px; }}
        .error-detail {{ color: #e74c3c; font-size: 13px; background: #0f1a30;
                         padding: 10px; border-radius: 6px; margin: 12px 0; word-break: break-all; }}
        .btn {{
            display: inline-block;
            background: #049fd9;
            color: #fff;
            text-decoration: none;
            padding: 12px 28px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: background 0.2s;
            margin: 6px;
        }}
        .btn:hover {{ background: #0380b0; }}
        .btn:disabled {{ background: #555; cursor: not-allowed; }}
        .manual {{ margin-top: 24px; padding-top: 20px; border-top: 1px solid #2a3a5e; }}
        .manual label {{ color: #8a9; display: block; margin-bottom: 8px; font-size: 14px; }}
        .manual input {{
            width: 100%;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #3a4a6e;
            background: #0f1a30;
            color: #eee;
            font-family: monospace;
            font-size: 13px;
        }}
        .manual .btn {{ margin-top: 12px; font-size: 14px; padding: 10px 24px; }}
        .logo {{ font-size: 48px; margin-bottom: 16px; }}
        .success {{ color: #2ecc71; font-size: 18px; display: none; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo" id="logo">&#9888;&#65039;</div>
        <h1 id="heading">SSO Token Not Received</h1>
        <p id="msg">The automatic login redirect didn't include the expected token.
           This can happen if the SSO provider blocks the redirect.</p>
        <p class="error-detail" id="detail">{error_detail}</p>

        <p>You can try again or enter a token manually:</p>
        <a href="{retry_url}" class="btn">Try Again</a>

        <div class="manual">
            <label>Paste your JWT / auth token from browser dev tools:</label>
            <input type="text" id="manualToken" placeholder="eyJ..." />
            <button class="btn" onclick="sendManual()">Send Token</button>
            <p class="success" id="success">&#10004; Token sent to Kodi! You can close this tab.</p>
        </div>
    </div>

    <script>
        function sendManual() {{
            var token = document.getElementById('manualToken').value.trim();
            if (!token) return;

            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/token', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onload = function() {{
                if (xhr.status === 200) {{
                    document.getElementById('success').style.display = 'block';
                    document.getElementById('logo').textContent = '\\u2705';
                    document.getElementById('heading').textContent = 'Login Complete!';
                    document.getElementById('heading').style.color = '#2ecc71';
                    document.getElementById('msg').textContent =
                        'Token sent to Kodi. You can close this tab.';
                }} else {{
                    alert('Failed to send token. Try again.');
                }}
            }};
            xhr.onerror = function() {{
                alert('Could not reach Kodi server. Make sure you\\'re on the same network.');
            }};
            xhr.send(JSON.stringify({{token: token}}));
        }}
    </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class LoginCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the login callback server."""

    def log_message(self, fmt, *args):
        """Suppress default logging."""
        pass

    def _cors_headers(self):
        """Add CORS headers to allow cross-origin requests."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        if self.server.is_rate_limited(self.client_address[0]):
            self.send_error(429, "Too many requests")
            return
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/" or path == "/login":
            # Landing page with "Sign in with Cisco" button
            saml_url = self._build_saml_url()
            html = PAGE_LANDING.format(saml_url=saml_url)
            self._send_html(html)

        elif path == "/callback":
            # SAML callback - extract ssoToken from query params
            self._handle_callback(query)

        elif path == "/status":
            # Poll endpoint: Kodi plugin checks if token was received
            if self.server.received_jwt:
                self._send_json({"status": "ok", "jwt": self.server.received_jwt})
            else:
                self._send_json({"status": "waiting"})

        elif path == "/health":
            self._send_json({"status": "running"})

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests (manual token submission)."""
        if self.server.is_rate_limited(self.client_address[0]):
            self.send_error(429, "Too many requests")
            return
        path = urlparse(self.path).path

        if path == "/token":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            try:
                data = json.loads(body)
                token = data.get("token", "").strip()
                if token:
                    # Store as JWT directly (manual entry)
                    self.server.received_jwt = token
                    self.send_response(200)
                    self._cors_headers()
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"status": "ok"}).encode("utf-8"))
                else:
                    self.send_response(400)
                    self._cors_headers()
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"error": "empty token"}).encode("utf-8"))
            except (ValueError, KeyError):
                self.send_response(400)
                self._cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"error": "invalid json"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_callback(self, query):
        """
        Handle the SAML callback redirect.

        After SAML login, RainFocus redirects to:
        http://LOCAL_IP:PORT/callback?ssoToken=xxx&ssoProfileId=xxx

        We extract the ssoToken and exchange it for a JWT server-side.
        """
        sso_token = query.get("ssoToken", [None])[0]
        sso_profile_id = query.get("ssoProfileId", [None])[0]

        if sso_token:
            # Exchange ssoToken for JWT
            success, msg = auth.login_with_sso_token(sso_token, sso_profile_id)
            if success:
                # Get the stored JWT
                auth_headers = auth.get_auth_headers()
                jwt = auth_headers.get("rfAuthToken", "")
                if jwt:
                    self.server.received_jwt = jwt
                    self._send_html(PAGE_SUCCESS)
                    return
                else:
                    # Saved but couldn't retrieve - unlikely
                    self.server.received_jwt = "__sso_success__"
                    self._send_html(PAGE_SUCCESS)
                    return
            else:
                # SSO token exchange failed - show failure page with manual fallback
                login_url = "/login"
                html = PAGE_FAILURE.format(
                    error_detail="SSO token exchange failed: {}".format(msg),
                    retry_url=login_url,
                )
                self._send_html(html)
                return

        # No ssoToken in callback URL - show failure page with manual fallback
        # This might happen if RainFocus doesn't append the token
        raw_query = "&".join("{}={}".format(k, v[0]) for k, v in query.items()) if query else "(none)"
        login_url = "/login"
        html = PAGE_FAILURE.format(
            error_detail="No ssoToken in callback. Received params: {}".format(raw_query),
            retry_url=login_url,
        )
        self._send_html(html)

    def _build_saml_url(self):
        """Build the SAML login URL with rfparam pointing to our callback."""
        callback_url = "http://{}:{}/callback".format(
            self.server.local_ip, self.server.server_port)

        params = {
            "rfapp": "events",
            "ssoProfileId": SSO_PROFILE_ID,
            "rfparam": callback_url,
        }
        return "{}?{}".format(SAML_BASE_URL, urlencode(params))

    def _send_html(self, html):
        """Send an HTML response."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_json(self, data):
        """Send a JSON response."""
        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


# ---------------------------------------------------------------------------
# Server class
# ---------------------------------------------------------------------------

class LoginServer(HTTPServer):
    """HTTP server with slots for received JWT and cancellation."""

    # Rate limiting: max requests per IP within window
    RATE_LIMIT = 20
    RATE_WINDOW = 60  # seconds

    def __init__(self, server_address, handler_class, local_ip="localhost"):
        self.received_jwt = None
        self.local_ip = local_ip
        self._shutdown_event = threading.Event()
        self._request_log = {}  # ip -> list of timestamps
        HTTPServer.__init__(self, server_address, handler_class)

    def is_rate_limited(self, client_ip):
        """Check if a client IP has exceeded the rate limit."""
        now = time.time()
        timestamps = self._request_log.get(client_ip, [])
        # Prune old entries
        timestamps = [t for t in timestamps if now - t < self.RATE_WINDOW]
        self._request_log[client_ip] = timestamps
        if len(timestamps) >= self.RATE_LIMIT:
            return True
        timestamps.append(now)
        return False

    def request_stop(self):
        """Signal the server to stop (non-blocking, no deadlock)."""
        self._shutdown_event.set()

    @property
    def should_stop(self):
        return self._shutdown_event.is_set()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _find_free_port():
    """Find an available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _get_local_ip():
    """Get the local network IP address (for display to user)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def run_login_flow(timeout=LOGIN_TIMEOUT):
    """
    Start the login server and return connection info.

    Does NOT block. Returns immediately so the caller can show UI
    (QR code window) and poll for the token.

    Args:
        timeout: Max seconds the server will run (used by server thread).

    Returns:
        tuple of (login_url, same_device_url, port, server, server_thread)
    """
    port = _find_free_port()
    local_ip = _get_local_ip()

    server = LoginServer((local_ip, port), LoginCallbackHandler, local_ip)
    server.timeout = 1  # handle_request() returns after 1 second max

    # Start server in background thread
    server_thread = threading.Thread(
        target=_serve_until_done, args=(server, timeout))
    server_thread.daemon = True
    server_thread.start()

    # Build the URLs
    login_url = "http://{}:{}/login".format(local_ip, port)
    same_device_url = "http://localhost:{}/login".format(port)

    return login_url, same_device_url, port, server, server_thread


def _serve_until_done(server, timeout):
    """
    Serve requests until JWT received, shutdown requested, or timeout.

    This runs in a daemon thread. Uses handle_request() with server.timeout=1
    so it never blocks for more than 1 second, enabling clean shutdown.
    """
    start = time.time()
    while (not server.received_jwt
           and not server.should_stop
           and (time.time() - start) < timeout):
        try:
            server.handle_request()
        except Exception:
            break

    # Keep serving briefly after JWT received (for the success page to load)
    if server.received_jwt and not server.should_stop:
        end = time.time() + 3
        while time.time() < end and not server.should_stop:
            try:
                server.handle_request()
            except Exception:
                break

    # Clean up the socket
    try:
        server.server_close()
    except Exception:
        pass


def get_token_from_server(server):
    """Check if the server has received a JWT token."""
    return server.received_jwt


def stop_server(server):
    """
    Stop the login server cleanly without blocking.

    Uses request_stop() to signal the server thread to exit, rather than
    server.shutdown() which can deadlock if called from the wrong thread.
    """
    try:
        server.request_stop()
    except Exception:
        pass
    # Also close the socket to unblock any pending handle_request()
    try:
        server.server_close()
    except Exception:
        pass
