import requests
from typing import Optional
from .logger import logger
from .config import config

class DiscordNotifier:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)

        if self.enabled:
            logger.info("Discord notifications enabled")
        else:
            logger.info("Discord notifications disabled (no webhook configured)")

    def send_arbitrage_opportunity(self, opportunity_text: str) -> bool:
        """Send arbitrage opportunity notification to Discord"""
        if not self.enabled:
            return False

        try:
            # Discord has a 2000 character limit for message content
            if len(opportunity_text) > 1900:
                opportunity_text = opportunity_text[:1900] + "...\n(truncated)"

            # Format as a code block for better readability
            content = f"```\n{opportunity_text}\n```"

            payload = {
                "content": content,
                "username": "Arbitrage Bot"
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 204:
                logger.debug("Discord notification sent successfully")
                return True
            else:
                logger.warning(f"Failed to send Discord notification: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False

    def send_message(self, message: str) -> bool:
        """Send a general message to Discord"""
        if not self.enabled:
            return False

        try:
            payload = {
                "content": message,
                "username": "Arbitrage Bot"
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            return response.status_code == 204

        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            return False

# Initialize global notifier
webhook_url = config.get("notifications", "discord_webhook") if config.config.get("notifications", {}).get("discord_webhook") else None
notifier = DiscordNotifier(webhook_url)
