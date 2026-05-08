#!/usr/bin/env python3
"""
Helper: find Feishu receive_id from Hermes session data.
Hermes stores per-thread metadata — this script reads it so the agent
knows who to send files back to.

Usage:
  python3 feishu_helper.py whoami          # print open_id / chat_id for current session
  python3 feishu_helper.py list-sessions   # list recent sessions
"""

import json
import os
import sys


def find_hermes_data_dir():
    """Return the Hermes data directory, if it exists."""
    candidates = [
        os.path.expanduser("~/.hermes/data"),
        os.path.expanduser("~/.hermes"),
    ]
    for d in candidates:
        if os.path.isdir(d):
            return d
    return None


def list_sessions(data_dir):
    """Print recent sessions with their IDs."""
    sessions_dir = os.path.join(data_dir, "sessions")
    if not os.path.isdir(sessions_dir):
        print("No sessions directory found at", sessions_dir)
        return

    session_files = sorted(
        [f for f in os.listdir(sessions_dir) if f.endswith(".json")],
        key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
        reverse=True,
    )
    for f in session_files[:20]:
        path = os.path.join(sessions_dir, f)
        try:
            with open(path) as fh:
                data = json.load(fh)
            metadata = data.get("metadata", {})
            sender = metadata.get("sender_id", metadata.get("open_id", "unknown"))
            chat = metadata.get("chat_id", metadata.get("group_id", ""))
            print(f"  session={f[:-5]}  sender={sender}  chat={chat}")
        except Exception:
            print(f"  session={f[:-5]}  (unreadable)")


def whoami(data_dir):
    """Guess the current session's sender_id and chat_id.

    Strategy: look at the most recently modified session file.
    This works because the current conversation is being written to disk.
    """
    sessions_dir = os.path.join(data_dir, "sessions")
    if not os.path.isdir(sessions_dir):
        sessions_dir = data_dir

    best = None
    best_mtime = 0
    for entry in os.listdir(sessions_dir):
        if not entry.endswith(".json"):
            continue
        path = os.path.join(sessions_dir, entry)
        mtime = os.path.getmtime(path)
        if mtime > best_mtime:
            best_mtime = mtime
            best = path

    if not best:
        print("No session files found.")
        sys.exit(1)

    with open(best) as f:
        data = json.load(f)

    metadata = data.get("metadata", {})
    messages = data.get("messages", [])

    # Try metadata first
    sender_id = metadata.get("sender_id") or metadata.get("open_id")
    chat_id = metadata.get("chat_id") or metadata.get("group_id")
    channel = metadata.get("channel", "")

    # Fallback: scan messages for Feishu sender
    if not sender_id:
        for msg in reversed(messages):
            msg_meta = msg.get("metadata", {})
            if msg_meta.get("channel") in ("feishu", "lark"):
                sender_id = msg_meta.get("sender_id") or msg.get("from")
                chat_id = msg_meta.get("chat_id") or msg.get("chat_id")
                break

    if sender_id:
        print(f"open_id={sender_id}")
    if chat_id:
        print(f"chat_id={chat_id}")
    if channel:
        print(f"channel={channel}")

    if not sender_id and not chat_id:
        # Dump what we can find for debugging
        print("# Could not determine receive_id automatically.")
        print("# Dumping session keys for debugging:",
              json.dumps(list(data.keys())))
        if metadata:
            print("# metadata keys:", json.dumps(list(metadata.keys())))
        sys.exit(1)


if __name__ == "__main__":
    data_dir = find_hermes_data_dir()
    if not data_dir:
        print("Hermes data directory not found.", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "whoami"
    if cmd == "whoami":
        whoami(data_dir)
    elif cmd in ("list", "list-sessions"):
        list_sessions(data_dir)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Usage: feishu_helper.py [whoami|list-sessions]", file=sys.stderr)
        sys.exit(1)
