"""Yoto MYO card uploader — OAuth Device Flow + REST API."""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLIENT_ID = "iUxGeKw2MTYaNvUK7bU6GNhao6uhnQVl"
AUTH_DOMAIN = "https://login.yotoplay.com"
API_BASE = "https://api.yotoplay.com"
SCOPE = "profile offline_access"
AUDIENCE = "https://api.yotoplay.com"

TOKEN_PATH = Path.home() / ".config" / "ebook-to-yoto" / "yoto-tokens.json"


# ---------------------------------------------------------------------------
# Token storage
# ---------------------------------------------------------------------------

def _save_tokens(access_token: str, refresh_token: str) -> None:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps({
        "access_token": access_token,
        "refresh_token": refresh_token,
    }))


def _load_tokens() -> Optional[tuple[str, str]]:
    if not TOKEN_PATH.exists():
        return None
    try:
        data = json.loads(TOKEN_PATH.read_text())
        return data["access_token"], data["refresh_token"]
    except Exception:
        return None


def _is_expired(access_token: str) -> bool:
    try:
        payload = access_token.split(".")[1]
        # Fix base64 padding
        payload += "=" * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        # Expired if within 60 seconds of expiry
        return decoded["exp"] * 1000 < (time.time() * 1000 + 60_000)
    except Exception:
        return True


def _refresh(refresh_token: str) -> tuple[str, str]:
    resp = requests.post(
        f"{AUTH_DOMAIN}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": refresh_token,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return data["access_token"], data.get("refresh_token", refresh_token)


# ---------------------------------------------------------------------------
# Auth — Device Flow
# ---------------------------------------------------------------------------

def authenticate() -> str:
    """
    Return a valid access token, refreshing or re-authenticating as needed.
    On first run, opens a browser-friendly URL for the user to approve.
    """
    tokens = _load_tokens()
    if tokens:
        access_token, refresh_token = tokens
        if not _is_expired(access_token):
            return access_token
        print("Refreshing Yoto token...")
        try:
            access_token, refresh_token = _refresh(refresh_token)
            _save_tokens(access_token, refresh_token)
            return access_token
        except Exception:
            print("Refresh failed, re-authenticating...")

    # Device Flow
    resp = requests.post(
        f"{AUTH_DOMAIN}/oauth/device/code",
        data={
            "client_id": CLIENT_ID,
            "scope": SCOPE,
            "audience": AUDIENCE,
        },
    )
    resp.raise_for_status()
    device = resp.json()

    print("\nTo authorise ebook-to-yoto with your Yoto account:")
    print(f"  1. Visit: {device['verification_uri_complete']}")
    print(f"  2. Enter code: {device['user_code']}")
    print("  3. Press Enter here once approved.")
    input()

    interval = device.get("interval", 5)
    deadline = time.time() + device.get("expires_in", 300)

    while time.time() < deadline:
        token_resp = requests.post(
            f"{AUTH_DOMAIN}/oauth/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device["device_code"],
                "client_id": CLIENT_ID,
                "audience": AUDIENCE,
            },
        )
        if token_resp.status_code == 200:
            data = token_resp.json()
            _save_tokens(data["access_token"], data["refresh_token"])
            print("Authenticated successfully.")
            return data["access_token"]

        error = token_resp.json().get("error", "")
        if error == "slow_down":
            interval += 5
        elif error not in ("authorization_pending",):
            raise RuntimeError(f"Auth failed: {error}")
        time.sleep(interval)

    raise RuntimeError("Device code expired. Please try again.")


# ---------------------------------------------------------------------------
# Upload a single track
# ---------------------------------------------------------------------------

def upload_track(mp3_path: Path, title: str, icon_path: Optional[Path], access_token: str) -> dict:
    """
    Upload one MP3 to Yoto and return the transcoded track info dict
    ready to be added to a playlist.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 1: Get upload URL
    resp = requests.get(f"{API_BASE}/media/transcode/audio/uploadUrl", headers=headers)
    resp.raise_for_status()
    upload_info = resp.json()["upload"]
    upload_url = upload_info["uploadUrl"]
    upload_id = upload_info["uploadId"]

    # Step 2: PUT the MP3
    with mp3_path.open("rb") as f:
        put_resp = requests.put(upload_url, data=f, headers={"Content-Type": "audio/mpeg"})
    put_resp.raise_for_status()

    # Step 3: Poll for transcoding
    for _ in range(60):
        tc_resp = requests.get(
            f"{API_BASE}/media/upload/{upload_id}/transcoded?loudnorm=false",
            headers=headers,
        )
        if tc_resp.status_code == 200:
            tc = tc_resp.json().get("transcode", {})
            if tc.get("transcodedSha256"):
                break
        time.sleep(2)
    else:
        raise RuntimeError(f"Transcoding timed out for {mp3_path.name}")

    info = tc.get("transcodedInfo", {})
    sha = tc["transcodedSha256"]

    # Step 4: Upload icon if present
    icon_hash = None
    if icon_path and icon_path.exists():
        icon_hash = _upload_icon(icon_path, access_token)

    display = {}
    if icon_hash:
        display["icon16x16"] = f"yoto:#{icon_hash}"

    return {
        "sha": sha,
        "title": title,
        "duration": info.get("duration"),
        "fileSize": info.get("fileSize"),
        "channels": info.get("channels"),
        "format": info.get("format"),
        "display": display,
    }


def _upload_icon(icon_path: Path, access_token: str) -> Optional[str]:
    """Upload a 16x16 PNG icon and return its hash."""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(f"{API_BASE}/media/upload/imageUrl", headers=headers)
        if resp.status_code != 200:
            return None
        upload_info = resp.json().get("upload", {})
        upload_url = upload_info.get("uploadUrl")
        upload_id = upload_info.get("uploadId")
        if not upload_url:
            return None

        with icon_path.open("rb") as f:
            requests.put(upload_url, data=f, headers={"Content-Type": "image/png"})

        # Poll for processing
        for _ in range(20):
            tc_resp = requests.get(
                f"{API_BASE}/media/upload/{upload_id}/transcoded",
                headers=headers,
            )
            if tc_resp.status_code == 200:
                sha = tc_resp.json().get("transcode", {}).get("transcodedSha256")
                if sha:
                    return sha
            time.sleep(1)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Create / update a MYO card
# ---------------------------------------------------------------------------

def create_card(title: str, tracks: list[dict], access_token: str) -> str:
    """Create a MYO card with all tracks. Returns the content ID."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    chapters = []
    total_duration = 0
    total_size = 0

    for i, track in enumerate(tracks):
        key = f"{i + 1:02d}"
        display = track.get("display", {})
        chapter = {
            "key": key,
            "title": track["title"],
            "overlayLabel": str(i + 1),
            "tracks": [
                {
                    "key": key,
                    "title": track["title"],
                    "trackUrl": f"yoto:#{track['sha']}",
                    "duration": track["duration"],
                    "fileSize": track["fileSize"],
                    "channels": track["channels"],
                    "format": track["format"],
                    "type": "audio",
                    "overlayLabel": str(i + 1),
                    "display": display,
                }
            ],
            "display": display,
        }
        chapters.append(chapter)
        total_duration += track.get("duration") or 0
        total_size += track.get("fileSize") or 0

    payload = {
        "title": title,
        "content": {"chapters": chapters},
        "metadata": {
            "media": {
                "duration": total_duration,
                "fileSize": total_size,
                "readableFileSize": round(total_size / 1024 / 1024 * 10) / 10,
            }
        },
    }

    resp = requests.post(f"{API_BASE}/content", json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json().get("contentId") or resp.json().get("id", "unknown")
