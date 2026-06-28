# Mattermost ServiceDesk Ticket Bot

A Dockerized automation bot that converts Mattermost channel messages into ServiceDesk Plus tickets.

The bot is designed for internal support workflows where users report issues or submit requests in a Mattermost channel, and the support team needs those requests to be registered, tracked, classified, and followed up inside ServiceDesk Plus.

---

## Table of Contents

* [Overview](#overview)
* [What This Bot Does](#what-this-bot-does)
* [Architecture](#architecture)
* [Features](#features)
* [Project Structure](#project-structure)
* [Prerequisites](#prerequisites)
* [Install Docker on Ubuntu](#install-docker-on-ubuntu)
* [Clone the Repository](#clone-the-repository)
* [Environment Configuration](#environment-configuration)
* [Build and Run](#build-and-run)
* [Run with Docker Compose](#run-with-docker-compose)
* [Run with Docker CLI](#run-with-docker-cli)
* [Offline Server Deployment](#offline-server-deployment)
* [Attachment Handling](#attachment-handling)
* [State Management](#state-management)
* [Logs and Monitoring](#logs-and-monitoring)
* [Troubleshooting](#troubleshooting)
* [Security Notes](#security-notes)
* [Git Workflow](#git-workflow)
* [Maintenance](#maintenance)

---

## Overview

Mattermost ServiceDesk Ticket Bot listens to a specific Mattermost channel and creates a ServiceDesk Plus request for every new valid message.

It helps teams move support requests from chat-based communication into a structured ticketing system.

The bot can:

* Read new messages from a Mattermost channel
* Detect the sender
* Create a ServiceDesk Plus ticket
* Set requester, technician, group, category, subcategory, item, and priority
* Download files from Mattermost
* Upload and attach files to the created ServiceDesk ticket
* Send a confirmation message back to Mattermost
* Prevent duplicate ticket creation after restart

---

## What This Bot Does

When a user sends a message in the configured Mattermost channel:

1. The bot receives the new post.
2. It reads the Mattermost user information.
3. It uses the user's email as the ServiceDesk requester.
4. It creates a ServiceDesk ticket with a fixed subject.
5. It uses only the user's message as the ticket description.
6. If the message has files, it downloads them from Mattermost.
7. It uploads the files to ServiceDesk Plus.
8. It links the uploaded files to the created ticket.
9. It sends a confirmation message back to Mattermost.

---

## Architecture

```text
+-----------------------+
|  Mattermost Channel   |
+----------+------------+
           |
           | Read new posts and file IDs
           v
+-----------------------+
|  Ticket Bot           |
|  Python + Docker      |
+----------+------------+
           |
           | Create ticket
           v
+-----------------------+
|  ServiceDesk Plus     |
+----------+------------+
           |
           | Upload and attach files
           v
+-----------------------+
|  Ticket with metadata |
|  and attachments      |
+-----------------------+
```

---

## Features

### Mattermost Integration

* Polls a configured Mattermost channel
* Reads new channel posts
* Resolves sender details through Mattermost API
* Ignores bot messages to prevent loops
* Supports text messages
* Supports file attachments
* Sends confirmation messages through Mattermost Incoming Webhook

### ServiceDesk Plus Integration

* Creates requests through ServiceDesk Plus API
* Uses Mattermost user email as requester email
* Assigns a configured technician
* Sets default support group
* Sets ticket category, subcategory, and item
* Sets priority
* Uploads and links attachments to the created request

### Reliability

* Persistent state file
* Duplicate post detection
* Old message skip on first run
* Restart-safe execution
* Detailed logs
* Docker restart policy support

### Deployment

* Dockerized Python application
* Supports Docker Compose
* Supports direct Docker CLI execution
* Supports online and offline server deployment
* Uses environment variables for configuration

---

## Project Structure

```text
mattermost-ticket-bot/
├── app/
│   ├── bot.py              # Main bot application
│   └── state.json          # Runtime state file, ignored by Git
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose service definition
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment file
├── .gitignore              # Git ignore rules
└── README.md               # Project documentation
```

---

## Prerequisites

Before running the bot, make sure you have:

* A Linux server
* Docker installed
* Docker Compose plugin or legacy docker-compose
* Network access from the bot server to Mattermost
* Network access from the bot server to ServiceDesk Plus
* A Mattermost bot token
* A Mattermost channel ID
* A Mattermost incoming webhook URL
* A ServiceDesk Plus API key

---

## Install Docker on Ubuntu

> Skip this section if Docker is already installed.

### 1. Remove old Docker packages

```bash
sudo apt-get remove -y docker docker-engine docker.io containerd runc || true
```

### 2. Install required packages

```bash
sudo apt-get update

sudo apt-get install -y \
  ca-certificates \
  curl \
  gnupg
```

### 3. Add Docker GPG key

```bash
sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

### 4. Add Docker repository

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 5. Install Docker Engine and Compose plugin

```bash
sudo apt-get update

sudo apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

### 6. Enable and start Docker

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

### 7. Verify Docker installation

```bash
docker --version
docker compose version
sudo docker run hello-world
```

### Optional: run Docker without sudo

```bash
sudo usermod -aG docker $USER
```

Log out and log back in for the group change to apply.

---

## Clone the Repository

```bash
git clone https://github.com/example-org/mattermost-ticket-bot.git
cd mattermost-ticket-bot
```

If the project is already on the server:

```bash
cd ~/mattermost-ticket-bot
```

---

## Environment Configuration

Create the `.env` file:

```bash
cp .env.example .env
```

Edit it:

```bash
nano .env
```

Example configuration:

```env
# Mattermost
MATTERMOST_URL=https://mattermost.example.com
MATTERMOST_TOKEN=replace_with_mattermost_bot_token
CHANNEL_ID=replace_with_mattermost_channel_id
WEBHOOK_URL=https://mattermost.example.com/hooks/replace_with_webhook

# ServiceDesk Plus
SDP_BASE=https://servicedesk.example.com/api/v3
SDP_API_KEY=replace_with_servicedesk_api_key

# Ticket Defaults
FIXED_TICKET_SUBJECT=Support request from Mattermost
BOT_TECHNICIAN_EMAIL=technician@example.com

DEFAULT_GROUP=Support Group
DEFAULT_CATEGORY=General Support
DEFAULT_SUBCATEGORY=Application
DEFAULT_ITEM=Internal Tool
DEFAULT_PRIORITY=Normal
DEFAULT_IMPACT=

# Runtime
CHECK_INTERVAL=5
IGNORE_EMAIL=

# Attachments
ENABLE_SDP_ATTACHMENTS=true
MAX_ATTACHMENT_MB=20
KEEP_FAILED_ATTACHMENTS=true

# State Management
STATE_FILE=/app/state.json
SKIP_OLD_MESSAGES_ON_FIRST_RUN=true
PROCESSED_POST_LIMIT=1000
```

---

## Environment Variables

| Variable                         | Required | Description                                    |
| -------------------------------- | -------: | ---------------------------------------------- |
| `MATTERMOST_URL`                 |      Yes | Base URL of Mattermost                         |
| `MATTERMOST_TOKEN`               |      Yes | Mattermost bot token                           |
| `CHANNEL_ID`                     |      Yes | Mattermost channel ID to monitor               |
| `WEBHOOK_URL`                    |      Yes | Incoming webhook URL for confirmation messages |
| `SDP_BASE`                       |      Yes | ServiceDesk Plus API v3 base URL               |
| `SDP_API_KEY`                    |      Yes | ServiceDesk Plus API key                       |
| `FIXED_TICKET_SUBJECT`           |      Yes | Fixed subject for created tickets              |
| `BOT_TECHNICIAN_EMAIL`           |      Yes | Technician email assigned to tickets           |
| `DEFAULT_GROUP`                  |      Yes | Default ServiceDesk group                      |
| `DEFAULT_CATEGORY`               | Optional | Default category                               |
| `DEFAULT_SUBCATEGORY`            | Optional | Default subcategory                            |
| `DEFAULT_ITEM`                   | Optional | Default item                                   |
| `DEFAULT_PRIORITY`               | Optional | Default priority                               |
| `DEFAULT_IMPACT`                 | Optional | Default impact                                 |
| `CHECK_INTERVAL`                 | Optional | Polling interval in seconds                    |
| `IGNORE_EMAIL`                   | Optional | Email address to ignore                        |
| `ENABLE_SDP_ATTACHMENTS`         | Optional | Enable attachment upload                       |
| `MAX_ATTACHMENT_MB`              | Optional | Maximum file size in MB                        |
| `KEEP_FAILED_ATTACHMENTS`        | Optional | Keep files if upload fails                     |
| `STATE_FILE`                     | Optional | Path to runtime state file                     |
| `SKIP_OLD_MESSAGES_ON_FIRST_RUN` | Optional | Skip previous channel messages on first run    |
| `PROCESSED_POST_LIMIT`           | Optional | Maximum processed post IDs to keep             |

---

## Build and Run

### Build Docker image

```bash
docker build -t mattermost-ticket-bot:latest .
```

### Run container

```bash
docker rm -f mattermost-ticket-bot 2>/dev/null || true

docker run -d \
  --name mattermost-ticket-bot \
  --restart always \
  --env-file .env \
  -v ./app:/app \
  mattermost-ticket-bot:latest
```

### Check container status

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### View logs

```bash
docker logs -f mattermost-ticket-bot
```

---

## Run with Docker Compose

Example `docker-compose.yml`:

```yaml
version: "3.8"

services:
  ticket-bot:
    image: mattermost-ticket-bot:latest
    container_name: mattermost-ticket-bot
    restart: always
    env_file:
      - .env
    volumes:
      - ./app:/app
```

Start:

```bash
docker compose up -d
```

Check logs:

```bash
docker compose logs -f
```

For older servers with legacy Compose:

```bash
docker-compose up -d
docker-compose logs -f
```

---

## Run with Docker CLI

Direct Docker CLI run is useful when Docker Compose is not available.

```bash
docker rm -f mattermost-ticket-bot 2>/dev/null || true

docker run -d \
  --name mattermost-ticket-bot \
  --restart always \
  --env-file .env \
  -v ./app:/app \
  mattermost-ticket-bot:latest
```

If `.env` changes, recreate the container:

```bash
docker rm -f mattermost-ticket-bot

docker run -d \
  --name mattermost-ticket-bot \
  --restart always \
  --env-file .env \
  -v ./app:/app \
  mattermost-ticket-bot:latest
```

A simple `docker restart` does not reload `.env` values.

---

## Offline Server Deployment

If the production server does not have internet access, do not run commands that require pulling images or installing packages from the internet.

### 1. Build the image on a connected machine

```bash
docker build -t mattermost-ticket-bot:latest .
```

### 2. Export the image

```bash
docker save mattermost-ticket-bot:latest -o mattermost-ticket-bot.tar
```

### 3. Copy image and project files to the offline server

```bash
scp mattermost-ticket-bot.tar user@server:/opt/
scp -r mattermost-ticket-bot user@server:/opt/
```

### 4. Load the image on the offline server

```bash
docker load -i /opt/mattermost-ticket-bot.tar
```

### 5. Start the container on the offline server

```bash
cd /opt/mattermost-ticket-bot

docker rm -f mattermost-ticket-bot 2>/dev/null || true

docker run -d \
  --name mattermost-ticket-bot \
  --restart always \
  --env-file .env \
  -v ./app:/app \
  mattermost-ticket-bot:latest
```

---

## Attachment Handling

The bot supports file attachments sent in Mattermost messages.

Attachment flow:

1. Mattermost message contains one or more file IDs.
2. Bot downloads the files through the Mattermost API.
3. Bot uploads the files to ServiceDesk Plus.
4. Bot links the uploaded files to the created request.
5. Bot cleans temporary files after upload.

Relevant variables:

```env
ENABLE_SDP_ATTACHMENTS=true
MAX_ATTACHMENT_MB=20
KEEP_FAILED_ATTACHMENTS=true
```

The upload endpoint used by ServiceDesk Plus may vary by environment. This implementation uses the request upload endpoint discovered from the ServiceDesk web UI:

```text
/api/v3/requests/_upload
```

If attachment upload fails, check the logs for:

```text
[ATTACHMENTS DETECTED]
[FILE DOWNLOADED]
[SDP REAL UPLOAD TRY]
[SDP REAL UPLOAD OK]
[SDP ATTACH LINK TRY]
[SDP ATTACH UPLOADED]
```

---

## State Management

The bot stores runtime state in:

```text
/app/state.json
```

The state file keeps:

* last processed Mattermost timestamp
* processed Mattermost post IDs

This prevents duplicate tickets after restart.

Recommended values:

```env
STATE_FILE=/app/state.json
SKIP_OLD_MESSAGES_ON_FIRST_RUN=true
PROCESSED_POST_LIMIT=1000
```

Do not commit `state.json` to Git.

---

## Logs and Monitoring

View live logs:

```bash
docker logs -f mattermost-ticket-bot
```

Expected startup logs:

```text
[STATE LOADED] last_timestamp=...
BOT ID: ...
Bot Started...
[CONFIG] enable_sdp_attachments=True
[CONFIG] category=...
[CONFIG] subcategory=...
[CONFIG] item=...
[CONFIG] priority=Normal
```

Successful ticket creation:

```text
[POST RECEIVED] post_id=... username=... email=... files=0
[SDP CREATE] status=201
[TICKET CREATED] id=...
```

Successful ticket creation with attachment:

```text
[POST RECEIVED] post_id=... username=... email=... files=1
[ATTACHMENTS DETECTED] count=1
[FILE DOWNLOADED] filename=...
[SDP CREATE] status=201
[TICKET CREATED] id=...
[SDP REAL UPLOAD OK] filename=...
[SDP ATTACH UPLOADED] ticket_id=...
```

---

## Troubleshooting

### Docker is not installed

Check:

```bash
docker --version
```

If Docker is missing, install it using the Docker installation section above.

---

### Docker Compose is not available

Check:

```bash
docker compose version
```

If this does not work, try legacy Compose:

```bash
docker-compose --version
```

If neither exists, run the bot with Docker CLI.

---

### Bot starts but creates tickets for old messages

Check:

```env
SKIP_OLD_MESSAGES_ON_FIRST_RUN=true
STATE_FILE=/app/state.json
```

If needed, stop the bot and inspect the state file:

```bash
docker stop mattermost-ticket-bot
cat app/state.json
```

---

### Environment changes are not applied

Docker does not reload `--env-file` values on restart.

Recreate the container:

```bash
docker rm -f mattermost-ticket-bot

docker run -d \
  --name mattermost-ticket-bot \
  --restart always \
  --env-file .env \
  -v ./app:/app \
  mattermost-ticket-bot:latest
```

---

### Ticket fields are empty

Check `.env`:

```bash
grep -n "DEFAULT_GROUP\|DEFAULT_CATEGORY\|DEFAULT_SUBCATEGORY\|DEFAULT_ITEM\|DEFAULT_PRIORITY" .env
```

Then recreate the container.

---

### Priority is empty

Check:

```env
DEFAULT_PRIORITY=Normal
```

Then recreate the container.

---

### Attachments are not uploaded

Check:

```env
ENABLE_SDP_ATTACHMENTS=true
```

Then check logs:

```bash
docker logs -f mattermost-ticket-bot
```

Look for:

```text
[ATTACHMENTS DETECTED]
[FILE DOWNLOADED]
[SDP REAL UPLOAD TRY]
[SDP REAL UPLOAD OK]
[SDP ATTACH UPLOADED]
```

---

### ServiceDesk returns Invalid Input

This usually means one of the configured values does not exist in ServiceDesk Plus.

Check these fields in the ServiceDesk UI:

* Group
* Category
* Subcategory
* Item
* Priority
* Technician

Then update `.env` and recreate the container.

---

### Mattermost user email is empty

The bot needs the Mattermost user's email to create the ServiceDesk requester.

Check:

* Mattermost bot token permissions
* Mattermost user profile
* API access to `/api/v4/users/{user_id}`

---

## Security Notes

Never commit secrets to Git.

Do not commit:

* `.env`
* API keys
* Mattermost bot tokens
* Webhook URLs
* ServiceDesk API keys
* runtime state files
* logs
* temporary files

Recommended `.gitignore`:

```gitignore
.env
.env.*
!.env.example
app/state.json
state.json
*.log
__pycache__/
*.pyc
*.bak
tmp/
temp/
```

Use dedicated service accounts and rotate credentials if exposed.

---

## Git Workflow

Check repository status:

```bash
git status
```

Stage safe files:

```bash
git add README.md .env.example .gitignore Dockerfile docker-compose.yml requirements.txt app/bot.py
```

Make sure `.env` is not staged:

```bash
git status
```

If `.env` was staged accidentally:

```bash
git rm --cached .env
```

Commit:

```bash
git commit -m "docs: rewrite setup and deployment guide"
```

Push:

```bash
git push
```

---

## Maintenance

Recommended update flow:

```bash
docker stop mattermost-ticket-bot

cp app/bot.py app/bot.py.bak.$(date +%F-%H%M%S)

python3 -m py_compile app/bot.py

docker start mattermost-ticket-bot

docker logs -f mattermost-ticket-bot
```

After every change:

1. Validate Python syntax
2. Start the bot
3. Check logs
4. Send a test Mattermost message
5. Verify ticket creation
6. Verify ticket fields
7. Verify attachments if needed

---

## License

This project is intended for internal automation workflows. Add a license file if the repository will be shared publicly.

---

## Maintainer

Maintained by the internal infrastructure or support automation team.
