import os
import zipfile
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler

IST = timezone(timedelta(hours=5, minutes=30))

def backup_storage():
    if not os.path.exists('storage'):
        return

    os.makedirs('backups', exist_ok=True)
    timestamp = datetime.now(IST).strftime('%Y%m%d_%H%M%S')
    backup_path = f"backups/backup_{timestamp}.zip"

    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk('storage'):
            for file in files:
                file_path = os.path.join(root, file)
                zf.write(file_path)

    print(f"Backup created: {backup_path}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(backup_storage, 'interval', hours=6)
    scheduler.start()