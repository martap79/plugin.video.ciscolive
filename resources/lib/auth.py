"""
Cisco Live authentication module.

Handles authentication with the RainFocus platform used by Cisco Live.
The site uses Cisco SSO (SAML) which sets a global RainFocus cookie,
then exchanges for a JWT via the login API.

Auth flow:
1. SAML login via browser sets ssoToken on callback redirect
2. Exchange ssoToken for JWT via POST /api/login
3. Use JWT in rfAuthToken header for all authenticated API calls

Auth methods:
- SSO token exchange (from browser login flow callback)
- Global cookie exchange (fallback if ssoToken not available)
- Manual JWT entry (user copies token from browser dev tools)

The JWT token is stored locally and used until it expires.
"""

import json
import os
import time

try:
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import Request, urlopen, HTTPError, URLError
    from urllib import urlencode

try:
    import xbmcaddon
    import xbmcvfs
    import xbmc
    _ADDON = xbmcaddon.Addon()
    TOKEN_DIR = xbmcvfs.translatePath(_ADDON.getAddonInfo("profile"))
except Exception:
    TOKEN_DIR = os.path.join(os.path.dirname(__file__), ".auth")

from . import rainfocus

TOKEN_FILE = os.path.join(TOKEN_DIR, "auth.json")

# RainFocus API endpoints
LOGIN_URL = "https://events.rainfocus.com/api/login"

# SAML SSO profile for Cisco Live on-demand
SSO_PROFILE_ID = "saml:jUN6c3A5jl"

# Widget/profile IDs for authenticated requests
AUTH_WIDGET_ID = "M7n14I8sz0pklW1vybwVRdKrgdREj8sR"
AUTH_PROFILE_ID = "HEedDIRblcZk7Ld3KHm1T0VUtZog9eG9"

# Global cookie name used by RainFocus for SSO
GLOBAL_COOKIE_NAME = "1586783053443001TvYm"


def _log(msg):
    """Log a message, using xbmc.log if available."""
    try:
        xbmc.log("CiscoLive.auth: {}".format(msg), xbmc.LOGINFO)
    except Exception:
        pass


def _load_token():
    """Load saved authentication token."""
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
        # Check if token has an expiry
        if data.get("expires", 0) > 0 and time.time() > data["expires"]:
            _log("Token expired")
            return None
        return data
    except Exception:
        return None


def _save_token(token_data):
    """Save authentication token to disk."""
    os.makedirs(TOKEN_DIR, exist_ok=True)
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f)
    except Exception:
        pass


def clear_token():
    """Remove saved authentication token."""
    try:
        os.remove(TOKEN_FILE)
    except Exception:
        pass


def get_auth_headers():
    """
    Get authentication headers for RainFocus API calls.

    Returns dict with rfAuthToken, rfWidgetId, rfApiProfileId if authenticated,
    or empty dict if not authenticated.
    """
    token = _load_token()
    if not token:
        return {}

    jwt = token.get("jwt", "")
    if not jwt:
        return {}

    return {
        "rfAuthToken": jwt,
        "rfWidgetId": AUTH_WIDGET_ID,
        "rfApiProfileId": AUTH_PROFILE_ID,
    }


def is_authenticated():
    """Check if we have a valid authentication token."""
    token = _load_token()
    return token is not None and bool(token.get("jwt"))


def login_with_sso_token(sso_token, sso_profile_id=None):
    """
    Exchange an SSO token from the SAML callback for a JWT.

    After the user completes SAML login, RainFocus redirects to our callback
    with ?ssoToken=xxx&ssoProfileId=xxx. We exchange this for a JWT.

    Args:
        sso_token: The ssoToken from the callback URL
        sso_profile_id: The ssoProfileId (defaults to our known SSO profile)

    Returns:
        tuple of (success: bool, message: str)
    """
    sso_token = sso_token.strip()
    if not sso_token:
        return False, "SSO token is empty"

    profile_id = sso_profile_id or SSO_PROFILE_ID

    params = {
        "ssoToken": sso_token,
        "ssoProfileId": profile_id,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "rfWidgetId": AUTH_WIDGET_ID,
        "rfApiProfileId": AUTH_PROFILE_ID,
        "Origin": "https://ciscolive.cisco.com",
        "Referer": "https://www.ciscolive.com/on-demand/on-demand-library.html",
    }

    body = urlencode(params).encode("utf-8")
    req = Request(LOGIN_URL, data=body, headers=headers)

    try:
        resp = urlopen(req, timeout=20)
        data = json.loads(resp.read().decode("utf-8"))
        _log("SSO login response keys: {}".format(list(data.keys())))

        jwt = _extract_jwt(data)
        if jwt:
            token_data = {
                "method": "sso_token",
                "jwt": jwt,
                "saved_at": time.time(),
                "expires": time.time() + 86400,  # 24h, conservative estimate
            }
            _save_token(token_data)
            return True, "Login successful via SSO"

        # Check for error
        error = data.get("error", data.get("message", ""))
        if error:
            return False, "SSO login failed: {}".format(error)

        return False, "SSO login returned no token. Response: {}".format(
            json.dumps(data)[:200])

    except HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        return False, "SSO login HTTP error {}: {}".format(e.code, body_text)

    except (URLError, Exception) as e:
        return False, "SSO login error: {}".format(str(e))


