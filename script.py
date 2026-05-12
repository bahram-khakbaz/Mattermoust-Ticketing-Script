# -*- coding: utf-8 -*-
import requests
import time
import logging
import json
import os
from typing import Dict, List, Any

# ======================
# CONFIG (FROM ENV)
# ======================

MATTERMOST_URL = os.getenv("MATTERMOST_URL")
MATTERMOST_API = f"{MATTERMOST_URL}/api/v4"

MATTERMOST_TOKEN = os.getenv("MATTERMOST_TOKEN")
SDP_API_KEY = os.getenv("SDP_API_KEY")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CHANNEL_ID = os.getenv("CHANNEL_ID")

IGNORE_EMAIL = os.getenv("IGNORE_EMAIL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 5))

SDP_BASE = os.getenv("SDP_BASE")

DEFAULT_TECHNICIAN_EMAIL = os.getenv("DEFAULT_TECHNICIAN_EMAIL")
DEFAULT_GROUP = os.getenv("DEFAULT_GROUP")
DEFAULT_CATEGORY = os.getenv("DEFAULT_CATEGORY")
DEFAULT_SUBCATEGORY = os.getenv("DEFAULT_SUBCATEGORY")
DEFAULT_ITEM = os.getenv("DEFAULT_ITEM")

# ======================
# LOGGING
# ======================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("bot")

# ======================
# SESSION
# ======================

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {MATTERMOST_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
})

sdp_headers = {
    "AUTHTOKEN": SDP_API_KEY,
    "Accept": "application/json"
}

# ======================
# STATE
# ======================

last_timestamp = 0
BOT_USER_ID = None

# ======================
# MATTERMOST
# ======================

def get_posts(since: int) -> List[Dict[str, Any]]:
    try:
        url = f"{MATTERMOST_API}/channels/{CHANNEL_ID}/posts"
        res = session.get(url, params={"since": since})

        if res.status_code != 200:
            logger.error(res.text)
            return []

        return list(res.json().get("posts", {}).values())

    except Exception as e:
        logger.error(f"[MM ERROR] {e}")
        return []

# ======================
# USER
# ======================

def get_user(user_id: str) -> Dict:
    try:
        res = session.get(f"{MATTERMOST_API}/users/{user_id}")
        if res.status_code != 200:
            return {}
        return res.json()
    except Exception as e:
        logger.error(f"[USER ERROR] {e}")
        return {}

# ======================
# BOT ID
# ======================

def get_my_user_id():
    try:
        res = session.get(f"{MATTERMOST_API}/users/me")
        if res.status_code == 200:
            return res.json().get("id")
    except Exception as e:
        logger.error(e)
    return None

# ======================
# CREATE TICKET
# ======================

def create_ticket(user: Dict, message: str):

    email = user.get("email")

    if not email:
        return None

    payload = {
        "request": {
            "subject": (message or "No Subject")[:120],
            "description": message or "EMPTY",

            "requester": {
                "email_id": email
            },

            "technician": {
                "email_id": DEFAULT_TECHNICIAN_EMAIL
            },

            "category": {
                "name": DEFAULT_CATEGORY
            },

            "group": {
                "name": DEFAULT_GROUP
            },

            "impact": {"name": "Medium"},
            "subcategory": {"name": DEFAULT_SUBCATEGORY},
            "item": {"name": DEFAULT_ITEM}
        }
    }

    try:
        res = requests.post(
            f"{SDP_BASE}/requests",
            headers=sdp_headers,
            data={
                "input_data": json.dumps(payload)
            },
            timeout=30
        )

        logger.info(f"[SDP] {res.status_code}")
        logger.info(res.text)

        if res.status_code not in [200, 201]:
            return None

        return res.json().get("request", {}).get("id")

    except Exception as e:
        logger.error(f"[SDP ERROR] {e}")
        return None

# ======================
# NOTIFY
# ======================

def notify(username: str, ticket_id: str):
    try:
        requests.post(
            WEBHOOK_URL,
            json={"text": f"@{username}\n\n✅ Ticket Created\n🎫 ID: {ticket_id}"}
        )
    except Exception as e:
        logger.error(f"[WEBHOOK ERROR] {e}")

# ======================
# MAIN
# ======================

def main():

    global last_timestamp, BOT_USER_ID

    BOT_USER_ID = get_my_user_id()

    logger.info("🚀 Bot Started...")

    while True:
        try:

            posts = get_posts(last_timestamp)

            for post in posts:

                message = post.get("message")
                user_id = post.get("user_id")
                created = post.get("create_at")

                if not message or not user_id:
                    continue

                if user_id == BOT_USER_ID:
                    continue

                if created <= last_timestamp:
                    continue

                user = get_user(user_id)

                email = user.get("email")
                username = user.get("username")

                if email == IGNORE_EMAIL:
                    continue

                if "joined the channel" in message.lower():
                    continue
                if "added to the channel" in message.lower():
                    continue

                ticket_id = create_ticket(user, message)

                if ticket_id:
                    notify(username, ticket_id)

                last_timestamp = max(last_timestamp, created)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logger.error(f"[LOOP ERROR] {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
