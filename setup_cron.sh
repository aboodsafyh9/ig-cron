# إعداد الـ Cron Jobs
# شغّل: bash setup_cron.sh

SCRIPT_DIR=$(pwd)
PYTHON=$(which python3)

echo "إعداد الـ cron jobs..."

# احفظ الـ crontab الحالي
crontab -l > mycron 2>/dev/null

# أضف الـ cron jobs
echo "*/5 * * * * cd $SCRIPT_DIR && $PYTHON cron_likes.py >> logs/likes.log 2>&1" >> mycron
echo "*/15 * * * * cd $SCRIPT_DIR && $PYTHON cron_comments.py >> logs/comments.log 2>&1" >> mycron

# طبّق
crontab mycron
rm mycron

# أنشئ مجلد logs
mkdir -p logs

echo "✅ تم إعداد الـ cron jobs!"
echo ""
echo "Cron 1: كل 5 دقايق  → cron_likes.py"
echo "Cron 2: كل 15 دقيقة → cron_comments.py"
echo ""
echo "عشان تشوف الـ logs:"
echo "  tail -f logs/likes.log"
echo "  tail -f logs/comments.log"
