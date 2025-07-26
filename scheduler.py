from apscheduler.schedulers.background import BackgroundScheduler
from main import main
import time

# Run once immediately
main()

# Start the recurring schedule
scheduler = BackgroundScheduler(timezone='Asia/Ho_Chi_Minh')  # Use your local timezone
scheduler.add_job(main, 'interval', minutes=30)
scheduler.start()

try:
    while True:
        time.sleep(60)  # Keep the script running
except KeyboardInterrupt:
    scheduler.shutdown()
