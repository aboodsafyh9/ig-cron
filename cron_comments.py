"""
cron_comments.py - كل 15 دقيقة
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from ig_base import (
    get_active_account, mark_account_failed, mark_account_success,
    get_active_posts, insert_comment, get_browser_context
)


async def scrape_comments(page, post, account_id):
    post_url = post['post_url']
    post_db_id = post['id']
    print(f"  📍 {post_url}")

    await page.goto(post_url, wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)

    if "login" in page.url:
        print("  ❌ غير مسجل الدخول")
        mark_account_failed(account_id)
        return 0

    # اضغط زر Comment
    try:
        for el in await page.query_selector_all('[aria-label]'):
            label = (await el.get_attribute('aria-label') or '').lower()
            if 'comment' in label:
                await el.click()
                await page.wait_for_timeout(1500)
                break
    except:
        pass

    # سكرول
    for _ in range(20):
        await page.evaluate("() => window.scrollBy(0, 600)")
        await asyncio.sleep(0.5)
    await asyncio.sleep(2)

    # استخرج الكومنتات
    comments = await page.evaluate("""() => {
        var out = [];
        var all = Array.prototype.slice.call(document.querySelectorAll('span'));
        all.forEach(function(s, i) {
            if (!s.classList.contains('_ap3a')) return;
            var u = (s.innerText || '').trim();
            if (!u) return;
            var nextSpan = all[i + 2];
            var txt = (nextSpan && nextSpan.innerText) ? nextSpan.innerText.trim() : '';
            var container = s.closest('li') || s.closest('div');
            var timeEl = container ? container.querySelector('time') : null;
            var t = timeEl ? (timeEl.getAttribute('datetime') || '') : '';
            var linkEl = container ? container.querySelector('a[href*="/c/"]') : null;
            var commentUrl = linkEl ? linkEl.href : '';
            out.push({ username: u, comment: txt, timestamp: t, comment_url: commentUrl });
        });
        return out;
    }""")

    new_count = 0
    for c in comments:
        if not c['username']:
            continue
        if insert_comment(post_db_id, c['username'], c['comment'], c['comment_url'], c['timestamp']):
            new_count += 1

    print(f"  ✓ {len(comments)} كومنت ({new_count} جديد)")
    return new_count


async def main():
    print(f"\n💬 Cron Comments - {datetime.now().strftime('%H:%M:%S')}")

    account = get_active_account()
    if not account:
        return

    print(f"  حساب: @{account['username']}")
    posts = get_active_posts()
    if not posts:
        print("  ⚠️  ما في منشورات")
        return

    async with async_playwright() as p:
        browser, context = await get_browser_context(p, account)

        page = await context.new_page()
        await page.route("**/*.{png,jpg,jpeg,gif,woff,woff2,ttf}", lambda r: r.abort())

        success = True
        for post in posts:
            try:
                await scrape_comments(page, post, account['id'])
                await asyncio.sleep(3)
            except Exception as e:
                print(f"  ❌ {e}")
                success = False

        await browser.close()

    if success:
        mark_account_success(account['id'])
    else:
        mark_account_failed(account['id'])

    print("  ✅ انتهى\n")


if __name__ == "__main__":
    asyncio.run(main())
