"""
cron_runner.py - يشغّل الـ cron jobs تلقائياً
لايكات: كل 5 دقايق
كومنتات: كل 15 دقيقة
"""

import asyncio
import time
from datetime import datetime

import os
import sys
sys.stdout.reconfigure(line_buffering=True)


async def run_likes():
    from cron_likes import main as likes_main
    try:
        await likes_main()
    except Exception as e:
        print(f"❌ خطأ في اللايكات: {e}")

async def run_comments():
    from cron_comments import main as comments_main
    try:
        await comments_main()
    except Exception as e:
        print(f"❌ خطأ في الكومنتات: {e}")

async def main():
    print("🚀 Cron Runner شغال...", flush=True)
    print(f"SUPABASE: {os.getenv('SUPABASE_URL', 'NOT SET')}", flush=True)

    likes_counter = 0
    comments_counter = 0

    while True:
        now = datetime.now().strftime('%H:%M:%S')

        # لايكات كل 5 دقايق (300 ثانية)
        if likes_counter <= 0:
            print(f"\n⏰ {now} - تشغيل اللايكات...")
            await run_likes()
            likes_counter = 300

        # كومنتات كل 15 دقيقة (900 ثانية)
        if comments_counter <= 0:
            print(f"\n⏰ {now} - تشغيل الكومنتات...")
            await run_comments()
            comments_counter = 900

        await asyncio.sleep(30)
        likes_counter -= 30
        comments_counter -= 30

if __name__ == "__main__":
    asyncio.run(main())