def login_with_global_cookie(cookie_value):
    """
    Exchange the global RainFocus cookie for a JWT.

    The cookie '1586783053443001TvYm' is set on .rainfocus.com after SAML login.
    We can POST it to the login API to get a JWT.

    Args:
        cookie_value: The value of the 1586783053443001TvYm cookie

    Returns:
        tuple of (success: bool, message: str)
    """
    cookie_value = cookie_value.strip()
    if not cookie_value:
        return False, "Cookie value is empty"

    params = {
        "performLogin": "true",
        GLOBAL_COOKIE_NAME: cookie_value,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "rfWidgetId": AUTH_WIDGET_ID,
        "rfApiProfileId": AUTH_PROFILE_ID,
        "Origin": "https://ciscolive.cisco.com",
        "Referer": "https://www.ciscolive.com/on-demand/on-demand-library.html",
    }

    body = urlencode(params).encode("utf-8")
    req = Request(LOGIN_URL, data=body, headers=headers)

    try:
        resp = urlopen(req, timeout=20)
        data = json.loads(resp.read().decode("utf-8"))
        _log("Cookie login response keys: {}".format(list(data.keys())))

        jwt = _extract_jwt(data)
        if jwt:
            token_data = {
                "method": "global_cookie",
                "jwt": jwt,
                "saved_at": time.time(),
                "expires": time.time() + 86400,
            }
            _save_token(token_data)
            return True, "Login successful via cookie"

        error = data.get("error", data.get("message", ""))
        if error:
            return False, "Cookie login failed: {}".format(error)

        return False, "Cookie login returned no token"

    except HTTPError as e:
        return False, "Cookie login HTTP error {}".format(e.code)

    except (URLError, Exception) as e:
        return False, "Cookie login error: {}".format(str(e))


def login_with_token(jwt_token):
    """
    Save a manually provided JWT token.

    The user can get this from their browser:
    1. Log in to ciscolive.com/on-demand
    2. Open browser dev tools > Network tab
    3. Look for requests with rfAuthToken header, or
    4. Check Application > Local Storage for JWT values

    Args:
        jwt_token: The JWT/auth token value

    Returns:
        tuple of (success: bool, message: str)
    """
    jwt_token = jwt_token.strip()
    if not jwt_token:
        return False, "Token is empty"

    # Validate by making a test search request
    valid, msg = validate_token(jwt_token)
    if valid:
        token_data = {
            "method": "manual",
            "jwt": jwt_token,
            "saved_at": time.time(),
            "expires": 0,  # Manual tokens: unknown expiry
        }
        _save_token(token_data)
        return True, "Token saved and validated"

    # If validation is inconclusive (network error etc), save anyway
    if "error" in msg.lower() or "timeout" in msg.lower():
        token_data = {
            "method": "manual",
            "jwt": jwt_token,
            "saved_at": time.time(),
            "expires": 0,
        }
        _save_token(token_data)
        return True, "Token saved (could not fully validate: {})".format(msg)

    return False, msg


def validate_token(jwt_token):
    """
    Test a JWT token by making a simple search request.

    Args:
        jwt_token: The JWT token to validate

    Returns:
        tuple of (valid: bool, message: str)
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "rfWidgetId": AUTH_WIDGET_ID,
        "rfApiProfileId": AUTH_PROFILE_ID,
        "rfAuthToken": jwt_token,
        "Origin": "https://ciscolive.cisco.com",
        "Referer": "https://www.ciscolive.com/on-demand/on-demand-library.html",
    }

    # Simple search to test auth
    body = urlencode({
        "type": "session",
        "size": "1",
        "from": "0",
    }).encode("utf-8")

    search_url = "https://events.rainfocus.com/api/search"
    req = Request(search_url, data=body, headers=headers)

    try:
        resp = urlopen(req, timeout=15)
        data = json.loads(resp.read().decode("utf-8"))

        # Check for auth-related errors
        if data.get("responseCode") == "107":
            return False, "Token is invalid or expired"

        # If we get section data, the token works
        sections = data.get("sectionList", [])
        if sections:
            return True, "Token is valid"

        # Some response but no sections - might still be OK
        return True, "Token accepted (no results to verify)"

    except HTTPError as e:
        if e.code in (401, 403):
            return False, "Token is invalid or expired (HTTP {})".format(e.code)
        return False, "Validation error (HTTP {})".format(e.code)

    except (URLError, Exception) as e:
        return False, "Validation network error: {}".format(str(e))


def get_video_url(session_id, video_id):
    """
    Get a playable video URL for a session.

    With authentication, the search API already returns video URLs as
    Brightcove video IDs in videos[].url. We resolve those via the
    Brightcove Playback API.

    Falls back to direct Brightcove resolution (unauthenticated).

    Args:
        session_id: RainFocus session ID
        video_id: Brightcove video ID

    Returns:
        tuple of (url, mime_type) or (None, None)
    """
    # Always resolve via Brightcove - the video_id IS a Brightcove ID
    from . import brightcove
    return brightcove.best_stream(video_id, prefer_hls=True)


def _extract_jwt(data):
    """
    Extract JWT token from a login API response.

    The login API may return the token in different fields depending
    on the auth method used.
    """
    # Direct token fields
    for key in ("rfAuthToken", "authToken", "token", "jwt", "access_token"):
        val = data.get(key)
        if val and isinstance(val, str) and len(val) > 20:
            return val

    # Nested in user/attendee data
    for container_key in ("user", "attendee", "data", "result"):
        container = data.get(container_key)
        if isinstance(container, dict):
            for key in ("rfAuthToken", "authToken", "token", "jwt"):
                val = container.get(key)
                if val and isinstance(val, str) and len(val) > 20:
                    return val

    # Check cookie-like headers in response
    # Some APIs return tokens in a cookie-style field
    cookie_val = data.get("cookie", "")
    if cookie_val and "rfjwt=" in str(cookie_val):
        import re
        m = re.search(r'rfjwt=([^;]+)', str(cookie_val))
        if m:
            return m.group(1)

    return None
