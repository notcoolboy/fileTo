# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context

This repo contains scripts that bridge Hermes Agent (on a Mac mini) with the Feishu Open API, enabling Hermes to send local files to users via Feishu — a capability neither Hermes nor OpenClaw has built-in.

Target machine: Mac mini running both Hermes and OpenClaw. This Windows directory is the staging area; files are meant to be transferred to the Mac.

## Deploy to Mac mini

```bash
mkdir -p ~/.hermes/scripts ~/.hermes/skills/feishu-file-sender
pip3 install requests
# Copy feishu_file_sender.py → ~/.hermes/scripts/
# Copy feishu_helper.py      → ~/.hermes/scripts/
# Copy SKILL.md              → ~/.hermes/skills/feishu-file-sender/
```

## Test after deploy

```bash
python3 ~/.hermes/scripts/feishu_helper.py whoami              # verify session reading works
python3 ~/.hermes/scripts/feishu_file_sender.py ~/Desktop/test.txt --receive-id ou_xxx  # test send
```

## Architecture

- `feishu_file_sender.py` — the main tool. Uploads a local file to Feishu's `im/v1/files`, gets a `file_key`, then sends it as a file message via `im/v1/messages`. Auto-discovers credentials from `~/.hermes/.env` or `~/.openclaw/openclaw.json`.
- `feishu_helper.py` — reads Hermes session JSON files to determine the current conversation's `open_id` / `chat_id`, so the agent knows who to send files to without asking the user.
- `hermes-skill-feishu-file/SKILL.md` — the Hermes Skill doc. Teaches Hermes when to trigger file sending and how to run the two scripts in sequence (helper → sender).

## Credential auto-discovery order

1. `--app-id` / `--app-secret` CLI args
2. `FEISHU_APP_ID` / `FEISHU_APP_SECRET` env vars
3. `~/.hermes/.env`
4. `~/.openclaw/openclaw.json` → `.channels.feishu`

## Required Feishu app permissions

`im:file`, `im:resource`, `im:message`, `im:message:send_as_bot`

## README

README.md 是用户面向文档，描述问题、解决方案、部署步骤。对外。

## Limits

File size ≤ 30 MB. File type is auto-mapped from extension; unrecognized extensions sent as `stream`.
