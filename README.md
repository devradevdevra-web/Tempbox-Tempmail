# Tempbox Mail

A lightweight, robust Python client that interfaces with tempbox.co.uk to programmatically generate temporary mailboxes, fetch messages, and poll inboxes in real time.

Built with `requests` and `BeautifulSoup`, this script handles session initialization, CSRF token extraction, dynamic polling cycles, and automatic token re-negotiation if a session expires.

---

## Features

- **Automated Session & CSRF Handshake:** Scrapes the main page on startup to automatically extract and manage Laravel/site CSRF tokens.
- **Real-Time Polling Loop:** Periodically checks your inbox at a customizable interval (`poll_interval`).
- **Deduplication:** Keeps track of seen messages via a memory set so you only get alerted for fresh emails.
- **Resilient Error Recovery:** Gracefully catches network timeouts and HTTP errors, automatically re-initializing sessions when an expired token (HTTP 401, 403, 419) is detected.
- **Structured Logging:** Clean, time-stamped console output using Python's built-in `logging` module.

---

## Prerequisites

Make sure you have Python 3.10+ installed along with the required third-party libraries:

```bash
pip install requests beautifulsoup4
