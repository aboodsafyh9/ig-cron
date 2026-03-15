"""
ig_base.py - الأساس المشترك
"""

import os
import re
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}


def db_select(table, filters=None, order=None, limit=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    if filters:
        for k, v in filters.items():
            url += f"&{k}=eq.{v}"
    if order:
        url += f"&order={order}"
    if limit:
        url += f"&limit={limit}"
    res = requests.get(url, headers=HEADERS)
    return res.json()


def db_insert(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    res = requests.post(url, json=data, headers=HEADERS)
    return res.status_code in [200, 201]


def db_update(table, filters, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?"
    for k, v in filters.items():
        url += f"{k}=eq.{v}&"
    url = url.rstrip("&")
    headers = {**HEADERS, "Prefer": "return=minimal"}
    res = requests.patch(url, json=data, headers=headers)
    return res.status_code in [200, 204]


def get_active_account():
    accounts = db_select("ig_accounts", {"status": "active"}, order="last_used.asc.nullsfirst", limit=1)
    if not accounts:
        print("❌ ما في حسابات شغالة!")
        return None
    return accounts[0]


def mark_account_failed(account_id):
    accounts = db_select("ig_accounts", {"id": account_id})
    if not accounts:
        return
    fail_count = accounts[0].get('fail_count', 0) + 1
    if fail_count >= 3:
        db_update("ig_accounts", {"id": account_id}, {"status": "blocked", "fail_count": fail_count})
        print(f"  ⚠️  الحساب {account_id} انبلك")
    else:
        db_update("ig_accounts", {"id": account_id}, {"fail_count": fail_count})


def mark_account_success(account_id):
    db_update("ig_accounts", {"id": account_id}, {
        "last_used": datetime.now().isoformat(),
        "fail_count": 0
    })


def get_active_posts():
    return db_select("ig_posts", {"active": "true"})


def extract_post_id(url):
    m = re.search(r'/(p|reel|tv)/([^/?]+)', url)
    return m.group(2) if m else None


def insert_like(post_db_id, username):
    """أضف لايك - تجاهل لو موجود"""
    url = f"{SUPABASE_URL}/rest/v1/ig_likes"
    headers = {**HEADERS, "Prefer": "resolution=ignore-duplicates"}
    res = requests.post(url, json={
        "post_id": post_db_id,
        "username": username.lower(),
        "discovered_at": datetime.now().isoformat()
    }, headers=headers)
    return res.status_code in [200, 201]


def insert_comment(post_db_id, username, comment_text, comment_url, timestamp):
    """أضف كومنت - تجاهل لو موجود"""
    url = f"{SUPABASE_URL}/rest/v1/ig_comments"
    headers = {**HEADERS, "Prefer": "resolution=ignore-duplicates"}
    res = requests.post(url, json={
        "post_id": post_db_id,
        "username": username.lower(),
        "comment_text": comment_text,
        "comment_url": comment_url,
        "discovered_at": datetime.now().isoformat(),
        "status": "active"
    }, headers=headers)
    return res.status_code in [200, 201]
