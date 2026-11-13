"""Persistence and notification boundary for future booking integrations."""
import json
import logging
import sqlite3
import urllib.request
from datetime import datetime, timezone


def initialise_database(path):
    with sqlite3.connect(path) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT,
            class_type TEXT NOT NULL, preferred_date TEXT, preferred_time TEXT,
            experience TEXT NOT NULL, message TEXT, consent INTEGER NOT NULL,
            request_token TEXT UNIQUE NOT NULL)''')


def save_enquiry(path, data, token):
    with sqlite3.connect(path) as db:
        cursor = db.execute('''INSERT OR IGNORE INTO enquiries
            (created_at, name, email, phone, class_type, preferred_date,
             preferred_time, experience, message, consent, request_token)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (datetime.now(timezone.utc).isoformat(), data['name'], data['email'],
             data['phone'], data['class_type'], data['preferred_date'],
             data['preferred_time'], data['experience'], data['message'], 1, token))
        return cursor.lastrowid if cursor.rowcount else None


def notify_enquiry(reference, data, url='', token=''):
    """Optional webhook; persistence succeeds even if email delivery is unavailable."""
    if not url:
        return
    if not url.startswith('https://'):
        logging.warning('Enquiry webhook requires HTTPS')
        return
    request = urllib.request.Request(url,
        data=json.dumps({'reference': reference, 'enquiry': data}).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            response.read(1024)
    except Exception:
        logging.warning('Enquiry %s saved; notification delivery failed', reference)
