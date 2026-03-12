import os
from datetime import datetime
import requests


def send_to_n8n(payload: dict, webhook_url: str):
    """
    Send JSON payload to an n8n webhook.

    Args:
        payload (dict): JSON payload to send
        webhook_url (str): n8n webhook URL

    Returns:
        dict: response info
    """

    if not isinstance(payload, dict):
        return {
            "status_code": 400,
            "response_text": "Payload must be a dictionary"
        }

    if not webhook_url:
        return {
            "status_code": 400,
            "response_text": "Webhook URL is missing"
        }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        return {
            "status_code": response.status_code,
            "response_text": response.text
        }

    except requests.exceptions.RequestException as e:
        return {
            "status_code": 500,
            "response_text": str(e)
        }


def send_telegram_post(text: str, lang: str,  url: str):
    """
    Prepare Telegram message payload and send it to n8n.

    Args:
        text (str): Telegram message
        lang (str): message language (ar / en)

    Returns:
        tuple: (success: bool, response: dict or str)
    """

    webhook_url = url

    if not webhook_url:
        return False, "Environment variable N8N_WEBHOOK_URL is not set"

    if not text:
        return False, "Telegram message is empty"

    payload = {
        "platform": "telegram",
        "language": lang,
        "message": text,
        "timestamp": datetime.utcnow().isoformat()
    }

    result = send_to_n8n(payload=payload, webhook_url=webhook_url)

    if result["status_code"] in [200, 201]:
        return True, result
    else:
        return False, result