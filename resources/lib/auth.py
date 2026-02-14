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
import http.cookiejar

try:
    from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler, HTTPCookieProcessor
    from urllib.parse import urlencode
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import Request, urlopen, build_opener, HTTPRedirectHandler, HTTPCookieProcessor, HTTPError, URLError
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
    try:
        os.makedirs(TOKEN_DIR, exist_ok=True)
    except OSError:
        return
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
    or empty dict if not authenticated (including expired tokens).
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
    """Check if we have a valid, non-expired authentication token."""
    token = _load_token()
    return token is not None and bool(token.get("jwt"))


def token_expires_soon(threshold=600):
    """
    Check if the stored token will expire within the given threshold.

    Args:
        threshold: Seconds before expiry to consider "soon" (default 10 min).

    Returns:
        True if token expires within threshold, False if healthy or no token.
    """
    token = _load_token()
    if not token:
        return False
    expires = token.get("expires", 0)
    if expires <= 0:
        return False  # Unknown expiry (manual tokens)
    return (expires - time.time()) < threshold


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


def login_with_credentials(username, password):
    """
    Log in with Cisco account username and password.

    Uses the Okta primary authentication API on id.cisco.com to get a
    sessionToken, then completes the SAML flow programmatically to
    obtain a RainFocus JWT.

    Args:
        username: Cisco account email address
        password: Account password

    Returns:
        tuple of (success: bool, message: str)
    """
    username = username.strip()
    password = password.strip()
    if not username or not password:
        return False, "Username and password are required"

    # Step 1: Okta primary authentication -> sessionToken
    _log("Authenticating with Cisco identity...")
    authn_body = json.dumps({
        "username": username,
        "password": password,
    }).encode("utf-8")

    authn_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    req = Request("https://id.cisco.com/api/v1/authn",
                  data=authn_body, headers=authn_headers)

    try:
        resp = urlopen(req, timeout=20)
        authn_data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = ""
        try:
            error_data = json.loads(e.read().decode("utf-8"))
            error_body = error_data.get("errorSummary", "")
        except Exception:
            pass
        if e.code == 401:
            return False, "Invalid username or password"
        return False, "Authentication failed: {}".format(error_body or e.code)
    except (URLError, Exception) as e:
        return False, "Connection error: {}".format(str(e))

    status = authn_data.get("status", "")
    session_token = authn_data.get("sessionToken", "")

    if status == "MFA_REQUIRED":
        return False, ("Multi-factor authentication required. "
                       "Use the QR/Phone sign-in method instead.")
    if status == "LOCKED_OUT":
        return False, "Account is locked. Please reset via id.cisco.com."
    if status == "PASSWORD_EXPIRED":
        return False, "Password expired. Please update at id.cisco.com."
    if status != "SUCCESS" or not session_token:
        return False, "Unexpected auth status: {}".format(status)

    _log("Okta auth successful, exchanging for RainFocus token...")

    # Step 2: Use sessionToken to complete SAML flow
    # The SAML URL with sessionToken auto-completes without user interaction
    saml_url = (
        "https://id.cisco.com/app/ciscoid_rainfocus_1/exkl5r8gqEFXndKvm5d6/sso/saml"
        "?sessionToken={}".format(session_token)
    )

    try:
        # Follow redirects manually to capture the ssoToken
        cj = http.cookiejar.CookieJar()
        opener = build_opener(
            HTTPCookieProcessor(cj),
            _NoRedirectHandler()
        )

        # Request SAML endpoint with sessionToken
        req2 = Request(saml_url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            resp2 = opener.open(req2, timeout=20)
            body2 = resp2.read().decode("utf-8", errors="replace")
        except HTTPError as e2:
            if e2.code in (301, 302, 303, 307, 308):
                body2 = ""
                location = e2.headers.get("Location", "")
            else:
                return False, "SAML request failed: HTTP {}".format(e2.code)

        # The SAML response is an HTML form that auto-submits to RainFocus
        # Extract the SAMLResponse from the form
        import re
        saml_match = re.search(
            r'name="SAMLResponse"\s+value="([^"]+)"', body2)
        relay_match = re.search(
            r'name="RelayState"\s+value="([^"]+)"', body2)

        if not saml_match:
            # Maybe we got redirected. Check for ssoToken in any redirect
            return False, ("Could not extract SAML response. "
                           "Try the QR/Phone sign-in method.")

        saml_response = saml_match.group(1)
        relay_state = relay_match.group(1) if relay_match else ""

        # Step 3: POST SAMLResponse to RainFocus ACS endpoint
        _log("Posting SAML assertion to RainFocus...")
        acs_url = "https://events.rainfocus.com/api/saml"
        acs_body = urlencode({
            "SAMLResponse": saml_response,
            "RelayState": relay_state,
        }).encode("utf-8")

        req3 = Request(acs_url, data=acs_body, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://id.cisco.com",
        })
        try:
            resp3 = opener.open(req3, timeout=20)
            body3 = resp3.read().decode("utf-8", errors="replace")
        except HTTPError as e3:
            if e3.code in (301, 302, 303, 307, 308):
                location3 = e3.headers.get("Location", "")
                # Check for ssoToken in redirect
                sso_match = re.search(r'ssoToken=([^&]+)', location3)
                if sso_match:
                    sso_token = sso_match.group(1)
                    return login_with_sso_token(sso_token)
            # Even if redirect, check cookies for global auth cookie
            pass

        # Step 4: Check if we got the global cookie from the SAML exchange
        for cookie in cj:
            if cookie.name == GLOBAL_COOKIE_NAME:
                _log("Got global auth cookie, exchanging for JWT...")
                return login_with_global_cookie(cookie.value)

        # Step 5: Try performLogin with any cookies we have
        cookie_header = "; ".join(
            "{}={}".format(c.name, c.value) for c in cj)
        if cookie_header:
            login_headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "rfWidgetId": AUTH_WIDGET_ID,
                "rfApiProfileId": AUTH_PROFILE_ID,
                "Cookie": cookie_header,
                "Origin": "https://ciscolive.cisco.com",
            }
            login_body = urlencode({"performLogin": "true"}).encode("utf-8")
            req4 = Request(LOGIN_URL, data=login_body, headers=login_headers)
            try:
                resp4 = urlopen(req4, timeout=20)
                data4 = json.loads(resp4.read().decode("utf-8"))
                jwt = _extract_jwt(data4)
                if jwt:
                    token_data = {
                        "method": "credentials",
                        "jwt": jwt,
                        "username": username,
                        "saved_at": time.time(),
                        "expires": time.time() + 86400,
                    }
                    _save_token(token_data)
                    return True, "Login successful"
            except Exception:
                pass

        return False, ("Authentication succeeded but token exchange failed. "
                       "Try the QR/Phone sign-in method.")

    except Exception as e:
        return False, "Token exchange error: {}".format(str(e))


class _NoRedirectHandler(HTTPRedirectHandler):
    """HTTP handler that doesn't follow redirects automatically."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(newurl, code, msg, headers, fp)


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
