# 📘 README.md

```markdown
# 🎫 Mattermost → ServiceDesk Auto Ticket Bot

A Python automation bot that converts Mattermost messages into tickets in **ManageEngine ServiceDesk Plus (SDP)**.

---

## 🚀 Overview

This bot continuously listens to a Mattermost channel and automatically creates a support ticket in SDP whenever a user sends a message.

### 🔄 Flow

1. User sends message in Mattermost
2. Bot reads message via API
3. Extracts user email
4. Sends request to SDP API
5. SDP resolves user via Active Directory
6. Ticket is created
7. Bot sends ticket ID back to Mattermost

---

## 🧠 Architecture

```

Mattermost → Python Bot → SDP API → Ticket Created
↓
Webhook Reply

````

---

## ⚙️ Requirements

### 🐍 Software

- Python 3.8+
- pip

### 📦 Python Libraries

```bash
pip install requests python-dotenv
````

---

## 🔐 Configuration

Create a `.env` file in the project root:

```env
MATTERMOST_URL=https://your-mattermost-url
MATTERMOST_TOKEN=your_token
CHANNEL_ID=your_channel_id

WEBHOOK_URL=your_webhook_url

SDP_BASE=https://your-sdp-url/api/v3
SDP_API_KEY=your_api_key

IGNORE_EMAIL=test@example.com

DEFAULT_TECHNICIAN_EMAIL=tech@example.com
DEFAULT_GROUP=Your Group Name
DEFAULT_CATEGORY=Your Group Name
DEFAULT_SUBCATEGORY=Your Sub Name
DEFAULT_ITEM=Your Item
CHECK_INTERVAL=5
```

---

## 📁 Project Structure

```
.
├── bot.py
├── .env
├── requirements.txt
└── README.md
```

---

## ▶️ Running the Bot

```bash
python bot.py
```

---

## 🧩 Full Code with Explanation

### 🔹 Imports

```python
import requests
import time
import logging
import json
import os
from typing import Dict, List, Any
```

* `requests` → API calls
* `time` → loop delay
* `logging` → logs
* `json` → payload encoding
* `os` → read environment variables

---

### 🔹 Environment Variables

```python
MATTERMOST_URL = os.getenv("MATTERMOST_URL")
MATTERMOST_API = f"{MATTERMOST_URL}/api/v4"
```

* Loads Mattermost base URL from `.env`

---

### 🔹 Session Setup

```python
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {MATTERMOST_TOKEN}",
    "Content-Type": "application/json"
})
```

* Reusable HTTP session for better performance

---

### 🔹 Fetch Messages

```python
def get_posts(since):
```

* Calls Mattermost API
* Gets messages after a timestamp
* Prevents duplicate processing

---

### 🔹 Get User Info

```python
def get_user(user_id):
```

* Fetches user details
* Extracts email (critical for SDP)

---

### 🔹 Identify Bot (Prevent Loop)

```python
def get_my_user_id():
```

* Prevents bot from responding to itself

---

### 🔹 Create Ticket (Core Logic)

```python
def create_ticket(user, message):
```

#### 🔥 Key Points:

* Uses `email_id` → SDP resolves AD user
* Uses `input_data` → required by SDP API
* Sets:

  * requester
  * technician
  * group
  * category

#### Payload Example:

```json
{
  "request": {
    "subject": "message",
    "requester": {
      "email_id": "user@example.com"
    }
  }
}
```

---

### 🔹 Send Notification

```python
def notify(username, ticket_id):
```

* Sends ticket ID back to Mattermost via webhook

---

### 🔹 Main Loop

```python
while True:
```

* Polls Mattermost every X seconds
* Processes new messages only
* Creates tickets
* Sends response

---

## 🛡️ Security Best Practices

* Never commit `.env`
* Add `.env` to `.gitignore`

```bash
echo ".env" >> .gitignore
```

* Rotate tokens regularly
* Use restricted API keys

---

## 🧪 Testing

1. Run bot
2. Send message in channel
3. Check:

   * Ticket created in SDP
   * Ticket ID appears in Mattermost

---

## 🧱 Common Errors

| Error                  | Cause                | Fix                   |
| ---------------------- | -------------------- | --------------------- |
| 400 input_data missing | Wrong request format | Use `data=input_data` |
| requester not found    | Email not in AD      | Sync AD               |
| category required      | Missing field        | Add category          |
| auth failed            | Wrong API key        | Fix token             |

---

## 🚀 Future Improvements

* Prevent duplicate tickets
* Add Redis queue
* Dockerize service
* Add retry mechanism
* Thread reply instead of new message

---

## 🐳 (Optional) Docker

```dockerfile
FROM python:3.10

WORKDIR /app
COPY . .

RUN pip install requests python-dotenv

CMD ["python", "bot.py"]
```

---

## 👨‍💻 Author

Automation built for internal IT workflow optimization 🚀

```

---
