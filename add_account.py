"""
add_account.py - أضف حساب أو منشور
python3.11 add_account.py
"""

import asyncio
import re
from pathlib import Path
from playwright.async_api import async_playwright
from ig_base import db_insert, SUPABASE_URL, HEADERS
import requests


async def add_account():
    username = input("اسم المستخدم على انستاجرام: ").strip()
    session_file = f"sessions/{username}.json"
    Path("sessions").mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.instagram.com/accounts/login/")
        print(f"🌐 سجّل دخول بحساب @{username} ثم اضغط Enter...")
        input("اضغط Enter بعد تسجيل الدخول: ")
        await context.storage_state(path=session_file)
        await browser.close()

    db_insert("ig_accounts", {
        "username": username,
        "session_file": session_file,
        "status": "active"
    })
    print(f"✅ تم إضافة @{username}")


def add_post():
    url = input("رابط المنشور: ").strip()
    desc = input("وصف (اختياري): ").strip()
    m = re.search(r'/(p|reel|tv)/([^/?]+)', url)
    post_id = m.group(2) if m else None

    db_insert("ig_posts", {
        "post_url": url,
        "post_id": post_id,
        "description": desc,
        "active": True
    })
    print(f"✅ تم إضافة المنشور")


def show_stats():
    from ig_base import db_select
    accounts = db_select("ig_accounts")
    posts = db_select("ig_posts")
    likes = db_select("ig_likes")
    comments = db_select("ig_comments")

    print(f"\n📊 الإحصائيات:")
    print(f"   حسابات: {len(accounts)}")
    print(f"   منشورات: {len(posts)}")
    print(f"   لايكات: {len(likes)}")
    print(f"   كومنتات: {len(comments)}")

    print(f"\n👤 الحسابات:")
    for a in accounts:
        print(f"   @{a['username']} - {a['status']} - فشلات: {a.get('fail_count',0)}")


async def main():
    print("\n=== إدارة النظام ===")
    print("1. أضف حساب انستاجرام")
    print("2. أضف منشور للمراقبة")
    print("3. إحصائيات")
    choice = input("\nاختر: ").strip()

    if choice == "1":
        await add_account()
    elif choice == "2":
        add_post()
    elif choice == "3":
        show_stats()
    else:
        print("خيار غير صحيح")


if __name__ == "__main__":
    asyncio.run(main())
