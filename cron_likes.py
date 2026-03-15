"""
cron_likes.py - كل 5 دقايق
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from ig_base import (
    get_active_account, mark_account_failed, mark_account_success,
    get_active_posts, insert_like
)


async def scrape_likes(page, post, account_id):
    post_url = post['post_url']
    post_db_id = post['id']
    print(f"  📍 {post_url}")

    await page.goto(post_url, wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)

    if "login" in page.url:
        print("  ❌ غير مسجل الدخول")
        mark_account_failed(account_id)
        return 0

    # اضغط زر اللايكات
    clicked = await page.evaluate("""() => {
        var els = document.querySelectorAll('section *');
        var nums = [];
        els.forEach(function(el) {
            var text = (el.innerText || '').trim();
            if (!/^[\\d,\\.]+$/.test(text)) return;
            var num = parseInt(text.replace(/[,\\.]/g, ''));
            if (num < 1 || el.closest('a')) return;
            nums.push({ el: el, num: num });
        });
        nums.sort(function(a, b) { return b.num - a.num; });
        if (nums.length === 0) return false;
        var clickable = nums[0].el.closest('[role="button"]') ||
                        nums[0].el.closest('[tabindex="0"]') ||
                        nums[0].el;
        clickable.click();
        return true;
    }""")

    if not clicked:
        print("  ⚠️  ما قدر يضغط زر اللايكات")
        return 0

    await page.wait_for_timeout(2500)

    dialog = await page.query_selector('[role="dialog"]')
    if not dialog:
        print("  ⚠️  الـ modal ما فتح")
        return 0

    # حقن Observer
    await page.evaluate("""() => {
        window._igLikes = {};
        var d = document.querySelector('[role="dialog"]');
        if (!d) return;
        function col(root) {
            root.querySelectorAll('a[href^="/"]').forEach(function(a) {
                var u = (a.getAttribute('href') || '')
                    .replace(/^\\//, '').replace(/\\/$/, '').replace(/\\?.*/,'');
                if (!u || u.length < 2 || u.includes('/')) return;
                if (/^(explore|reel|p|stories|direct|accounts|tv|reels|audio|liked_by)/.test(u)) return;
                window._igLikes[u] = u;
            });
        }
        col(d);
        window._igObserver = new MutationObserver(function(ms) {
            ms.forEach(function(m) {
                m.addedNodes.forEach(function(n) { if (n.nodeType===1) col(n); });
            });
        });
        window._igObserver.observe(d, { childList: true, subtree: true });
    }""")

    # اسكرول لأقصى تحت أولاً
    await page.evaluate("""() => {
        var d = document.querySelector('[role="dialog"]');
        var el = null, mx = 0;
        d.querySelectorAll('*').forEach(function(e) {
            var df = e.scrollHeight - e.clientHeight;
            if (df > mx) { mx = df; el = e; }
        });
        if (el) el.scrollTop = el.scrollHeight;
    }""")
    await asyncio.sleep(1.5)

    # سكرول لفوق تدريجياً - بدون early stop
    for i in range(200):
        r = await page.evaluate("""() => {
            var d = document.querySelector('[role="dialog"]');
            if (!d) return { total: 0, atTop: true };
            var el = null, mx = 0;
            d.querySelectorAll('*').forEach(function(e) {
                var df = e.scrollHeight - e.clientHeight;
                if (df > mx) { mx = df; el = e; }
            });
            var atTop = false;
            if (el && mx > 5) {
                el.scrollTop -= 350;
                atTop = el.scrollTop <= 0;
            }
            return { total: Object.keys(window._igLikes||{}).length, atTop: atTop };
        }""")

        total = r['total']
        print(f"  scroll {i+1}: {total} لايك   ", end='\r')

        if r['atTop']:
            await asyncio.sleep(1.5)
            # تحقق مرة أخيرة
            final = await page.evaluate("() => Object.keys(window._igLikes||{}).length")
            print(f"\n  وصلنا للأعلى: {final} لايك")
            break

        await asyncio.sleep(0.8)

    likes = await page.evaluate("""() => {
        if (window._igObserver) window._igObserver.disconnect();
        return Object.keys(window._igLikes || {});
    }""")

    await page.keyboard.press("Escape")

    new_count = sum(1 for u in likes if insert_like(post_db_id, u))
    print(f"\n  ✓ {len(likes)} لايك ({new_count} جديد)")
    return new_count


async def main():
    print(f"\n❤️  Cron Likes - {datetime.now().strftime('%H:%M:%S')}")

    account = get_active_account()
    if not account:
        return

    print(f"  حساب: @{account['username']}")
    posts = get_active_posts()
    if not posts:
        print("  ⚠️  ما في منشورات")
        return

    from playwright.async_api import async_playwright
    from ig_base import get_browser_context

    async with async_playwright() as p:
        browser, context = await get_browser_context(p, account)

        page = await context.new_page()
        await page.route("**/*.{png,jpg,jpeg,gif,woff,woff2,ttf}", lambda r: r.abort())

        success = True
        for post in posts:
            try:
                await scrape_likes(page, post, account['id'])
                await asyncio.sleep(2)
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
