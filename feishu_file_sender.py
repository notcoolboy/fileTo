#!/usr/bin/env python3
"""
Send a local file to a Feishu user/chat via the Feishu Bot API.

Usage:
  python3 feishu_file_sender.py /path/to/file.pdf --receive-id ou_xxx
  python3 feishu_file_sender.py /path/to/file.pdf --receive-id oc_xxx --chat

Credentials can be passed via:
  --app-id / --app-secret  (highest priority)
  FEISHU_APP_ID / FEISHU_APP_SECRET  env vars
  Auto-discovery from ~/.hermes/.env or ~/.openclaw/openclaw.json
"""

import argparse
import json
import os
import sys

import requests

FEISHU_API = "https://open.feishu.cn/open-apis"

# ----- file extension → Feishu file_type -----
EXT_TO_TYPE = {
    "pdf": "pdf",
    "doc": "doc", "docx": "doc",
    "xls": "xls", "xlsx": "xls",
    "ppt": "pptx", "pptx": "pptx",
    "zip": "zip", "rar": "zip", "7z": "zip", "gz": "zip", "tar": "zip",
    "txt": "txt", "csv": "csv", "json": "txt", "md": "txt",
    "jpg": "image", "jpeg": "image", "png": "image", "gif": "image",
    "webp": "image", "bmp": "image", "svg": "image",
    "mp3": "mp3", "wav": "mp3", "ogg": "mp3",
    "mp4": "mp4", "mov": "mp4", "avi": "mp4", "webm": "mp4",
}


def discover_credentials():
    """Try to find Feishu credentials from common config locations."""
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    if app_id and app_secret:
        return app_id, app_secret

    # Hermes .env
    for env_path in [
        os.path.expanduser("~/.hermes/.env"),
        os.path.expanduser("~/.hermes/data/.env"),
    ]:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    v = v.strip().strip('"').strip("'")
                    if k == "FEISHU_APP_ID":
                        app_id = v
                    elif k == "FEISHU_APP_SECRET":
                        app_secret = v
            if app_id and app_secret:
                return app_id, app_secret

    # OpenClaw config
    claw_config = os.path.expanduser("~/.openclaw/openclaw.json")
    if os.path.exists(claw_config):
        with open(claw_config) as f:
            cfg = json.load(f)
        feishu = cfg.get("channels", {}).get("feishu", {})
        if feishu.get("appId") and feishu.get("appSecret"):
            return feishu["appId"], feishu["appSecret"]

    return None, None


def get_tenant_token(app_id, app_secret):
    resp = requests.post(
        f"{FEISHU_API}/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=15,
    )
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Failed to get tenant token: {data}")
    return data["tenant_access_token"]


def upload_file(token, file_path, file_name=None):
    """Upload a file to Feishu. Returns file_key."""
    name = file_name or os.path.basename(file_path)
    ext = os.path.splitext(name)[1].lower().lstrip(".")
    file_type = EXT_TO_TYPE.get(ext, "stream")

    with open(file_path, "rb") as f:
        resp = requests.post(
            f"{FEISHU_API}/im/v1/files",
            headers={"Authorization": f"Bearer {token}"},
            data={"file_type": file_type, "file_name": name},
            files={"file": (name, f)},
            timeout=60,
        )
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"File upload failed: {data}")
    return data["data"]["file_key"]


def send_file_message(token, receive_id, file_key, is_chat=False):
    """Send a file message. receive_id_type is open_id or chat_id."""
    id_type = "chat_id" if is_chat else "open_id"
    resp = requests.post(
        f"{FEISHU_API}/im/v1/messages?receive_id_type={id_type}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "receive_id": receive_id,
            "msg_type": "file",
            "content": json.dumps({"file_key": file_key}),
        },
        timeout=15,
    )
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Send message failed: {data}")
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Send a local file via Feishu Bot"
    )
    parser.add_argument("file_path", help="Path to the file on disk")
    parser.add_argument(
        "--receive-id",
        help="Recipient open_id (DM) or chat_id (group)",
    )
    parser.add_argument(
        "--chat", action="store_true", help="receive_id is a chat_id (group)"
    )
    parser.add_argument("--app-id", help="Feishu App ID")
    parser.add_argument("--app-secret", help="Feishu App Secret")
    parser.add_argument(
        "--file-name",
        help="Override file name sent to Feishu",
    )
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"Error: file not found: {args.file_path}", file=sys.stderr)
        sys.exit(1)

    app_id = args.app_id
    app_secret = args.app_secret
    if not app_id or not app_secret:
        discovered_id, discovered_secret = discover_credentials()
        app_id = app_id or discovered_id
        app_secret = app_secret or discovered_secret

    if not app_id or not app_secret:
        print(
            "Error: Feishu App ID / Secret not found. "
            "Pass --app-id/--app-secret or set env vars.",
            file=sys.stderr,
        )
        sys.exit(1)

    receive_id = args.receive_id
    if not receive_id:
        print("Error: --receive-id is required.", file=sys.stderr)
        sys.exit(1)

    try:
        token = get_tenant_token(app_id, app_secret)
        file_key = upload_file(token, args.file_path, args.file_name)
        send_file_message(token, receive_id, file_key, is_chat=args.chat)
        print(f"✓ Sent: {args.file_path} → {receive_id}")
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
