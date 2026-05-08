---
name: feishu-file-sender
description: Send local files (e.g. from Desktop, Downloads) to users via Feishu DM or group chat. Use when the user asks to send, share, or transfer a file through Feishu.
version: 1.0.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [feishu, file, messaging]
    category: communication
---

# Feishu File Sender

Send a file from this Mac to a Feishu user or group chat.

## When to use

- User says "send this file to me on Feishu" or "share xxx file via Feishu"
- User asks you to transfer a file from disk through Feishu
- User wants to push a document, image, PDF, etc. to a Feishu conversation

## Prerequisites

- Python 3 with `requests` library (`pip3 install requests`)
- Feishu bot app with permissions: `im:file`, `im:message`, `im:message:send_as_bot`, `im:resource`

## Script location

```
~/.hermes/scripts/feishu_file_sender.py
```

## How to send a file

### Step 1 — Locate the file
Use `ls` / `find` to verify the file exists at the path the user gave.
If they only gave a filename (e.g. "send 报告.pdf"), search common locations:
```
~/Desktop/  ~/Downloads/  ~/Documents/
```

### Step 2 — Determine the receive_id

**First, try the helper script** — it reads Hermes session files to find the
current conversation's sender:

```bash
python3 ~/.hermes/scripts/feishu_helper.py whoami
```

This prints `open_id=ou_xxx` and/or `chat_id=oc_xxx`. Use that value.

**If the helper doesn't work**, determine manually:

- **DM (single chat)**: Use the sender's `open_id`. Look in the incoming
  message metadata or the thread/session state for `sender_id` / `open_id`.
  As a last resort, ask: "What's your Feishu open_id?"

- **Group chat**: Use the `chat_id` and add the `--chat` flag.

### Step 3 — Run the sender script

```bash
python3 ~/.hermes/scripts/feishu_file_sender.py "/path/to/file" --receive-id "<open_id_or_chat_id>"
```

If sending to a group, add `--chat`:
```bash
python3 ~/.hermes/scripts/feishu_file_sender.py "/path/to/file" --receive-id "<chat_id>" --chat
```

### Step 4 — Report the result
Tell the user whether the file was sent successfully. If there's an error,
read the error message — it usually says what's wrong (bad token, missing
permission, file too large >30MB, etc.).

## Credentials

The script auto-discovers Feishu credentials from:
1. `FEISHU_APP_ID` / `FEISHU_APP_SECRET` env vars
2. `~/.hermes/.env`
3. `~/.openclaw/openclaw.json`

If none of these work, ask the user to run:
```bash
python3 ~/.hermes/scripts/feishu_file_sender.py /path/to/file \
  --app-id cli_xxx --app-secret xxx --receive-id ou_xxx
```

## Limitations

- Max file size: 30 MB
- The Feishu bot app must have `im:file` and `im:resource` permissions granted
- File types are auto-detected from extension; unusual types are sent as `stream`
