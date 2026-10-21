import logging
import time
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname).1s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Tempbox")

class TempboxClient:
    def __init__(self, base_url="https://tempbox.co.uk", poll_interval=10):
        self.base_url = base_url
        self.poll_interval = poll_interval
        self.timeout = (5, 30)
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        })
        
        self.csrf_token = None
        self.mailbox = None

    def initialize_session(self):
        logger.info("Initializing connection to Tempbox...")
        
        response = self.session.get(self.base_url, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        token_tag = soup.select_one('meta[name="csrf-token"]')

        if not token_tag or not token_tag.get("content"):
            raise RuntimeError("CSRF token could not be found. The site layout may have changed.")

        self.csrf_token = token_tag.get("content")
        logger.info("Session established successfully.")

    def fetch_inbox(self):
        response = self.session.post(
            f"{self.base_url}/get_messages",
            data={
                "_token": self.csrf_token,
                "captcha": "",
            },
            headers={"Referer": f"{self.base_url}/"},
            timeout=self.timeout,
        )

        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and isinstance(data.get("data"), dict):
            data = data["data"]

        if not isinstance(data, dict):
            logger.warning(f"Received unexpected payload structure: {repr(data)[:150]}")
            return None, []

        self.mailbox = data.get("mailbox", self.mailbox)
        messages = data.get("messages", [])
        
        return self.mailbox, messages if isinstance(messages, list) else []

    def start_polling(self):
        if not self.csrf_token:
            self.initialize_session()

        seen_messages = set()
        mailbox_announced = False

        logger.info(f"Polling inbox every {self.poll_interval} seconds. Press Ctrl+C to exit.")

        while True:
            try:
                mailbox, messages = self.fetch_inbox()

                if mailbox and not mailbox_announced:
                    logger.info(f"Active Mailbox Address: {mailbox}")
                    mailbox_announced = True

                if not messages:
                    logger.debug("Inbox checked — no messages found yet.")

                for message in messages:
                    if not isinstance(message, dict):
                        continue

                    msg_id = str(
                        message.get("id")
                        or message.get("message_id")
                        or repr(message)
                    )

                    if msg_id in seen_messages:
                        continue

                    seen_messages.add(msg_id)
                    self._display_message(message)

            except requests.exceptions.Timeout:
                logger.warning("Connection timed out waiting for server response. Retrying next cycle...")

            except requests.exceptions.HTTPError as err:
                status = err.response.status_code if err.response else "unknown"
                logger.error(f"HTTP error encountered ({status}): {err}")
                
                if status in (401, 403, 419):
                    logger.warning("Session or token likely expired. Attempting to re-initialize...")
                    try:
                        self.initialize_session()
                    except Exception as ex:
                        logger.error(f"Re-initialization failed: {ex}")

            except requests.exceptions.RequestException as err:
                logger.error(f"Network error: {err}")

            except ValueError:
                logger.error("Server returned a response that isn't valid JSON.")

            time.sleep(self.poll_interval)

    @staticmethod
    def _display_message(message):
        sender = message.get("from", "Unknown Sender")
        subject = message.get("subject", "(No Subject)")
        body = (
            message.get("text")
            or message.get("body")
            or message.get("html")
            or "(No body content available)"
        )

        logger.info("New message received")
        logger.info(f"From: {sender}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {body.strip()}")


if __name__ == "__main__":
    client = TempboxClient(poll_interval=10)
    try:
        client.start_polling()
    except KeyboardInterrupt:
        logger.info("Polling stopped by user. Goodbye.")
    except Exception as err:
        logger.critical(f"Fatal error during execution: {err}")
